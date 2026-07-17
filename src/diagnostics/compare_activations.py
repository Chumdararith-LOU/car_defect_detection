import cv2
import numpy as np
import torch
from ultralytics import YOLO


def compare_activations(
    model_path, img_path, mask_path, imgsz=640, overlap_frac=0.15, target_y=379
):
    print("=" * 85)
    print(" 🔬 SIGMOID VS SOFTMAX ACTIVATION DIAGNOSTIC")
    print("=" * 85)

    model = YOLO(model_path, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    img = cv2.imread(str(img_path))
    gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if img is None or gt_mask is None:
        raise FileNotFoundError("Could not find source image or mask.")

    h_orig, w_orig = img.shape[:2]
    x_coords = np.where(gt_mask[target_y, :] > 0)[0]
    if len(x_coords) == 0:
        raise ValueError("No target mask pixels found at Y=379.")
    target_x = int(np.mean(x_coords))

    h_mid, w_mid = h_orig // 2, w_orig // 2
    oh, ow = int(h_orig * overlap_frac), int(w_orig * overlap_frac)
    y0, y1 = max(0, h_mid - oh), h_orig
    x0, x1 = 0, min(w_orig, w_mid + ow)

    tile_crop = img[y0:y1, x0:x1]
    t_h, t_w = tile_crop.shape[:2]

    tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
    img_tensor = (
        torch.from_numpy(tile_resized[:, :, ::-1].copy()).permute(2, 0, 1).float()
        / 255.0
    )
    img_tensor = img_tensor.unsqueeze(0).to(device)

    with torch.no_grad():
        raw_output = net(img_tensor)

    logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output

    probs_sig = torch.sigmoid(logits)
    sig_channel = 1 if logits.shape[1] > 1 else 0
    raw_sig_map = probs_sig[0, sig_channel, :, :].cpu().numpy()
    tile_sig_resized = cv2.resize(
        raw_sig_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
    )
    val_sigmoid = tile_sig_resized[target_y - y0, target_x - x0]

    probs_soft = torch.softmax(logits, dim=1)
    raw_soft_map = probs_soft[0, 1, :, :].cpu().numpy()
    tile_soft_resized = cv2.resize(
        raw_soft_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
    )
    val_softmax = tile_soft_resized[target_y - y0, target_x - x0]

    print(
        f"Target Coordinate: Global (X={target_x}, Y={target_y}) -> "
        f"Tile 2 Local (X={target_x - x0}, Y={target_y - y0})"
    )
    print("-" * 85)
    print(f"  Probability using SIGMOID: {val_sigmoid:.4f}")
    print(f"  Probability using SOFTMAX: {val_softmax:.4f}")
    print("-" * 85)

    if abs(val_sigmoid - 0.186) < 0.005:
        print(
            "[!] SIGMOID CONFIRMED: Your previous '0.186' value was computed using sigmoid!"
        )
        print("    You must use the SOFTMAX value for all future calibrations.")
    elif abs(val_softmax - 0.186) < 0.005:
        print(
            "[✓] SOFTMAX CONFIRMED: Your previous '0.186' value was already using "
            "the correct softmax activation."
        )
    else:
        print(
            "[ℹ] NEITHER MATCHES: Check your model weight path or coordinate mappings."
        )
    print("=" * 85 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Sigmoid vs Softmax Activation Diagnostic"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to YOLO semantic weights"
    )
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument(
        "--mask", type=str, required=True, help="Path to ground truth mask"
    )
    parser.add_argument(
        "--target_y", type=int, default=379, help="Target Y coordinate line to analyze"
    )
    parser.add_argument(
        "--imgsz", type=int, default=640, help="Inference resolution size"
    )
    args = parser.parse_args()

    compare_activations(
        model_path=args.model,
        img_path=args.image,
        mask_path=args.mask,
        imgsz=args.imgsz,
        target_y=args.target_y,
    )
