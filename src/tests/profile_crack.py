import cv2
import numpy as np
import torch
from ultralytics import YOLO


def extract_1d_confidence_profile(model_path, img_path, mask_path, imgsz=512):
    print("[+] Loading model and raw logits bypass...")
    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    # 1. Load Ground Truth Mask to locate the crack
    gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if gt_mask is None:
        raise FileNotFoundError(f"Could not load mask at {mask_path}")

    # Get coordinates of the crack (where mask > 0)
    y_coords, x_coords = np.where(gt_mask > 0)
    if len(y_coords) == 0:
        raise ValueError("No defect pixels found in the ground truth mask.")

    # Sort coordinates from top to bottom (by Y-coordinate)
    sorted_indices = np.argsort(y_coords)
    y_sorted = y_coords[sorted_indices]
    x_sorted = x_coords[sorted_indices]

    # 2. Run Direct Forward Pass to get continuous float probabilities
    img = cv2.imread(str(img_path))
    h_orig, w_orig = img.shape[:2]
    img_resized = cv2.resize(img, (imgsz, imgsz))

    img_tensor = (
        torch.from_numpy(img_resized[:, :, ::-1].copy()).permute(2, 0, 1).float()
        / 255.0
    )
    img_tensor = img_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        raw_output = net(img_tensor)

    logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output
    probs = torch.sigmoid(logits)

    target_channel = 1 if logits.shape[1] > 1 else 0
    raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()

    # Scale probabilities back to original canvas resolution
    probs_resized = cv2.resize(
        raw_probs_map, (w_orig, h_orig), interpolation=cv2.INTER_LINEAR
    )

    # 3. Extract confidence values along the sorted crack path
    # To handle multiple pixels on the same Y-row, we take the max probability per unique Y-row
    unique_ys = np.unique(y_sorted)
    profile_data = []

    for y in unique_ys:
        # Find all X coordinates matching this Y row on the crack
        xs_at_y = x_sorted[y_sorted == y]
        # Grab the maximum model probability along this row's crack section
        max_prob = np.max([probs_resized[y, x] for x in xs_at_y])
        profile_data.append((y, max_prob))

    # 4. Generate ASCII terminal plot of the 1D Profile (Top to Bottom of the crack)
    print("\n" + "=" * 60)
    print(" 📈 1D CRACK CONFIDENCE PROFILE (TOP TO BOTTOM)")
    print("=" * 60)
    print(f"Crack Span: Y={unique_ys.min()} (Top) to Y={unique_ys.max()} (Bottom)")
    print("=" * 60)

    # Downsample the profile to ~30 steps so it fits cleanly in the terminal screen
    step_size = max(1, len(profile_data) // 30)
    downsampled_profile = profile_data[::step_size]

    for y, prob in downsampled_profile:
        # Create a horizontal bar representing the confidence level
        bar_length = int(prob * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"Y={y:03d} | [{bar}] {prob:.3f}")

    print("=" * 60)

    # Calculate key metrics
    avg_conf = np.mean([p[1] for p in profile_data])
    top_third_conf = np.mean([p[1] for p in profile_data[: len(profile_data) // 3]])
    bottom_third_conf = np.mean([p[1] for p in profile_data[-len(profile_data) // 3 :]])

    print(f"Average Confidence: {avg_conf:.3f}")
    print(f"Top-Third (Tip) Average: {top_third_conf:.3f}")
    print(f"Bottom-Third (Base) Average: {bottom_third_conf:.3f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    model_weight = "mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt"
    img_file = "data/processed/sod/val/images/000552.jpg"
    mask_file = "data/processed/sod/val/masks/000552.png"

    extract_1d_confidence_profile(model_weight, img_file, mask_file)
