import cv2
import os
from pathlib import Path

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Identify and isolate background-only clean files"
    )
    parser.add_argument(
        "--masks_dir", type=str, required=True, help="Path to evaluation masks folder"
    )
    parser.add_argument(
        "--images_dir",
        type=str,
        required=True,
        help="Path to corresponding images folder",
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Max clean file sample paths to extract"
    )
    args = parser.parse_args()

    masks_dir = Path(args.masks_dir)
    images_dir = Path(args.images_dir)

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
                    if len(clean_images) >= args.limit:
                        break

    for path in clean_images:
        print(f'"{path}",')
