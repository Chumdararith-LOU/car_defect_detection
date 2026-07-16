import cv2
import numpy as np
import os
from pathlib import Path

masks_dir = Path("data/processed/sod/train/masks")

if not masks_dir.exists():
    print(f"[!] Directory does not exist: {masks_dir}")
    exit()

files = sorted(os.listdir(masks_dir))
total_files = len(files)
successfully_loaded = 0
completely_clean_count = 0
almost_clean_images = []

print("=" * 65)
print(" 🩺 MASKS DIRECTORY HEALTH CHECK")
print("=" * 65)
print(f"Total files found in directory: {total_files}")

for f in files[:100]:
    mask_path = masks_dir / f
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

    if mask is not None:
        successfully_loaded += 1
        max_val = mask.max()
        active_pixels = np.sum(mask > 0)
        total_pixels = mask.size
        defect_ratio = active_pixels / total_pixels

        if max_val == 0:
            completely_clean_count += 1
        elif defect_ratio < 0.001:  # Defect is less than 0.1% of the image
            almost_clean_images.append((f, defect_ratio))

print(
    f"Successfully read by OpenCV:  {successfully_loaded} / {min(100, total_files)} (sampled)"
)
print(f"Completely clean masks (max=0): {completely_clean_count}")
print(f"Extremely small defect masks:   {len(almost_clean_images)}")
print("-" * 65)

if successfully_loaded == 0:
    print(
        "[!] DIAGNOSIS: OpenCV is failing to read your files. Check your paths or file integrity!"
    )
elif completely_clean_count == 0:
    print(
        "[✓] DIAGNOSIS: Pathing is correct, but your dataset contains zero completely clean images."
    )
    print("    This is a defect-only dataset. Every image has labeled defects.")
    if almost_clean_images:
        print(
            "\n💡 Recommendation: Since you have no 100% clean images, use these "
            "'almost clean' images"
        )
        print(
            "   (tiny defects) as your shadow/noise test set in the validation harness:"
        )
        for name, ratio in almost_clean_images[:5]:
            # Convert mask filename to image filename
            img_name = Path(name).stem + ".jpg"
            print(
                f'        "data/processed/sod/val/images/{img_name}",  # Defect ratio: {ratio:.5f}'
            )
else:
    print(
        "[✓] DIAGNOSIS: Clean images exist! Review the original find_clean_files.py script mapping logic."
    )
print("=" * 65 + "\n")
