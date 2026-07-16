import cv2
import numpy as np
import torch
from ultralytics import YOLO


def get_tile_2_coords(h, w, overlap_frac=0.15):
    """Returns the exact crop coordinate boundaries for Tile 2 (Bottom-Left)."""
    h_mid, w_mid = h // 2, w // 2
    oh, ow = int(h * overlap_frac), int(w * overlap_frac)
    return (max(0, h_mid - oh), h), (0, min(w, w_mid + ow))


def run_diagnostic_audit(model_path, img_path, mask_path, imgsz=640, overlap_frac=0.15):
    print("=" * 80)
    print(" 🛠️  PHASE 3 PRE-DEPLOYMENT SAFETY & CALIBRATION AUDIT")
    print("=" * 80)

    # 1. Load Model and Raw Logits Network
    print("[+] Loading best model weights...")
    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # 2. Load Original Image & Ground Truth Mask
    img = cv2.imread(str(img_path))
    gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if img is None or gt_mask is None:
        raise FileNotFoundError("Could not find source image or mask.")

    h_orig, w_orig = img.shape[:2]

    # Locate crack coordinates in the thinnest tail region (Y=365 to Y=379)
    y_coords, x_coords = np.where(gt_mask > 0)
    tail_indices = np.where((y_coords >= 365) & (y_coords <= 379))[0]
    tail_y = y_coords[tail_indices]
    tail_x = x_coords[tail_indices]

    # 3. Process Tile 2 (Bottom-Left)
    (y0, y1), (x0, x1) = get_tile_2_coords(h_orig, w_orig, overlap_frac)
    tile_crop = img[y0:y1, x0:x1]
    t_h, t_w = tile_crop.shape[:2]

    # Run Raw forward pass at production 640x640 resolution
    tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
    img_tensor = (
        torch.from_numpy(tile_resized[:, :, ::-1].copy()).permute(2, 0, 1).float()
        / 255.0
    )
    img_tensor = img_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        raw_output = net(img_tensor)

    logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
    probs = torch.sigmoid(logits)
    target_channel = 1 if logits.shape[1] > 1 else 0
    raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

    # Scale probabilities back to unresized crop coordinates
    tile_probs = cv2.resize(raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR)

    print("\nExecuting Step 1: Isolated Erosion Failure Test...")

    # Generate low-threshold binary mask
    pixel_thresh_low = 0.18
    mask_low = (tile_probs >= pixel_thresh_low).astype(np.uint8)

    # Apply standard 2x2 erosion (The supervisor's critical warning)
    kernel_2x2 = np.ones((2, 2), np.uint8)
    mask_eroded = cv2.erode(mask_low, kernel_2x2, iterations=1)

    # Track the tail pixel survival
    pre_erosion_pixels = 0
    post_erosion_pixels = 0

    for ty, tx in zip(tail_y, tail_x):
        # Convert global coordinates to Tile 2 local coordinates
        local_y, local_x = ty - y0, tx - x0

        if mask_low[local_y, local_x] > 0:
            pre_erosion_pixels += 1
        if mask_eroded[local_y, local_x] > 0:
            post_erosion_pixels += 1

    survival_pct = (
        (post_erosion_pixels / pre_erosion_pixels * 100)
        if pre_erosion_pixels > 0
        else 0.0
    )

    print("-" * 80)
    print(f"  Thinnest Tail Coordinates Checked (Y=365 to Y=379): {len(tail_y)} pixels")
    print(f"  Active Pixels BEFORE 2x2 Erosion:                  {pre_erosion_pixels}")
    print(f"  Active Pixels AFTER 2x2 Erosion:                   {post_erosion_pixels}")
    print(f"  Thinnest Tail Survival Rate:                      {survival_pct:.2f}%")
    print("-" * 80)

    if post_erosion_pixels == 0:
        print(
            "[!] FAILURE CONFIRMED: A 2x2 erosion completely erases the thin tail of the crack!"
        )
        print("    We must drop the erosion operator to protect thin-defect integrity.")
    else:
        print(
            "[✓] SURVIVED: The thin tail has enough local density to withstand a 2x2 erosion."
        )

    print("\nExecuting Step 2: In-Distribution Noise Floor Check...")

    # Get the ground truth mask for Tile 2 to locate pure background regions (where GT == 0)
    tile_gt_mask = gt_mask[y0:y1, x0:x1]
    background_pixels = tile_probs[tile_gt_mask == 0]

    # Isolate pavement/shadow area specifically (lower half of Tile 2)
    pavement_start_y = int(t_h * 0.6)  # Focus on bottom 40% of the tile
    pavement_gt_mask = tile_gt_mask[pavement_start_y:, :]
    pavement_probs = tile_probs[pavement_start_y:, :]
    pavement_noise_pixels = pavement_probs[pavement_gt_mask == 0]

    print("-" * 80)
    print(
        f"  Global Background Prob Range: {background_pixels.min():.4f} to {background_pixels.max():.4f}"
    )
    print("  Pavement/Shadow Zone Noise Floor Statistics:")
    print(f"    - Maximum Peak Noise (Ceiling):  {pavement_noise_pixels.max():.4f}")
    print(f"    - Mean Background Noise:         {pavement_noise_pixels.mean():.4f}")
    print(
        f"    - 95th Percentile Noise Level:   {np.percentile(pavement_noise_pixels, 95):.4f}"
    )
    print(
        f"    - 99th Percentile Noise Level:   {np.percentile(pavement_noise_pixels, 99):.4f}"
    )
    print("-" * 80)

    max_noise = pavement_noise_pixels.max()
    print("[ℹ] Calibration Recommendation:")
    if max_noise >= pixel_thresh_low:
        print(
            f"    Warning: Your lower threshold ({pixel_thresh_low}) sits BELOW "
            f"the maximum noise ceiling ({max_noise:.4f})!"
        )
        print(
            f"    To prevent shadow leaks, you must raise pixel_thresh_low to at "
            f"least {max_noise + 0.01:.3f}."
        )
    else:
        print(
            f"    Success: Your lower threshold ({pixel_thresh_low}) safely clears "
            f"the noise ceiling ({max_noise:.4f})."
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Point directly to your best tiled-trained model weights
    model_weight = "mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt"
    img_file = "data/processed/sod/val/images/000552.jpg"
    mask_file = "data/processed/sod/val/masks/000552.png"

    run_diagnostic_audit(model_weight, img_file, mask_file)
