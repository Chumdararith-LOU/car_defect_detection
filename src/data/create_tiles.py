import cv2
from pathlib import Path
import yaml


def tile_image(img, overlap_frac=0.15):
    h, w = img.shape[:2]
    h_mid, w_mid = h // 2, w // 2
    oh, ow = int(h * overlap_frac), int(w * overlap_frac)

    # Calculate slices with overlap
    tiles = [
        img[0 : min(h, h_mid + oh), 0 : min(w, w_mid + ow)],  # top-left
        img[0 : min(h, h_mid + oh), max(0, w_mid - ow) : w],  # top-right
        img[max(0, h_mid - oh) : h, 0 : min(w, w_mid + ow)],  # bottom-left
        img[max(0, h_mid - oh) : h, max(0, w_mid - ow) : w],  # bottom-right
    ]
    return tiles


def process_dataset(src_dir, dest_dir):
    src, dest = Path(src_dir), Path(dest_dir)
    for split in ["train", "val"]:
        (dest / "images" / split).mkdir(parents=True, exist_ok=True)
        (dest / "masks" / split).mkdir(parents=True, exist_ok=True)

    imgs = list((src / "train" / "images").glob("*.jpg")) + list(
        (src / "val" / "images").glob("*.jpg")
    )

    for img_p in imgs:
        split = img_p.parent.name
        mask_p = src / split / "masks" / f"{img_p.stem}.png"
        if not mask_p.exists():
            continue

        img, mask = cv2.imread(str(img_p)), cv2.imread(
            str(mask_p), cv2.IMREAD_GRAYSCALE
        )

        img_tiles = tile_image(img)
        mask_tiles = tile_image(mask)

        for i, (t_img, t_mask) in enumerate(zip(img_tiles, mask_tiles)):
            cv2.imwrite(str(dest / "images" / split / f"{img_p.stem}_t{i}.jpg"), t_img)
            cv2.imwrite(str(dest / "masks" / split / f"{img_p.stem}_t{i}.png"), t_mask)

    yaml_content = {
        "path": str(dest.absolute()),
        "train": "images/train",
        "val": "images/val",
        "masks_dir": "masks",
        "names": {0: "background", 1: "defect"},
    }
    with open(dest / "sod_data_tiled.yaml", "w") as f:
        yaml.dump(yaml_content, f)

    print(f"[✓] Tiled dataset with overlap created at {dest}")


if __name__ == "__main__":
    process_dataset("data/processed/sod", "data/processed/sod_tiled")
