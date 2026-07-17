import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import torch


def build_dynamic_evaluation_lists(images_dir, masks_dir, clean_threshold=0.001):
    """
    Dynamically categorizes tiles based on ground-truth mask content.
    clean_threshold: Max allowed defect pixel ratio to be considered "clean background".
                     0.001 means 0.1% of the tile can be defect (accounts for minor mask bleed).
    """
    images_path = Path(images_dir)
    masks_path = Path(masks_dir)

    clean_tiles = []
    defect_tiles = []

    for img_path in images_path.glob("*.png"):
        mask_path_png = masks_path / (img_path.stem + ".png")
        mask_path_jpg = masks_path / (img_path.stem + ".jpg")

        if mask_path_png.exists():
            mask_path = mask_path_png
        elif mask_path_jpg.exists():
            mask_path = mask_path_jpg
        else:
            continue

        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue

        defect_pixels = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        defect_ratio = defect_pixels / total_pixels

        if defect_ratio == 0:
            clean_tiles.append(str(img_path))
        else:
            defect_tiles.append(str(img_path))

    print(
        f"[+] Dynamically categorized: {len(clean_tiles)} Clean Background Tiles, {len(defect_tiles)} Defect Tiles."
    )
    return clean_tiles, defect_tiles


def run_softmax_profiling(
    model_path, images_dir, masks_dir, clean_threshold=0.001, limit=10, device=None
):
    print("[+] Loading retrained Stage 1 Model...")
    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    if device is not None:
        net.to(device)
    device = next(net.parameters()).device

    clean_tiles, defect_tiles = build_dynamic_evaluation_lists(
        images_dir=images_dir,
        masks_dir=masks_dir,
        clean_threshold=clean_threshold,
    )

    clean_tiles = clean_tiles[:limit]
    defect_tiles = defect_tiles[:limit]

    print("\n" + "=" * 80)
    print(" 📊 PROFILING CLEAN BACKGROUND TILES (ESTABLISHING THE NOISE FLOOR)")
    print("=" * 80)
    clean_maxes = []
    for f in clean_tiles:
        path = Path(f)
        if not path.exists():
            print(f" [!] Missing: {f}")
            continue
        img = cv2.imread(str(path))
        h_orig, w_orig = img.shape[:2]
        img_resized = cv2.resize(img, (640, 640))
        img_tensor = (
            (
                torch.from_numpy(img_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            .unsqueeze(0)
            .to(device)
        )
        with torch.no_grad():
            raw_out = net(img_tensor)
        logits = raw_out[0] if isinstance(raw_out, tuple) else raw_out
        probs = torch.softmax(logits, dim=1)[0, 1, :, :].cpu().numpy()
        probs = cv2.resize(probs, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)

        tile_max = float(np.max(probs))
        tile_perc = float(np.percentile(probs, 99.9))
        clean_maxes.append(tile_perc)
        print(
            f" 🟢 {path.name:<15} | Peak Softmax: {tile_max:.5f} | 99.9th Percentile: {tile_perc:.5f}"
        )

    print("\n" + "=" * 80)
    print(" 🔥 PROFILING CONFIRMED DEFECT TILES (ESTABLISHING THE SIGNAL PEAKS)")
    print("=" * 80)
    defect_peaks = []
    for f in defect_tiles:
        path = Path(f)
        if not path.exists():
            print(f" [!] Missing: {f}")
            continue
        img = cv2.imread(str(path))
        h_orig, w_orig = img.shape[:2]
        img_resized = cv2.resize(img, (640, 640))
        img_tensor = (
            (
                torch.from_numpy(img_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            .unsqueeze(0)
            .to(device)
        )
        with torch.no_grad():
            raw_out = net(img_tensor)
        logits = raw_out[0] if isinstance(raw_out, tuple) else raw_out
        probs = torch.softmax(logits, dim=1)[0, 1, :, :].cpu().numpy()
        probs = cv2.resize(probs, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR)

        tile_max = float(np.max(probs))
        tile_90th = float(np.percentile(probs, 99.9))
        defect_peaks.append(tile_max)
        print(
            f" 🔴 {path.name:<15} | Peak Softmax: {tile_max:.5f} | 99.9th Percentile: {tile_90th:.5f}"
        )

    print("\n" + "=" * 80)
    print(" 📈 HYSTERESIS CALIBRATION SUMMARY")
    print("=" * 80)
    if clean_maxes and defect_peaks:
        max_clean_noise = max(clean_maxes)
        min_defect_signal = min(defect_peaks)
        print(f"  Maximum 99.9th Percentile Background Noise: {max_clean_noise:.5f}")
        print(f"  Lowest Peak Defect Signal:              {min_defect_signal:.5f}")
        print("-" * 80)
        print("  Suggested Calibration Range:")
        print(
            f"    - Seed Anchor (tau_high):   Must be > {max_clean_noise:.5f} but < {min_defect_signal:.5f}"
        )
        print(
            "    - Pathway (tau_low):        Tuned lower to recover tails, but above mean noise."
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Softmax Profile Calibration Diagnostic"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to YOLO semantic weights"
    )
    parser.add_argument(
        "--images_dir",
        type=str,
        default="data/processed/sod_tiled/images/val",
        help="Tiled images dir",
    )
    parser.add_argument(
        "--masks_dir",
        type=str,
        default="data/processed/sod_tiled/masks/val",
        help="Tiled masks/labels dir",
    )
    parser.add_argument(
        "--clean_threshold",
        type=float,
        default=0.001,
        help="Max defect ratio to consider background clean",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Cap evaluation runs limit to speed up processing",
    )
    parser.add_argument(
        "--device", type=str, default=None, help="Hardware target (e.g., cuda:0)"
    )
    args = parser.parse_args()

    run_softmax_profiling(
        model_path=args.model,
        images_dir=args.images_dir,
        masks_dir=args.masks_dir,
        clean_threshold=args.clean_threshold,
        limit=args.limit,
        device=args.device,
    )
