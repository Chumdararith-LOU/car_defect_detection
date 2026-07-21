import cv2
from pathlib import Path


def fix_mask_pixels():
    base_dir = Path("data/processed/sod")
    mask_files = list(base_dir.glob("*/masks/*.png"))

    count = 0
    for mask_path in mask_files:
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue

        mask[mask > 0] = 1

        cv2.imwrite(str(mask_path), mask)
        count += 1

    print(f"[✓] Successfully converted {count} masks to use Class ID 1.")


if __name__ == "__main__":
    fix_mask_pixels()
