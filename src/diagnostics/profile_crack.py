import cv2
import numpy as np
import torch
from ultralytics import YOLO


def get_tile_coords(h, w, overlap_frac=0.15):
    """
    Returns the exact pixel slice coordinate bounds (y_range, x_range)
    for the 4 overlapping quadrants, matching create_tiles.py perfectly.
    """
    h_mid, w_mid = h // 2, w // 2
    oh, ow = int(h * overlap_frac), int(w * overlap_frac)

    return [
        ((0, min(h, h_mid + oh)), (0, min(w, w_mid + ow))),  # Top-Left
        ((0, min(h, h_mid + oh)), (max(0, w_mid - ow), w)),  # Top-Right
        ((max(0, h_mid - oh), h), (0, min(w, w_mid + ow))),  # Bottom-Left
        ((max(0, h_mid - oh), h), (max(0, w_mid - ow), w)),  # Bottom-Right
    ]


def extract_tiled_confidence_profile(
    model_path, img_path, mask_path, imgsz=640, overlap_frac=0.15, tiled=True
):
    print(f"[+] Loading model and initializing raw-logits bypass at {imgsz}x{imgsz}...")
    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # 1. Load Ground Truth Mask
    gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if gt_mask is None:
        raise FileNotFoundError(f"Could not load mask at {mask_path}")

    y_coords, x_coords = np.where(gt_mask > 0)
    if len(y_coords) == 0:
        raise ValueError("No defect pixels found in the ground truth mask.")

    sorted_indices = np.argsort(y_coords)
    y_sorted = y_coords[sorted_indices]
    x_sorted = x_coords[sorted_indices]

    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Could not load image at {img_path}")
    h_orig, w_orig = img.shape[:2]

    global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)
    tile_canvases = [
        np.full((h_orig, w_orig), -1.0, dtype=np.float32) for _ in range(4)
    ]

    if tiled:
        tile_bounds = get_tile_coords(h_orig, w_orig, overlap_frac)
        print(f"[+] Slicing image with {overlap_frac*100:.1f}% overlap...")

        for idx, ((y0, y1), (x0, x1)) in enumerate(tile_bounds):
            tile_crop = img[y0:y1, x0:x1]
            t_h, t_w = tile_crop.shape[:2]

            tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
            img_tensor = (
                torch.from_numpy(tile_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            img_tensor = img_tensor.unsqueeze(0).to(device)

            with torch.no_grad():
                raw_output = net(img_tensor)

            logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
            probs = torch.sigmoid(logits)

            target_channel = 1 if logits.shape[1] > 1 else 0
            raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

            tile_probs_resized = cv2.resize(
                raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
            )

            tile_canvases[idx][y0:y1, x0:x1] = tile_probs_resized
            global_probs[y0:y1, x0:x1] = np.maximum(
                global_probs[y0:y1, x0:x1], tile_probs_resized
            )
    else:
        print(f"[+] Running untiled standard inference at {imgsz}x{imgsz}...")
        img_resized = cv2.resize(img, (imgsz, imgsz))
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
            raw_output = net(img_tensor)

        logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
        probs = torch.sigmoid(logits)

        target_channel = 1 if logits.shape[1] > 1 else 0
        raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

        global_probs = cv2.resize(
            raw_probs_map, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR
        )

    unique_ys = np.unique(y_sorted)
    profile_data = []

    for y in unique_ys:
        xs_at_y = x_sorted[y_sorted == y]
        max_idx = np.argmax([global_probs[y, x] for x in xs_at_y])
        target_x = xs_at_y[max_idx]

        # Grab stitched and individual tile values for this pixel
        stitched_val = global_probs[y, target_x]
        t0_val = tile_canvases[0][y, target_x]
        t2_val = tile_canvases[2][y, target_x]

        profile_data.append(
            {"y": y, "stitched": stitched_val, "t0": t0_val, "t2": t2_val}
        )

    # 5. Output Results & Print ASCII Plot with Side-by-Side Tile Isolation
    print("\n" + "=" * 85)
    print(" 📈 TILED-CORRECT 1D CONFIDENCE PROFILE (PRODUCTION RESOLUTION: 640x640)")
    print("=" * 85)
    print(f"Crack Span: Y={unique_ys.min()} (Top) to Y={unique_ys.max()} (Bottom)")
    print("=" * 85)

    # Downsample profile to ~30 rows for terminal scannability
    step_size = max(1, len(profile_data) // 30)
    downsampled_profile = profile_data[::step_size]

    for row in downsampled_profile:
        y, prob = row["y"], row["stitched"]
        bar_length = int(prob * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)

        # Format unstitched tiles for comparison
        t0_str = f"{row['t0']:.3f}" if row["t0"] >= 0 else "  -  "
        t2_str = f"{row['t2']:.3f}" if row["t2"] >= 0 else "  -  "

        print(
            f"Y={y:03d} | [{bar}] Stitched: {prob:.3f} | Tile 0 (TL): {t0_str} | Tile 2 (BL): {t2_str}"
        )

    print("=" * 85)

    # Bottom-third isolation check (Y=309 to Y=379)
    bottom_third_rows = [r for r in profile_data if 309 <= r["y"] <= 379]
    avg_stitched = np.mean([r["stitched"] for r in bottom_third_rows])

    # Filter out out-of-bounds tiles (-1.0 values) for averages
    t0_vals = [r["t0"] for r in bottom_third_rows if r["t0"] >= 0]
    t2_vals = [r["t2"] for r in bottom_third_rows if r["t2"] >= 0]

    avg_t0 = np.mean(t0_vals) if t0_vals else 0.0
    avg_t2 = np.mean(t2_vals) if t2_vals else 0.0

    print(" 🔍 BOTTOM-THIRD ISOLATION METRICS (Y=309 to Y=379):")
    print("-" * 85)
    print(f"  Stitched Region Average:          {avg_stitched:.3f}")
    print(f"  Tile 0 (Top-Left) Raw Average:    {avg_t0:.3f}")
    print(f"  Tile 2 (Bottom-Left) Raw Average: {avg_t2:.3f}")
    print("-" * 85)

    if avg_t2 > 0.15 and abs(avg_t2 - avg_stitched) < 0.03:
        print(
            "[✓] VERDICT: Hypothesis C confirmed! "
            "Tile 2 holds a genuine, healthy unstitched signal."
        )
    elif avg_t0 > avg_t2 + 0.10:
        print(
            "[!] VERDICT: Stitching artifact detected! "
            "Tile 0 border effects are artificially inflating the stitched signal."
        )
    else:
        print(
            "[ℹ] VERDICT: Mixed signals. "
            "Analyze individual tile averages to evaluate localized loss."
        )
    print("=" * 85 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract 1D continuous confidence profile along defect coordinates"
    )
    parser.add_argument("--model", type=str, required=True, help="Path to YOLO weights")
    parser.add_argument(
        "--image", type=str, required=True, help="Path to evaluation image"
    )
    parser.add_argument(
        "--mask", type=str, required=True, help="Path to ground-truth mask"
    )
    parser.add_argument(
        "--imgsz", type=int, default=640, help="Inference resolution size"
    )
    parser.add_argument(
        "--overlap", type=float, default=0.15, help="Tile overlap fraction (0.15 = 15%)"
    )
    parser.add_argument(
        "--no-tiling",
        action="store_true",
        help="Bypass overlapping tiling (run untiled)",
    )
    args = parser.parse_args()

    extract_tiled_confidence_profile(
        model_path=args.model,
        img_path=args.image,
        mask_path=args.mask,
        imgsz=args.imgsz,
        overlap_frac=args.overlap,
        tiled=not args.no_tiling,
    )
