import shutil
from pathlib import Path
import cv2
import yaml


def tile_image(img, overlap_frac=0.15):
    h, w = img.shape[:2]
    h_mid, w_mid = h // 2, w // 2
    oh, ow = int(h * overlap_frac), int(w * overlap_frac)

    return [
        img[0 : min(h, h_mid + oh), 0 : min(w, w_mid + ow)],  # top-left
        img[0 : min(h, h_mid + oh), max(0, w_mid - ow) : w],  # top-right
        img[max(0, h_mid - oh) : h, 0 : min(w, w_mid + ow)],  # bottom-left
        img[max(0, h_mid - oh) : h, max(0, w_mid - ow) : w],  # bottom-right
    ]


def process_dataset(src_dir, dest_dir, overlap_frac=0.15, clean_dest=True):
    src, dest = Path(src_dir), Path(dest_dir)

    if clean_dest and dest.exists():
        shutil.rmtree(dest)

    image_roots = sorted(src.glob("*/images"))
    if not image_roots:
        print(f"[!] No */images folders found under {src}. Check src_dir.")
        return

    processed_splits = []

    for img_root in image_roots:
        split = img_root.parent.name
        mask_root = img_root.parent / "masks"

        n_written, n_skipped = 0, 0
        (dest / "images" / split).mkdir(parents=True, exist_ok=True)
        (dest / "masks" / split).mkdir(parents=True, exist_ok=True)

        for img_p in sorted(img_root.glob("*.jpg")):
            mask_p = mask_root / f"{img_p.stem}.png"
            if not mask_p.exists():
                n_skipped += 1
                continue

            img = cv2.imread(str(img_p))
            mask = cv2.imread(str(mask_p), cv2.IMREAD_GRAYSCALE)
            if img is None or mask is None:
                n_skipped += 1
                continue

            img_tiles = tile_image(img, overlap_frac)
            mask_tiles = tile_image(mask, overlap_frac)

            for i, (t_img, t_mask) in enumerate(zip(img_tiles, mask_tiles)):
                cv2.imwrite(
                    str(dest / "images" / split / f"{img_p.stem}_t{i}.png"), t_img
                )
                cv2.imwrite(
                    str(dest / "masks" / split / f"{img_p.stem}_t{i}.png"), t_mask
                )
            n_written += 1

        processed_splits.append(split)
        print(
            f"[+] {split}: {n_written} images tiled "
            f"({n_written * 4} tiles), {n_skipped} skipped (no/bad mask)"
        )

    yaml_content = {
        "path": str(dest.absolute()),
        "masks_dir": "masks",
        "names": {0: "background", 1: "defect"},
    }
    for split in processed_splits:
        yaml_content[split] = f"images/{split}"

    yaml_path = dest / "sod_data_tiled.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(yaml_content, f, sort_keys=False)

    print(f"[\u2713] Tiled dataset created at {dest}")
    print(f"[\u2713] Dataset YAML written to {yaml_path}")


if __name__ == "__main__":
    import argparse
    from stage1.utils.config_helpers import load_pipeline_config

    parser = argparse.ArgumentParser(description="Configurable Dataset Tiling Engine")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pipeline_config.yaml",
        help="Path to YAML config",
    )
    args = parser.parse_args()

    cfg = load_pipeline_config(args.config)

    overlap = cfg.get("dataset", {}).get("overlap_percent", 0.15)

    src_data_dir = "data/processed/sod"
    dest_data_dir = "data/processed/sod_tiled"

    print(f"[*] Initializing tiling pipeline with overlap fraction: {overlap}")
    process_dataset(src_data_dir, dest_data_dir, overlap_frac=overlap)
