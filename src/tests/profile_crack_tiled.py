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
    model_path, img_path, mask_path, imgsz=512, overlap_frac=0.15
):
    print("[+] Loading model and initializing raw-logits bypass...")
    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # 1. Load Ground Truth Mask to locate the crack coordinates
    gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if gt_mask is None:
        raise FileNotFoundError(f"Could not load mask at {mask_path}")

    y_coords, x_coords = np.where(gt_mask > 0)
    if len(y_coords) == 0:
        raise ValueError("No defect pixels found in the ground truth mask.")

    # Sort coordinates from top to bottom (by Y-coordinate)
    sorted_indices = np.argsort(y_coords)
    y_sorted = y_coords[sorted_indices]
    x_sorted = x_coords[sorted_indices]

    # 2. Load the original full-resolution image
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(f"Could not load image at {img_path}")
    h_orig, w_orig = img.shape[:2]

    # Initialize our global canvas for stitched probabilities
    global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)

    # 3. Slice, Infer on Tiles, and Stitch
    tile_bounds = get_tile_coords(h_orig, w_orig, overlap_frac)
    print(f"[+] Slicing image into 4 quadrants with {overlap_frac*100:.1f}% overlap...")

    for idx, ((y0, y1), (x0, x1)) in enumerate(tile_bounds):
        # Extract the overlapping quadrant crop
        tile_crop = img[y0:y1, x0:x1]
        t_h, t_w = tile_crop.shape[:2]

        # Preprocess tile to the model's training size (512x512)
        tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
        img_tensor = (
            torch.from_numpy(tile_resized[:, :, ::-1].copy()).permute(2, 0, 1).float()
            / 255.0
        )
        img_tensor = img_tensor.unsqueeze(0).to(device)

        # Raw forward pass
        with torch.no_grad():
            raw_output = net(img_tensor)

        logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
        probs = torch.sigmoid(logits)

        # Extract defect channel probability map
        target_channel = 1 if logits.shape[1] > 1 else 0
        raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

        # Scale the tile's probability map back to its unresized cropped tile shape
        tile_probs_resized = cv2.resize(
            raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
        )

        # Stitch back into global canvas resolving overlaps with maximum pooling
        global_probs[y0:y1, x0:x1] = np.maximum(
            global_probs[y0:y1, x0:x1], tile_probs_resized
        )
        print(
            f"    [✓] Processed Tile {idx} (Shape: {t_w}x{t_h}) -> "
            f"Logit range: {tile_probs_resized.min():.4f} to "
            f"{tile_probs_resized.max():.4f}"
        )

    # 4. Extract confidence values along the sorted crack path from stitched canvas
    unique_ys = np.unique(y_sorted)
    profile_data = []

    for y in unique_ys:
        xs_at_y = x_sorted[y_sorted == y]
        max_prob = np.max([global_probs[y, x] for x in xs_at_y])
        profile_data.append((y, max_prob))

    # 5. Output Results & Print ASCII Plot
    print("\n" + "=" * 60)
    print(" 📈 TILED-CORRECT 1D CRACK CONFIDENCE PROFILE")
    print("=" * 60)
    print(f"Crack Span: Y={unique_ys.min()} (Top) to Y={unique_ys.max()} (Bottom)")
    print("=" * 60)

    # Downsample profile to ~30 rows for terminal scannability
    step_size = max(1, len(profile_data) // 30)
    downsampled_profile = profile_data[::step_size]

    for y, prob in downsampled_profile:
        bar_length = int(prob * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"Y={y:03d} | [{bar}] {prob:.3f}")

    print("=" * 60)

    avg_conf = np.mean([p[1] for p in profile_data])
    top_third_conf = np.mean([p[1] for p in profile_data[: len(profile_data) // 3]])
    bottom_third_conf = np.mean([p[1] for p in profile_data[-len(profile_data) // 3 :]])

    print(f"Stitched Average Confidence: {avg_conf:.3f}")
    print(f"Stitched Top-Third (Tip) Average: {top_third_conf:.3f}")
    print(f"Stitched Bottom-Third (Base) Average: {bottom_third_conf:.3f}")
    print("=" * 60 + "\n")

    # Save a visual tiled heatmap output for validation
    heatmap_pixels = (global_probs * 255).astype(np.uint8)
    heatmap_colored = cv2.applyColorMap(heatmap_pixels, cv2.COLORMAP_JET)
    cv2.imwrite("tiled_stitched_xray_000552.jpg", heatmap_colored)
    print("[✓] Stitched visual heatmap saved to tiled_stitched_xray_000552.jpg")


if __name__ == "__main__":
    model_weight = "mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt"
    img_file = "data/processed/sod/val/images/000552.jpg"
    mask_file = "data/processed/sod/val/masks/000552.png"

    extract_tiled_confidence_profile(model_weight, img_file, mask_file)
