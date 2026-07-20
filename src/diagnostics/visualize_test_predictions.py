import os
import cv2
import numpy as np
from glob import glob
from ultralytics import YOLO

# 1. Setup paths
MODEL_PATH = "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt"  # Adjust this path to your best.pt location
TEST_IMG_DIR = "data/processed/sod/test/images"
TEST_MASK_DIR = "data/processed/sod/test/masks"
OUTPUT_DIR = "predictions_stitched"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 2. Load the trained YOLO26-sem model
print(f"Loading model from {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

# 3. Generate a distinct color palette for classes (up to 256 classes)
np.random.seed(42)
COLOR_PALETTE = np.random.randint(0, 255, size=(256, 3), dtype=np.uint8)
COLOR_PALETTE[0] = [0, 0, 0]  # Background class remains uncolored/black


def apply_mask_overlay(image, mask, palette, alpha=0.4):
    """Maps class IDs to colors and overlays them onto the original image."""
    # Create colored mask
    colored_mask = palette[mask]

    # Ignore background (0) when blending so original image shows clearly
    mask_pixel_cond = mask > 0

    overlay = image.copy()
    overlay[mask_pixel_cond] = cv2.addWeighted(
        image, 1 - alpha, colored_mask, alpha, 0
    )[mask_pixel_cond]

    return overlay


def add_label_text(image, text):
    """Utility to add text labels on top of the images."""
    img_labeled = image.copy()
    cv2.putText(
        img_labeled,
        text,
        (15, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return img_labeled


# 4. Loop through the test images
image_paths = glob(os.path.join(TEST_IMG_DIR, "*"))
if not image_paths:
    print(f"No images found in {TEST_IMG_DIR}. Please check your path.")
    exit()

print(f"Found {len(image_paths)} images. Starting inference...")

for img_path in image_paths:
    filename = os.path.basename(img_path)
    basename, _ = os.path.splitext(filename)

    # Find matching ground truth mask (assuming PNG format)
    mask_path = os.path.join(TEST_MASK_DIR, f"{basename}.png")
    if not os.path.exists(mask_path):
        # Fallback check if your masks use the same extension as images
        mask_path = os.path.join(TEST_MASK_DIR, filename)
        if not os.path.exists(mask_path):
            print(f"Warning: Mask not found for {filename}, skipping.")
            continue

    # Load original image and ground truth mask
    img = cv2.imread(img_path)
    gt_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    if img is None or gt_mask is None:
        print(f"Error reading image or mask for {filename}, skipping.")
        continue

    # Ensure mask matches image dimensions
    if gt_mask.shape[:2] != img.shape[:2]:
        gt_mask = cv2.resize(
            gt_mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST
        )

    # Run YOLO26-sem Inference
    results = model(img, verbose=False)
    result = results[0]

    # Extract predicted semantic mask
    if hasattr(result, "semantic_mask") and result.semantic_mask is not None:
        # Convert torch tensor map down to numpy array
        pred_mask = result.semantic_mask.data.cpu().numpy().astype(np.uint8)
    else:
        # Fallback to an empty map if no prediction mask exists
        pred_mask = np.zeros(img.shape[:2], dtype=np.uint8)

    # Resize prediction mask if it doesn't match the original image size
    if pred_mask.shape[:2] != img.shape[:2]:
        pred_mask = cv2.resize(
            pred_mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST
        )

    # Generate overlay visuals
    gt_overlay = apply_mask_overlay(img, gt_mask, COLOR_PALETTE)
    pred_overlay = apply_mask_overlay(img, pred_mask, COLOR_PALETTE)

    # Add descriptive text banners
    gt_overlay = add_label_text(gt_overlay, "Ground Truth")
    pred_overlay = add_label_text(pred_overlay, "YOLO26 Prediction")

    # Stitch images side-by-side horizontally
    stitched_output = np.hstack((gt_overlay, pred_overlay))

    # Save output to disk
    save_path = os.path.join(OUTPUT_DIR, f"comparison_{basename}.png")
    cv2.imwrite(save_path, stitched_output)

print(f"Inference completed! Visualizations saved to: {OUTPUT_DIR}")
