import shutil
import random
from pathlib import Path
from collections import defaultdict

SOURCE_DATASETS = []
for base_path in [Path("data/processed/stage2"), Path("data/processed/stage2_custom")]:
    for split in ["train", "val", "test"]:
        SOURCE_DATASETS.append(
            {
                "images": base_path / split / "images",
                "labels": base_path / split / "labels",
            }
        )

OUTPUT_DIR = Path("data/processed/golden_3000")
OUTPUT_IMG_DIR = OUTPUT_DIR / "images"
OUTPUT_LBL_DIR = OUTPUT_DIR / "labels"

# Target Sampling Quotas
QUOTAS = {
    "underrepresented": 600,  # crack, glass_shatter, broken_component, corrosion
    "boundary": 1200,  # dent, scratch
    "hard_complex": 800,  # Multi-defect (>3 instances) or micro-mixed
    "clean_negatives": 400,  # Internal clean images (shortfall backfilled)
}

random.seed(42)


def parse_label_file(label_path: Path):
    """
    Parses a YOLO format segmentation txt file.
    Strips class_id 5 (missing_component).
    Returns: list of dicts with class_id, num_points, and bbox_area.
    """
    if not label_path.exists() or label_path.stat().st_size == 0:
        return []

    instances = []
    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 3:
                continue
            class_id = int(parts[0])

            # FIX 1: Explicitly ignore class 5 (missing_component)
            if class_id == 5:
                continue

            coords = [float(x) for x in parts[1:]]
            num_points = len(coords) // 2

            xs = coords[0::2]
            ys = coords[1::2]
            if xs and ys:
                width = max(xs) - min(xs)
                height = max(ys) - min(ys)
                area = width * height
            else:
                area = 0.0

            instances.append(
                {"class_id": class_id, "num_points": num_points, "area": area}
            )
    return instances


def categorise_image(instances):
    """
    Categorises an image into golden priority buckets.
    Excludes images that are 100% untrainable micro-defects.
    """
    if not instances:
        return "clean_negatives"

    # FIX 2: Skip images where ALL instances are untrainable micro-defects (< 0.001)
    if all(inst["area"] < 0.001 for inst in instances):
        return "skip"

    class_ids = [inst["class_id"] for inst in instances]
    num_instances = len(instances)

    # Hard/complex: multiple defects or mixed micro + macro defects
    has_micro_defect = any(inst["area"] < 0.001 for inst in instances)
    if num_instances >= 3 or has_micro_defect or len(set(class_ids)) > 1:
        return "hard_complex"

    # Underrepresented classes: crack (2), glass_shatter (3), broken (4), corrosion (6)
    if any(cid in [2, 3, 4, 6] for cid in class_ids):
        return "underrepresented"

    # Boundary cases: dent (0), scratch (1)
    if any(cid in [0, 1] for cid in class_ids):
        return "boundary"

    return "boundary"


def extract_golden_subset():
    OUTPUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_LBL_DIR.mkdir(parents=True, exist_ok=True)

    bucket_pools = defaultdict(list)
    total_scanned = 0
    skipped_micro_count = 0

    print("🔍 Scanning source datasets across train, val, and test splits...")
    for source in SOURCE_DATASETS:
        img_dir = source["images"]
        lbl_dir = source["labels"]

        if not img_dir.exists():
            continue

        for img_path in img_dir.glob("*.[jJ][pP][gG]"):
            total_scanned += 1
            lbl_path = lbl_dir / f"{img_path.stem}.txt"

            instances = parse_label_file(lbl_path)
            bucket = categorise_image(instances)

            if bucket == "skip":
                skipped_micro_count += 1
                continue

            bucket_pools[bucket].append((img_path, lbl_path))

    print(f"\n📊 Total Scanned Images: {total_scanned}")
    print(f"  - Skipped (100% micro-defects): {skipped_micro_count}")
    for b_name, pool in bucket_pools.items():
        print(f"  - Available in '{b_name}': {len(pool)} images")

    # Sample images per bucket with dynamic backfilling
    selected_files = []
    deficits = 0

    print("\n🎲 Sampling images for Golden Subset...")
    for b_name, target_count in QUOTAS.items():
        pool = bucket_pools[b_name]
        available = len(pool)

        if available < target_count:
            take_count = available
            deficits += target_count - available
            print(
                f"  ⚠️ Only {available} available for '{b_name}' (Target: {target_count}). Taking all {available}."
            )
        else:
            take_count = target_count
            print(f"  ✓ Sampled {take_count}/{target_count} for '{b_name}'")

        sampled = random.sample(pool, take_count)
        selected_files.extend(sampled)
        bucket_pools[b_name] = [item for item in pool if item not in sampled]

    # Dynamic backfilling if clean_negatives or any bucket is short
    if deficits > 0:
        print(
            f"\n🔄 Backfilling deficit of {deficits} images from remaining candidate pools..."
        )
        remaining_pool = (
            bucket_pools["hard_complex"]
            + bucket_pools["boundary"]
            + bucket_pools["underrepresented"]
        )

        if len(remaining_pool) >= deficits:
            extra_samples = random.sample(remaining_pool, deficits)
            selected_files.extend(extra_samples)
            print(f"  ✅ Successfully backfilled {deficits} extra images!")
        else:
            selected_files.extend(remaining_pool)
            print(
                f"  ⚠️ Reached maximum available dataset size: {len(selected_files)} total images."
            )

    # Copy files and strip Class 5 annotations
    print(
        f"\n📁 Copying and cleaning {len(selected_files)} images to '{OUTPUT_DIR}'..."
    )
    copied_count = 0
    for img_path, lbl_path in selected_files:
        # Create unique filename incorporating source folder and split name
        split_name = img_path.parent.parent.name
        base_dataset = img_path.parent.parent.parent.name
        unique_prefix = f"{base_dataset}_{split_name}"

        dest_img_name = f"{unique_prefix}_{img_path.name}"
        dest_lbl_name = f"{unique_prefix}_{lbl_path.stem}.txt"

        shutil.copy2(img_path, OUTPUT_IMG_DIR / dest_img_name)

        # Write cleaned label file (stripping Class 5 lines)
        if lbl_path.exists():
            with open(lbl_path, "r", encoding="utf-8") as f_in:
                clean_lines = [
                    line
                    for line in f_in
                    if line.strip() and int(line.strip().split()[0]) != 5
                ]

            with open(OUTPUT_LBL_DIR / dest_lbl_name, "w", encoding="utf-8") as f_out:
                f_out.writelines(clean_lines)
        else:
            open(OUTPUT_LBL_DIR / dest_lbl_name, "w").close()

        copied_count += 1

    print(
        f"\n✅ Extraction Complete! {copied_count} cleaned images ready in '{OUTPUT_DIR}' for CVAT annotation."
    )


if __name__ == "__main__":
    extract_golden_subset()
