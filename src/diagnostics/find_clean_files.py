import cv2
import os
from pathlib import Path

masks_dir = Path("data/processed/sod_tiled/masks/val")
images_dir = Path("data/processed/sod_tiled/images/val")

clean_images = []

print(f"[+] Scanning masks in {masks_dir} to find clean files...")

for mask_file in sorted(os.listdir(masks_dir)):
    mask_path = masks_dir / mask_file

    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is not None:
        if mask.max() == 0:
            img_path = images_dir / (mask_path.stem + ".png")
            if not img_path.exists():
                img_path = images_dir / (mask_path.stem + ".jpg")

            if img_path.exists():
                clean_images.append(str(img_path))
                if len(clean_images) >= 20:
                    break

for path in clean_images:
    print(f'"{path}",')
