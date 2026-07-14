import cv2
import numpy as np
from pathlib import Path
import yaml
import shutil


def tile_image(img, target_size=(512, 512)):
    """Slices an image into 4 quadrants, padding to target size if necessary."""
    h, w = img.shape[:2]
    h_mid, w_mid = h // 2, w // 2

    tiles = [
        img[0:h_mid, 0:w_mid],
        img[0:h_mid, w_mid:w],
        img[h_mid:h, 0:w_mid],
        img[h_mid:h, w_mid:w],
    ]
    return tiles


def process_dataset(src_dir, dest_dir):
    src, dest = Path(src_dir), Path(dest_dir)
    if dest.exists():
        shutil.rmtree(dest)

    for split in ["train", "val"]:
        (dest / split / "images").mkdir(parents=True, exist_ok=True)
        (dest / split / "masks").mkdir(parents=True, exist_ok=True)

        imgs = list((src / split / "images").glob("*.jpg"))
        for img_p in imgs:
            mask_p = src / split / "masks" / f"{img_p.stem}.png"
            if not mask_p.exists():
                continue

            img, mask = cv2.imread(str(img_p)), cv2.imread(
                str(mask_p), cv2.IMREAD_GRAYSCALE
            )

            img_tiles = tile_image(img)
            mask_tiles = tile_image(mask)

            for i, (t_img, t_mask) in enumerate(zip(img_tiles, mask_tiles)):
                # Only save tiles that actually contain car pixels (ignore empty background tiles)
                if np.sum(t_img) > 0:
                    cv2.imwrite(
                        str(dest / split / "images" / f"{img_p.stem}_t{i}.jpg"), t_img
                    )
                    cv2.imwrite(
                        str(dest / split / "masks" / f"{img_p.stem}_t{i}.png"), t_mask
                    )

    # Generate the new YOLO dataset YAML
    yaml_content = {
        "path": str(dest.absolute()),
        "train": "train/images",
        "val": "val/images",
        "names": {0: "background", 1: "defect"},
    }
    with open(dest / "sod_data_tiled.yaml", "w") as f:
        yaml.dump(yaml_content, f)

    print(f"[✓] Tiled dataset created at {dest}")


if __name__ == "__main__":
    process_dataset("data/processed/sod", "data/processed/sod_tiled")
