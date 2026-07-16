# src/tests/find_clean_files.py

import cv2
import os
from pathlib import Path

# Adjust this path if you are using sod_tiled or sod
masks_dir = Path("data/processed/sod/val/masks")
images_dir = Path("data/processed/sod/val/images")

clean_images = []

print(f"[+] Scanning masks in {masks_dir} to find clean files...")

for mask_file in sorted(os.listdir(masks_dir)):
    mask_path = masks_dir / mask_file

    # Load mask in grayscale
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is not None:
        # If the maximum pixel value in the mask is 0, it is completely black (no defect)
        if mask.max() == 0:
            # Match the mask filename to the image filename (e.g., change .png to .jpg)
            img_name = mask_path.stem + ".jpg"
            img_path = images_dir / img_name

            if img_path.exists():
                clean_images.append(str(img_path))
                if len(clean_images) >= 10:  # We only need 10 for our harness
                    break

print("\n========================================================")
print(" 🎯 FOUND 10 CLEAN IMAGES FOR YOUR VALIDATION HARNESS:")
print("========================================================")
for path in clean_images:
    print(f'        "{path}",')
print("========================================================\n")
