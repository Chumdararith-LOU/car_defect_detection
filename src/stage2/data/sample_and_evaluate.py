import random
import shutil
from pathlib import Path
import yaml


def calculate_polygon_area(coords):
    n = len(coords) // 2
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[2 * i] * coords[2 * j + 1] - coords[2 * j] * coords[2 * i + 1]
    return abs(area) / 2.0


def get_image_label_pairs(base_path):
    pairs = []
    base = Path(base_path)
    for img_path in base.rglob("*.*"):
        if img_path.suffix.lower() in [".jpg", ".png", ".jpeg"]:
            lbl_path = Path(str(img_path).replace("images", "labels")).with_suffix(
                ".txt"
            )
            if lbl_path.exists():
                pairs.append((img_path, lbl_path))
    return pairs


def stratified_sample(pairs, target_count, target_classes):
    """Samples images ensuring rare classes are prioritized."""
    # Ordered from most rare to most common
    rarity_order = [
        "corrosion",
        "crack",
        "glass_shatter",
        "missing_component",
        "broken_component",
        "scratch",
        "dent",
    ]

    grouped = {c: [] for c in rarity_order}

    # Group each image by the rarest class it contains
    for img, lbl in pairs:
        classes_in_img = set()
        with open(lbl, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes_in_img.add(target_classes[int(parts[0])])

        if classes_in_img:
            rarest = next(c for c in rarity_order if c in classes_in_img)
            grouped[rarest].append((img, lbl))

    selected = []
    random.seed(42)

    # Dynamically allocate the quota based on remaining images needed
    for i, cls in enumerate(rarity_order):
        random.shuffle(grouped[cls])
        available = len(grouped[cls])
        classes_left = len(rarity_order) - i
        quota = (target_count - len(selected)) // classes_left

        if available <= quota:
            selected.extend(grouped[cls])  # Take all available rare ones
        else:
            selected.extend(grouped[cls][:quota])  # Cap at quota for common ones

    return selected


def main():
    print("[⚙] Initializing Stratified 6K Sampling & Spatial Balance Check...")

    dir_prof = Path(
        "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/stage2"
    )
    dir_custom = Path(
        "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/stage2_custom"
    )
    dir_out = Path(
        "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/dataset_6k"
    )

    target_classes = [
        "dent",
        "scratch",
        "crack",
        "glass_shatter",
        "broken_component",
        "missing_component",
        "corrosion",
    ]

    pairs_prof = get_image_label_pairs(dir_prof)
    pairs_custom = get_image_label_pairs(dir_custom)

    print(f"    -> Found {len(pairs_prof)} images in stage2")
    print(f"    -> Found {len(pairs_custom)} images in stage2_custom")

    # Apply Stratified Sampling
    print("[+] Applying stratification logic to prioritize rare classes...")
    sample_prof = stratified_sample(pairs_prof, 3000, target_classes)
    sample_custom = stratified_sample(pairs_custom, 3000, target_classes)
    combined = sample_prof + sample_custom

    if dir_out.exists():
        shutil.rmtree(dir_out)
    (dir_out / "images").mkdir(parents=True)
    (dir_out / "labels").mkdir(parents=True)

    stats = {c: {"instances": 0, "total_area": 0.0} for c in target_classes}
    image_counts = {c: set() for c in target_classes}

    print(
        f"[⚙] Extracting {len(combined)} total images and calculating mask footprints..."
    )

    for i, (img, lbl) in enumerate(combined):
        new_name_base = f"sample_{i:06d}"
        new_img_path = dir_out / "images" / (new_name_base + img.suffix)
        new_lbl_path = dir_out / "labels" / (new_name_base + ".txt")

        shutil.copy(img, new_img_path)
        shutil.copy(lbl, new_lbl_path)

        with open(lbl, "r") as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue

                c_idx = int(parts[0])
                coords = list(map(float, parts[1:]))

                c_name = target_classes[c_idx]
                area_fraction = calculate_polygon_area(coords)

                stats[c_name]["instances"] += 1
                stats[c_name]["total_area"] += area_fraction
                image_counts[c_name].add(new_img_path.name)

    yaml_data = {
        "path": str(dir_out.resolve()),
        "train": "images",
        "val": "images",
        "names": {idx: name for idx, name in enumerate(target_classes)},
    }
    with open(dir_out / "data.yaml", "w") as f:
        yaml.safe_dump(yaml_data, f, default_flow_style=False)

    print("\n=======================================================================")
    print("  📊 SPATIAL BALANCE & INSTANCE DISTRIBUTION (STRATIFIED 6K)")
    print("=======================================================================")
    print(
        f"{'Class':<20} | {'Images Contained':<18} | {'Total Masks':<12} | {'Avg Mask Area'}"
    )
    print("-" * 80)

    for c in target_classes:
        imgs = len(image_counts[c])
        insts = stats[c]["instances"]
        tot_a = stats[c]["total_area"]
        avg_a_pct = (tot_a / insts * 100) if insts > 0 else 0.0

        print(f"{c:<20} | {imgs:<18} | {insts:<12} | {avg_a_pct:.2f}%")
    print("=======================================================================\n")


if __name__ == "__main__":
    main()
