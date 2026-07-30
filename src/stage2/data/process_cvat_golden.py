import json
import shutil
import random
from pathlib import Path
import numpy as np

# Set fixed seed for reproducible train/val split
random.seed(42)

# Source & Destination Paths
JSON_PATH = Path("data/raw/cvat_golden_2000/annotations/instances_default.json")
SRC_IMG_DIR = Path("data/raw/cvat_golden_2000/images/default")
OUTPUT_DIR = Path("data/processed/cvat_golden_2000")

# Taxonomy Mapping (8 Classes Total)
CLASS_MAPPING = {
    1: 0,  # dent -> dent
    2: 0,  # ding -> dent
    3: 1,  # deform -> deform
    4: 2,  # scratch_hairline -> scratch
    5: 2,  # scratch_gouge -> scratch
    6: 3,  # crack -> crack
    7: 4,  # glass_shatter -> glass_shatter
    8: 5,  # broken_lamp -> broken_lamp
    9: 6,  # corrosion -> corrosion
    10: 7,  # broken_components -> disjoint_part
}

CLASS_NAMES = [
    "dent",
    "deform",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_lamp",
    "corrosion",
    "disjoint_part",
]


def main():
    print(f"Loading annotation JSON from {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        coco = json.load(f)

    # 1. Isolate strictly the FIRST 2000 images
    all_images = coco["images"][:2000]
    target_img_ids = {img["id"] for img in all_images}
    # img_map = {img["id"]: img for img in all_images}

    print(f"Selected first {len(all_images)} images for processing.")

    # 2. Group annotations by image_id
    img_annotations = {img_id: [] for img_id in target_img_ids}
    for ann in coco.get("annotations", []):
        img_id = ann.get("image_id")
        if img_id in target_img_ids:
            img_annotations[img_id].append(ann)

    # 3. 80/20 Train / Val Split
    img_ids = list(all_images)
    random.shuffle(img_ids)
    split_idx = int(len(img_ids) * 0.8)

    train_imgs = img_ids[:split_idx]
    val_imgs = img_ids[split_idx:]

    splits = {"train": train_imgs, "val": val_imgs}

    # Prepare directories
    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 4. Convert and Save
    stats = {split: {cat: 0 for cat in CLASS_NAMES} for split in ["train", "val"]}

    for split, img_list in splits.items():
        print(f"\nProcessing '{split}' split ({len(img_list)} images)...")
        for img_meta in img_list:
            img_id = img_meta["id"]
            file_name = img_meta["file_name"]
            w_g = float(img_meta["width"])
            h_g = float(img_meta["height"])

            # Copy Image
            src_img_path = SRC_IMG_DIR / file_name
            dst_img_path = OUTPUT_DIR / "images" / split / file_name
            if src_img_path.exists():
                shutil.copy2(src_img_path, dst_img_path)

            # Generate YOLO Label Text
            txt_filename = Path(file_name).stem + ".txt"
            txt_filepath = OUTPUT_DIR / "labels" / split / txt_filename

            label_lines = []
            for ann in img_annotations[img_id]:
                cat_id = ann.get("category_id")
                if cat_id not in CLASS_MAPPING:
                    continue

                yolo_class_id = CLASS_MAPPING[cat_id]
                segmentations = ann.get("segmentation", [])

                if not segmentations:
                    continue

                for seg in segmentations:
                    if len(seg) < 6:  # Skip invalid polygons
                        continue

                    # Normalize points [0, 1]
                    norm_coords = []
                    for k in range(0, len(seg), 2):
                        x_norm = np.clip(seg[k] / w_g, 0.0, 1.0)
                        y_norm = np.clip(seg[k + 1] / h_g, 0.0, 1.0)
                        norm_coords.append(f"{x_norm:.6f} {y_norm:.6f}")

                    coord_str = " ".join(norm_coords)
                    label_lines.append(f"{yolo_class_id} {coord_str}")
                    stats[split][CLASS_NAMES[yolo_class_id]] += 1

            if label_lines:
                with open(txt_filepath, "w", encoding="utf-8") as f_txt:
                    f_txt.write("\n".join(label_lines) + "\n")

    # 5. Output YAML Dataset Configuration File
    data_yaml = {
        "path": str(OUTPUT_DIR.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(CLASS_NAMES)},
    }

    yaml_path = OUTPUT_DIR / "dataset.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f_yaml:
        import yaml

        yaml.dump(data_yaml, f_yaml, sort_keys=False)

    print("\nProcessing complete!")
    print(f"Dataset generated at: {OUTPUT_DIR}")
    print(f"YAML config saved to: {yaml_path}\n")
    print("Instance counts per class:")
    for split in ["train", "val"]:
        print(f"  [{split.upper()}]", stats[split])


if __name__ == "__main__":
    main()
