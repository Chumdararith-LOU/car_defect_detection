import json
import shutil
from pathlib import Path
from collections import Counter
import numpy as np

# --- CONFIGURATION ---
JSON_PATH = Path("data/raw/cvat_golden_2000/annotations/instances_default.json")
SRC_IMAGES_DIR = Path("data/raw/cvat_golden_2000/images/default")
OUTPUT_DIR = Path("data/processed/cvat_golden_2000_yolo")

MAX_IMAGES = 2000

# --- TAXONOMY MAPPING ---
# CVAT Cat ID -> (Target Class Index, Target Class Name)
CLASS_MAPPING = {
    1: (0, "dent"),  # dent -> dent
    2: (0, "dent"),  # ding -> dent
    3: (1, "deform"),  # deform (kept separate)
    4: (2, "scratch"),  # scratch_hairline -> scratch
    5: (2, "scratch"),  # scratch_gouge -> scratch
    6: (3, "crack"),  # crack -> crack
    7: (4, "glass_shatter"),  # glass_shatter -> glass_shatter
    8: (5, "broken_lamp"),  # broken_lamp (kept separate)
    9: (6, "corrosion"),  # corrosion -> corrosion
    10: (7, "disjoint_part"),  # broken_components -> disjoint_part
}

TARGET_CLASSES = [
    "dent",  # 0
    "deform",  # 1
    "scratch",  # 2
    "crack",  # 3
    "glass_shatter",  # 4
    "broken_lamp",  # 5
    "corrosion",  # 6
    "disjoint_part",  # 7
]


def convert_dataset():
    out_images_dir = OUTPUT_DIR / "images"
    out_labels_dir = OUTPUT_DIR / "labels"
    out_images_dir.mkdir(parents=True, exist_ok=True)
    out_labels_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading COCO JSON from {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    # Slice the first 2,000 images
    all_images = coco_data.get("images", [])
    selected_images = all_images[:MAX_IMAGES]
    print(
        f"Processing the first {len(selected_images)} images out of {len(all_images)} total..."
    )

    selected_img_ids = {img["id"]: img for img in selected_images}

    # Group annotations by image_id
    img_annotations = {img_id: [] for img_id in selected_img_ids.keys()}
    for ann in coco_data.get("annotations", []):
        img_id = ann.get("image_id")
        if img_id in img_annotations:
            img_annotations[img_id].append(ann)

    class_counts = Counter()
    processed_images_count = 0
    images_with_defects = 0

    for img_id, img_meta in selected_img_ids.items():
        file_name = img_meta["file_name"]
        w = float(img_meta["width"])
        h = float(img_meta["height"])

        # Check source image existence
        src_img_path = SRC_IMAGES_DIR / file_name
        if not src_img_path.exists():
            print(f"Warning: Image missing on disk: {src_img_path}")
            continue

        # Copy image to processed directory
        shutil.copy2(src_img_path, out_images_dir / file_name)

        # Process annotations for this image
        anns = img_annotations[img_id]
        txt_filename = Path(file_name).stem + ".txt"
        txt_filepath = out_labels_dir / txt_filename

        label_lines = []

        for ann in anns:
            cat_id = ann.get("category_id")
            if cat_id not in CLASS_MAPPING:
                continue

            target_cls_id, target_cls_name = CLASS_MAPPING[cat_id]
            segmentations = ann.get("segmentation", [])

            if not segmentations:
                continue

            for seg in segmentations:
                if len(seg) < 6:  # Skip degenerate points/lines
                    continue

                normalized_coords = []
                for k in range(0, len(seg), 2):
                    x_norm = np.clip(seg[k] / w, 0.0, 1.0)
                    y_norm = np.clip(seg[k + 1] / h, 0.0, 1.0)
                    normalized_coords.append(f"{x_norm:.6f} {y_norm:.6f}")

                coord_str = " ".join(normalized_coords)
                label_lines.append(f"{target_cls_id} {coord_str}")
                class_counts[target_cls_name] += 1

        # Write label file (even if empty, to ensure 1:1 image-label mapping)
        with open(txt_filepath, "w", encoding="utf-8") as f_label:
            if label_lines:
                f_label.write("\n".join(label_lines) + "\n")
                images_with_defects += 1

        processed_images_count += 1

    # --- PRINT DETAILED SUMMARY FOR STUDYING ---
    print("\n" + "=" * 50)
    print("      DATASET CONVERSION & AUDIT SUMMARY")
    print("=" * 50)
    print(f"Total Images Processed   : {processed_images_count}")
    print(f"Images with Defects     : {images_with_defects}")
    print(f"Clean Images (0 defects): {processed_images_count - images_with_defects}")
    print("\nInstance Counts Per Class:")
    print("-" * 35)
    for cls_idx, cls_name in enumerate(TARGET_CLASSES):
        count = class_counts[cls_name]
        print(f"  [{cls_idx}] {cls_name:<18}: {count:,} instances")
    print("=" * 50)
    print(f"Output saved to: {OUTPUT_DIR.resolve()}\n")


if __name__ == "__main__":
    convert_dataset()
