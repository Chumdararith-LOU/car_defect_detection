import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from src.inference.router import get_stitched_probability_map


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

    # Assuming your tiled images are .png or .jpg. Adjust glob if needed.
    for img_path in images_path.glob("*.png"):
        # Handle both .png and .jpg mask naming conventions
        mask_path_png = masks_path / (img_path.stem + ".png")
        mask_path_jpg = masks_path / (img_path.stem + ".jpg")

        if mask_path_png.exists():
            mask_path = mask_path_png
        elif mask_path_jpg.exists():
            mask_path = mask_path_jpg
        else:
            continue  # Skip if no mask exists

        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue

        # Count actual defect pixels
        defect_pixels = np.sum(mask > 0)
        total_pixels = mask.shape[0] * mask.shape[1]
        defect_ratio = defect_pixels / total_pixels

        # Categorize based on mask, NOT filename
        if defect_ratio <= clean_threshold:
            clean_tiles.append(str(img_path))
        else:
            defect_tiles.append(str(img_path))

    print(
        f"[+] Dynamically categorized: {len(clean_tiles)} Clean Background Tiles, {len(defect_tiles)} Defect Tiles."
    )
    return clean_tiles, defect_tiles


def run_softmax_profiling():
    model_weight = "runs/semantic/runs/semantic/Automated_Car_Defect_Stage1_SOD/Stage1_SOD_FocalLoss_Full/weights/best.pt"

    print("[+] Loading retrained Stage 1 Model...")
    model = YOLO(model_weight, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # DYNAMICALLY BUILD LISTS
    clean_tiles, defect_tiles = build_dynamic_evaluation_lists(
        images_dir="data/processed/sod_tiled/images/val",
        masks_dir="data/processed/sod_tiled/masks/val",
        clean_threshold=0.001,  # 0.1% tolerance
    )

    # Optional: Cap the lists to a manageable number for quick profiling
    clean_tiles = clean_tiles[:10]
    defect_tiles = defect_tiles[:10]

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
        probs = get_stitched_probability_map(
            img, net, device, overlap_frac=0.15, imgsz=640
        )

        tile_max = float(np.max(probs))
        tile_mean = float(np.mean(probs))
        clean_maxes.append(tile_max)
        print(
            f" 🟢 {path.name:<15} | Peak Softmax: {tile_max:.5f} | Mean Noise: {tile_mean:.5f}"
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
        probs = get_stitched_probability_map(
            img, net, device, overlap_frac=0.15, imgsz=640
        )

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
        print(f"  Absolute Maximum Background Noise:      {max_clean_noise:.5f}")
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
    run_softmax_profiling()
