import json
import os
import shutil
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm

# Output Directory for CVAT Staging
STAGING_DIR = Path("data/cvat_staging")
STAGING_IMG_DIR = STAGING_DIR / "images"
OUTPUT_COCO_JSON = STAGING_DIR / "unified_cvat_annotations.json"

CVAT_CATEGORIES = [
    {"id": 1, "name": "dent"},
    {"id": 2, "name": "ding"},
    {"id": 3, "name": "deform"},
    {"id": 4, "name": "scratch_hairline"},
    {"id": 5, "name": "scratch_gouge"},
    {"id": 6, "name": "crack"},
    {"id": 7, "name": "glass_shatter"},
    {"id": 8, "name": "broken_component"},
    {"id": 9, "name": "corrosion"},
]

CLASS_MAP = {
    # CarDD / Standard COCO
    "dent": 1,
    "Dent": 1,
    "scratch": 4,  # Map generic scratch to scratch_hairline for manual review
    "Scratch": 4,
    "Paint chip": 4,
    "Flaking": 4,
    "crack": 6,
    "Cracked": 6,
    "glass shatter": 7,
    "glass_shatter": 7,
    "lamp broken": 8,
    "Broken part": 8,
    "Missing part": 8,  # Will be manually reviewed in CVAT
    "Corrosion": 9,
    "rust": 9,
    "corrosion": 9,
    "severe-corrosion": 9,
    "moderate-corrosion": 9,
    "mild-corrosion": 9,
    "corroded-part": 9,
}


def process_coco_source(
    source_name, json_path, images_base_dir, unified_data, state, max_images=None
):
    """Processes COCO datasets with optional image capping and mask area filtering."""
    if not os.path.exists(json_path):
        print(f"[!] Warning: COCO JSON path not found: {json_path}")
        return

    with open(json_path, "r") as f:
        coco = json.load(f)

    cat_lookup = {c["id"]: c["name"] for c in coco.get("categories", [])}
    image_id_map = {}

    print(f"[*] Processing COCO source: {source_name}...")

    # Filter/Cap images if max_images is set (e.g. for rust dataset)
    coco_images = coco["images"]
    if max_images and len(coco_images) > max_images:
        import random

        random.seed(42)  # Deterministic sampling
        coco_images = random.sample(coco_images, max_images)
        print(
            f"  [!] Capped {source_name} from {len(coco['images'])} down to {max_images} sampled images."
        )

    for img_obj in tqdm(coco_images, desc=f"  Images ({source_name})"):
        orig_filename = img_obj["file_name"]

        src_img_path = Path(images_base_dir) / orig_filename
        if not src_img_path.exists():
            matches = list(Path(images_base_dir).rglob(orig_filename))
            if matches:
                src_img_path = matches[0]
            else:
                continue

        new_filename = f"{source_name}_{src_img_path.name}"
        dst_img_path = STAGING_IMG_DIR / new_filename

        if not dst_img_path.exists():
            shutil.copy2(src_img_path, dst_img_path)

        state["image_id"] += 1
        image_id_map[img_obj["id"]] = state["image_id"]

        unified_data["images"].append(
            {
                "id": state["image_id"],
                "file_name": new_filename,
                "width": img_obj["width"],
                "height": img_obj["height"],
            }
        )

    for ann in coco.get("annotations", []):
        old_img_id = ann["image_id"]
        if old_img_id not in image_id_map:
            continue

        raw_cat_name = cat_lookup.get(ann["category_id"], "")
        if raw_cat_name not in CLASS_MAP:
            continue

        # Area filtering for rust dataset: drop micro-specks (<0.5%) and giant wall panels (>30%)
        if "rust" in source_name:
            img_info = next(
                i for i in unified_data["images"] if i["id"] == image_id_map[old_img_id]
            )
            img_area = img_info["width"] * img_info["height"]
            area_ratio = ann.get("area", 0) / img_area
            if area_ratio < 0.005 or area_ratio > 0.30:
                continue

        new_cat_id = CLASS_MAP[raw_cat_name]
        state["ann_id"] += 1

        unified_data["annotations"].append(
            {
                "id": state["ann_id"],
                "image_id": image_id_map[old_img_id],
                "category_id": new_cat_id,
                "segmentation": ann.get("segmentation", []),
                "area": ann.get("area", 0.0),
                "bbox": ann.get("bbox", []),
                "iscrowd": ann.get("iscrowd", 0),
            }
        )


