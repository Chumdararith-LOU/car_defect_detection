import cv2
import numpy as np
import torch
import os
from pathlib import Path
from ultralytics import YOLO


def deep_xray_diagnostic(model_path, img_path, output_dir="reports"):
    img_path = Path(img_path)
    print(f"[+] Loading Deep X-Ray for {img_path.name}...")
    model = YOLO(model_path, task="semantic")

    if not img_path.exists():
        print(f"[!] Could not find {img_path}")
        return

    print("\n--- PART 1: Standard API Sanity Check ---")
    preds = model.predict(
        str(img_path), imgsz=640, conf=0.001, retina_masks=True, verbose=False
    )
    print(
        f"Attributes of preds[0]: {[a for a in dir(preds[0]) if not a.startswith('_')]}"
    )

    if preds[0].masks is not None:
        d = preds[0].masks.data
        print(f"Mask Shape: {d.shape}, Dtype: {d.dtype}")
        print(f"Unique values (first 10): {torch.unique(d)[:10]}")
    else:
        print(
            "[!] preds[0].masks is None! The standard API completely stripped the output."
        )

    print("\n--- PART 2: Direct Forward Pass (Intercepting Raw Logits) ---")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    img = cv2.imread(str(img_path))
    img_resized = cv2.resize(img, (640, 640))
    img_tensor = (
        torch.from_numpy(img_resized[:, :, ::-1].copy())
        .permute(2, 0, 1)
        .float()
        .unsqueeze(0)
        / 255.0
    )
    img_tensor = img_tensor.to(device)

    with torch.no_grad():
        raw_output = net(img_tensor)

    if isinstance(raw_output, tuple):
        print(f"Raw Output is a Tuple of length: {len(raw_output)}")
        logits = raw_output[0]
    else:
        print("Raw Output is a single Tensor")
        logits = raw_output

    print(f"Logits Shape: {logits.shape} (Format: [Batch, Channels, Height, Width])")

    probs = torch.sigmoid(logits)

    C = logits.shape[1]
    target_channel = 1 if C > 1 else 0
    print(
        f"Extracting probabilities from Channel {target_channel} (Total channels: {C})..."
    )

    raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()
    print(
        f"True Probability Map Min/Max: {raw_probs_map.min():.5f} / {raw_probs_map.max():.5f}"
    )

    heatmap_pixels = (raw_probs_map * 255).astype(np.uint8)
    heatmap_colored = cv2.applyColorMap(heatmap_pixels, cv2.COLORMAP_JET)

    output_path = Path(output_dir) / f"deep_xray_{img_path.name}"
    os.makedirs(output_dir, exist_ok=True)
    cv2.imwrite(str(output_path), heatmap_colored)
    print(f"\n[✓] Deep X-Ray heatmap saved to {output_path}")
    print(
        "[!] Open this image. If you see a faint red/yellow line where the scratch is, Focal Loss will save us."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Deep X-Ray Raw Logits Heatmap Diagnostic"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to YOLO semantic weights"
    )
    parser.add_argument(
        "--image", type=str, required=True, help="Path to input target image"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="docs/reports/figures",
        help="Directory to save the diagnostic heatmap",
    )
    args = parser.parse_args()

    deep_xray_diagnostic(
        model_path=args.model, img_path=args.image, output_dir=args.output_dir
    )
