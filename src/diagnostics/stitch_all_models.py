import os
import cv2
import numpy as np
from glob import glob
from ultralytics import YOLO

# 1. Setup paths and targets
TEST_IMG_DIR = "data/processed/sod/test/images"
TEST_MASK_DIR = "data/processed/sod/test/masks"
OUTPUT_DIR = "predictions_stitched_3x2"
PANEL_SIZE = (
    480,
    480,
)  # Uniform size for each grid panel to avoid scaling misalignment
DEVICE = "cuda:0"  # Explicitly force GPU execution

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Gather the models from your training runs
MODELS_CONFIG = [
    {
        "name": "M1 (122e3f76)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt",
    },
    {
        "name": "M2 (403d6b31)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt",
    },
    {
        "name": "M3 (f3b8f26d)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt",
    },
    {
        "name": "M4 (ba4046a3)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt",
    },
    {
        "name": "M5 (0b8ace4b)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt",
    },
]

print(f"[*] Loading {len(MODELS_CONFIG)} models onto GPU ({DEVICE})...")
loaded_models = []
for cfg in MODELS_CONFIG:
    if os.path.exists(cfg["path"]):
        # Load directly and bind to the GPU target
        model = YOLO(cfg["path"]).to(DEVICE)
        loaded_models.append({"name": cfg["name"], "model": model})
    else:
        print(
            f"[!] Warning: Model file missing, using empty fallback for {cfg['name']}"
        )
        loaded_models.append({"name": cfg["name"], "model": None})


def create_panel(base_img, mask, title, color):
    """Resizes canvas, overlays binary mask with color, and stamps text label."""
    canvas = cv2.resize(base_img, PANEL_SIZE)
    resized_mask = cv2.resize(mask, PANEL_SIZE, interpolation=cv2.INTER_NEAREST)

    overlay = canvas.copy()
    overlay[resized_mask > 0] = color
    blended = cv2.addWeighted(canvas, 0.6, overlay, 0.4, 0)

    # Add clear bounding text header
    cv2.putText(
        blended,
        title,
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return blended


# 3. Process test files
image_paths = glob(os.path.join(TEST_IMG_DIR, "*"))
if not image_paths:
    print(f"[!] Error: No test images found inside {TEST_IMG_DIR}")
    exit()

print(f"[*] Starting raw native batch inference on {len(image_paths)} test files...")

for img_path in image_paths:
    filename = os.path.basename(img_path)
    basename, _ = os.path.splitext(filename)

    img = cv2.imread(img_path)
    if img is None:
        continue

    # Search for matching Ground Truth Mask
    mask_path = os.path.join(TEST_MASK_DIR, f"{basename}.png")
    if not os.path.exists(mask_path):
        mask_path = os.path.join(TEST_MASK_DIR, filename)

    if os.path.exists(mask_path):
        gt_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    else:
        gt_mask = np.zeros(img.shape[:2], dtype=np.uint8)

    # Generate Panel 1: Ground Truth (Colored Red)
    panels = [create_panel(img, gt_mask, "GROUND TRUTH", [0, 0, 255])]

    # Generate Panels 2-6: Plain Native Model Predictions (Colored Neon Green)
    for cfg in loaded_models:
        if cfg["model"] is not None:
            # Run inference directly on GPU with native argmax properties
            results = cfg["model"](img, device=DEVICE, verbose=False)
            result = results[0]

            if hasattr(result, "semantic_mask") and result.semantic_mask is not None:
                pred_mask = result.semantic_mask.data.cpu().numpy().astype(np.uint8)
            elif hasattr(result, "masks") and result.masks is not None:
                pred_mask = result.masks.data[0].cpu().numpy().astype(np.uint8)
            else:
                pred_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        else:
            pred_mask = np.zeros(img.shape[:2], dtype=np.uint8)

        panels.append(create_panel(img, pred_mask, cfg["name"], [0, 255, 0]))

    # Ensure we have exactly 6 panels to build a clean 3x2 matrix layout
    while len(panels) < 6:
        blank = np.zeros((PANEL_SIZE[1], PANEL_SIZE[0], 3), dtype=np.uint8)
        panels.append(blank)

    # Build the 3x2 stitched graphic
    row1 = np.hstack((panels[0], panels[1], panels[2]))
    row2 = np.hstack((panels[3], panels[4], panels[5]))
    stitched_grid = np.vstack((row1, row2))

    # Save output frame
    save_path = os.path.join(OUTPUT_DIR, f"grid_{basename}.png")
    cv2.imwrite(save_path, stitched_grid)

print(f"[✓] Native inference complete. 3x2 matrix layouts saved to: {OUTPUT_DIR}")