def process_supervisely_source(source_name, supervisely_dir, unified_data, state):
    """Processes Supervisely dataset structure (images + individual JSON annotation files)."""
    base_path = Path(supervisely_dir)
    if not base_path.exists():
        print(f"[!] Warning: Supervisely path not found: {supervisely_dir}")
        return

    print(f"[*] Processing Supervisely source: {source_name}...")

    # Find all images recursively inside Supervisely folder structure
    image_extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG")
    img_paths = []
    for ext in image_extensions:
        img_paths.extend(list(base_path.rglob(ext)))

    # Limit to first 2200 images and sort for consistent ordering
    img_paths = sorted(img_paths)[:2200]

    for img_path in tqdm(img_paths, desc=f"  Supervisely Images ({source_name})"):
        # Locate corresponding Supervisely JSON file (e.g. image.jpg.json or image.json)
        json_path = Path(str(img_path) + ".json")
        if not json_path.exists():
            # Alternative: Check if inside parallel /ann/ directory
            parent_dir = img_path.parent.parent
            json_path = parent_dir / "ann" / f"{img_path.name}.json"
            if not json_path.exists():
                continue

        with open(json_path, "r") as f:
            ann_data = json.load(f)

        img_h = ann_data.get("size", {}).get("height")
        img_w = ann_data.get("size", {}).get("width")

        if not img_h or not img_w:
            cv_img = cv2.imread(str(img_path))
            if cv_img is None:
                continue
            img_h, img_w = cv_img.shape[:2]

        new_filename = f"{source_name}_{img_path.name}"
        dst_img_path = STAGING_IMG_DIR / new_filename

        if not dst_img_path.exists():
            shutil.copy2(img_path, dst_img_path)

        state["image_id"] += 1
        current_img_id = state["image_id"]

        unified_data["images"].append(
            {
                "id": current_img_id,
                "file_name": new_filename,
                "width": img_w,
                "height": img_h,
            }
        )

        # Parse Supervisely Objects
        for obj in ann_data.get("objects", []):
            raw_class = obj.get("classTitle")
            if raw_class not in CLASS_MAP:
                continue

            new_cat_id = CLASS_MAP[raw_class]
            points = obj.get("points", {}).get("exterior", [])

            if len(points) < 3:
                continue

            # Convert Supervisely exterior points [[x1, y1], [x2, y2]] to COCO flat list [x1, y1, x2, y2]
            polygon = []
            for pt in points:
                polygon.extend([float(pt[0]), float(pt[1])])

            pts_arr = np.array(points, dtype=np.float32)
            xmin, ymin = np.min(pts_arr, axis=0)
            xmax, ymax = np.max(pts_arr, axis=0)
            bbox = [
                float(xmin),
                float(ymin),
                float(xmax - xmin),
                float(ymax - ymin),
            ]
            area = float(cv2.contourArea(pts_arr))

            state["ann_id"] += 1
            unified_data["annotations"].append(
                {
                    "id": state["ann_id"],
                    "image_id": current_img_id,
                    "category_id": new_cat_id,
                    "segmentation": [polygon],
                    "area": area,
                    "bbox": bbox,
                    "iscrowd": 0,
                }
            )


def main():
    STAGING_IMG_DIR.mkdir(parents=True, exist_ok=True)

    unified_data = {
        "images": [],
        "annotations": [],
        "categories": CVAT_CATEGORIES,
    }

    state = {"image_id": 0, "ann_id": 0}

    # 1. CarDD COCO Sources
    cardd_base = Path("data/raw/CarDD_release/CarDD_COCO")
    process_coco_source(
        "cardd_train",
        cardd_base / "annotations/instances_train2017.json",
        cardd_base / "train2017",
        unified_data,
        state,
    )
    process_coco_source(
        "cardd_val",
        cardd_base / "annotations/instances_val2017.json",
        cardd_base / "val2017",
        unified_data,
        state,
    )
    process_coco_source(
        "cardd_test",
        cardd_base / "annotations/instances_test2017.json",
        cardd_base / "test2017",
        unified_data,
        state,
    )

    # 2. Supervisely Dataset Source (ADDED)
    supervisely_base = Path("data/raw/archive/Car parts dataset")
    process_supervisely_source("supervisely", supervisely_base, unified_data, state)

    # 3. Rust Detection COCO Sources
    rust_base = Path("data/raw/Roboflow/Rust Detection.v1i.coco")
    process_coco_source(
        "rust_train",
        rust_base / "train/_annotations.coco.json",
        rust_base / "train",
        unified_data,
        state,
        max_images=500,
    )
    process_coco_source(
        "rust_val",
        rust_base / "valid/_annotations.coco.json",
        rust_base / "valid",
        unified_data,
        state,
        max_images=100,
    )
    process_coco_source(
        "rust_test",
        rust_base / "test/_annotations.coco.json",
        rust_base / "test",
        unified_data,
        state,
        max_images=100,
    )

    # Export Unified COCO JSON
    with open(OUTPUT_COCO_JSON, "w") as f:
        json.dump(unified_data, f, indent=2)

    print("\n" + "=" * 80)
    print("[✔] SUCCESS: Staging complete!")
    print(f" ├─ Total Staged Images: {len(unified_data['images'])}")
    print(f" ├─ Total Staged Annotations: {len(unified_data['annotations'])}")
    print(f" ├─ Staged Image Directory: '{STAGING_IMG_DIR}'")
    print(f" └─ Unified COCO JSON File: '{OUTPUT_COCO_JSON}'")
    print("=" * 80)


if __name__ == "__main__":
    main()
