import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# --- Configuration ---
model_path = "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt"
images_dir = Path("data/processed/sod_tiled/images/test")
labels_dir = Path("data/processed/sod_tiled/labels/test")
output_dir = Path("inference_results_stitched")

output_dir.mkdir(parents=True, exist_ok=True)
model = YOLO(model_path)  # [cite: 1]


# --- Helper Function for Overlay ---
def create_overlay(image, mask, alpha=0.5):
    """
    Overlays a colorized mask onto the original image.
    The background (class 0) remains completely unchanged.
    """
    # Define colors for classes (BGR format for OpenCV)
    colors = np.array(
        [
            [0, 0, 0],  # Background (will be ignored)
            [0, 0, 255],  # Defect 1 (Red)
            [0, 255, 255],  # Defect 2 (Yellow)
        ],
        dtype=np.uint8,
    )

    # Clip mask and map to colors
    mask_clipped = np.clip(mask, 0, len(colors) - 1)
    colorized_mask = colors[mask_clipped]

    # Create a boolean mask of where defects actually exist
    defect_pixels = mask_clipped > 0

    # Create a copy of the original image to modify
    overlay = image.copy()

    # Apply alpha blending only on the defect pixels
    if defect_pixels.any():
        blended = cv2.addWeighted(image, 1 - alpha, colorized_mask, alpha, 0)
        overlay[defect_pixels] = blended[defect_pixels]

    return overlay


# --- Setup File Search ---
image_paths = []
for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"]:
    image_paths.extend(images_dir.glob(ext))

if len(image_paths) == 0:
    print(f"⚠️ Warning: No images found in '{images_dir}'.")
else:
    print(f"Found {len(image_paths)} images. Generating overlays...")

# --- Main Inference Loop ---
for img_path in image_paths:

    # 1. Load Original Image
    img = cv2.imread(str(img_path))
    if img is None:
        continue
    h, w = img.shape[:2]

    # 2. Load Ground Truth Label & Create Overlay
    label_path = labels_dir / img_path.with_suffix(".png").name
    if label_path.exists():
        gt_mask = cv2.imread(str(label_path), cv2.IMREAD_GRAYSCALE)
    else:
        gt_mask = np.zeros((h, w), dtype=np.uint8)

    gt_overlay = create_overlay(img, gt_mask, alpha=0.5)

    # 3. Run YOLO Inference & Create Overlay
    results = model(str(img_path), verbose=False)
    result = results[0]

    if result.semantic_mask is not None:
        pred_tensor = result.semantic_mask.data  # [cite: 1]
        pred_mask = pred_tensor.cpu().numpy().astype(np.uint8)
    else:
        pred_mask = np.zeros((h, w), dtype=np.uint8)

    if pred_mask.shape != (h, w):
        pred_mask = cv2.resize(pred_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    pred_overlay = create_overlay(img, pred_mask, alpha=0.5)

    # 4. Stitch Images Horizontally
    # Now combining: [Original] | [Ground Truth Overlay] | [Prediction Overlay]
    stitched_image = np.hstack((img, gt_overlay, pred_overlay))

    # 5. Save the Stitched Output
    save_path = output_dir / f"stitched_{img_path.name}"
    cv2.imwrite(str(save_path), stitched_image)

if len(image_paths) > 0:
    print(f"Inference complete! Stitched overlays saved to: {output_dir}")
