import cv2
import numpy as np
import torch
from pathlib import Path
from ultralytics import YOLO


def deep_xray_diagnostic(model_path, image_name, img_dir):
    print(f"[+] Loading Deep X-Ray for {image_name}...")
    model = YOLO(model_path, task="semantic")

    img_path = Path(img_dir) / image_name
    if not img_path.exists():
        print(f"[!] Could not find {img_path}")
        return

    # --- PART 1: The Supervisor's Sanity Check ---
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

    # --- PART 2: The Direct Forward Pass (Bypassing Post-Processing) ---
    print("\n--- PART 2: Direct Forward Pass (Intercepting Raw Logits) ---")
    net = model.model
    net.eval()  # Set to evaluation mode
    device = next(net.parameters()).device

    # 1. Manual Preprocessing
    img = cv2.imread(str(img_path))
    img_resized = cv2.resize(img, (640, 640))
    # Convert BGR to RGB, HWC to CHW format, normalize to [0,1], and add batch dimension
    img_tensor = (
        torch.from_numpy(img_resized[:, :, ::-1].copy())
        .permute(2, 0, 1)
        .float()
        .unsqueeze(0)
        / 255.0
    )
    img_tensor = img_tensor.to(device)

    # 2. The Raw Forward Pass
    with torch.no_grad():
        raw_output = net(img_tensor)

    # 3. Output Shape Inspection
    if isinstance(raw_output, tuple):
        print(f"Raw Output is a Tuple of length: {len(raw_output)}")
        logits = raw_output[0]  # The primary segmentation logits usually sit in index 0
    else:
        print("Raw Output is a single Tensor")
        logits = raw_output

    print(f"Logits Shape: {logits.shape} (Format: [Batch, Channels, Height, Width])")

    # 4. Convert Logits to Probabilities using Sigmoid
    probs = torch.sigmoid(logits)

    # 5. Channel Selection (Handling the background class trap)
    C = logits.shape[1]
    target_channel = 1 if C > 1 else 0
    print(
        f"Extracting probabilities from Channel {target_channel} (Total channels: {C})..."
    )

    raw_probs_map = probs[0, target_channel, :, :].cpu().numpy()
    print(
        f"True Probability Map Min/Max: {raw_probs_map.min():.5f} / {raw_probs_map.max():.5f}"
    )

    # --- PART 3: Visualizing the Ghost ---
    heatmap_pixels = (raw_probs_map * 255).astype(np.uint8)
    # Red = High Confidence, Blue = Low Confidence
    heatmap_colored = cv2.applyColorMap(heatmap_pixels, cv2.COLORMAP_JET)

    output_path = f"deep_xray_{image_name}"
    cv2.imwrite(output_path, heatmap_colored)
    print(f"\n[✓] Deep X-Ray heatmap saved to {output_path}")
    print(
        "[!] Open this image. If you see a faint red/yellow line where the scratch is, Focal Loss will save us."
    )


if __name__ == "__main__":
    model_weight = "yolo26n-sem.pt"
    img_directory = "data/processed/sod/val/images"

    deep_xray_diagnostic(model_weight, "000552.jpg", img_directory)
