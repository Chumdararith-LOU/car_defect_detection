import os
import json
import shutil
import random
import argparse
from pathlib import Path
from collections import defaultdict
import yaml


def load_config(config_name):
    """Loads the YAML configuration file with smart path resolution."""
    config_path = Path(config_name)

    script_dir = Path(__file__).resolve().parent
    config_folder_path = script_dir / "config" / config_name

    script_folder_path = script_dir / config_name

    if config_path.exists():
        target_file = config_path
    elif config_folder_path.exists():
        target_file = config_folder_path
    elif script_folder_path.exists():
        target_file = script_folder_path
    else:
        raise FileNotFoundError(
            f"Could not find '{config_name}'.\n"
            f"Checked locations:\n"
            f" 1. {config_path.resolve()}\n"
            f" 2. {config_folder_path.resolve()}\n"
            f" 3. {script_folder_path.resolve()}"
        )

    with open(target_file, "r") as file:
        print(f"[ℹ] Loaded configuration from: {target_file.resolve()}")
        return yaml.safe_load(file)


def clean_and_build_scaffolding(processed_dir):
    """Clears obsolete data and creates structured YOLO segmentation folders."""
    if processed_dir.exists():
        print(f"[⚙] Clearing obsolete data build at: {processed_dir}")
        shutil.rmtree(processed_dir)

    print("[+] Creating structured YOLO segmentation folders...")
    for split in ["train", "val", "test"]:
        (processed_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (processed_dir / split / "labels").mkdir(parents=True, exist_ok=True)


def collect_and_parse_pools(coco_json_paths, class_mapping, config):
    """Scans explicitly defined COCO JSON files and pools instances based on mapping rules and filters."""
    split_pools = {
        "train": defaultdict(list),
        "val": defaultdict(list),
        "test": defaultdict(list),
    }
    print("[+] Parsing COCO JSON files from config and applying YAML filters...")

    # Global tracker for max_total_instances across all images
    global_instance_counts = defaultdict(int)

    for split, paths in coco_json_paths.items():
        if isinstance(paths, str):
            paths = [paths]

        for json_path_str in paths:
            json_file = Path(json_path_str)
            if not json_file.exists():
                print(f"[-] Missing JSON for {split}: {json_file}")
                continue

            # 1. Match the current JSON file to its specific dataset rules
            dataset_key = None
            for key in class_mapping.keys():
                if key in str(json_file):
                    dataset_key = key
                    break

            if not dataset_key:
                print(f"[-] No class mapping found for {json_file.name}. Skipping.")
                continue

            current_class_mapping = class_mapping[dataset_key]
            dataset_filters = config.get("filter_config", {}).get(dataset_key, {})
            all_rules = dataset_filters.get("__all__", {})

            split_dir = json_file.parent
            with open(json_file, "r") as f:
                coco_data = json.load(f)

            categories = {
                cat["id"]: cat["name"] for cat in coco_data.get("categories", [])
            }
            images = {img["id"]: img for img in coco_data.get("images", [])}

            img_to_anns = defaultdict(list)
            for ann in coco_data.get("annotations", []):
                img_to_anns[ann["image_id"]].append(ann)

            for img_id, anns in img_to_anns.items():
                img_info = images[img_id]
                src_img_path = split_dir / img_info["file_name"]

                if not src_img_path.exists():
                    fallback_dir = json_file.parent.parent / f"{split}2017"
                    src_img_path = fallback_dir / img_info["file_name"]

                if not src_img_path.exists():
                    continue

                yolo_lines = []
                detected_classes_in_image = set()

                # Image-level tracker for max_instances_per_image
                image_instance_counts = defaultdict(int)

                img_w, img_h = img_info["width"], img_info["height"]
                img_area = img_w * img_h

                for ann in anns:
                    raw_label = categories.get(ann["category_id"])

                    # 2. Fix: Check the nested mapping for this specific dataset
                    if raw_label not in current_class_mapping:
                        continue

                    class_idx = current_class_mapping[raw_label]
                    class_rules = dataset_filters.get(raw_label, {})

                    # --- FILTER: Area Limits ---
                    min_area_ratio = class_rules.get(
                        "min_area_ratio", all_rules.get("min_area_ratio", 0.0)
                    )
                    max_area_ratio = class_rules.get(
                        "max_area_ratio", all_rules.get("max_area_ratio", 1.0)
                    )

                    ann_area = ann.get("area")
                    if not ann_area and "bbox" in ann:
                        ann_area = ann["bbox"][2] * ann["bbox"][3]

                    area_ratio = ann_area / img_area if img_area and ann_area else 0.0

                    if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
                        continue  # Defect is too small or too large

                    # --- FILTER: Aspect Ratio Limits ---
                    max_aspect_ratio = class_rules.get(
                        "max_aspect_ratio",
                        all_rules.get("max_aspect_ratio", float("inf")),
                    )
                    if "bbox" in ann:
                        bw, bh = ann["bbox"][2], ann["bbox"][3]
                        if bw > 0 and bh > 0:
                            aspect_ratio = max(bw / bh, bh / bw)
                            if aspect_ratio > max_aspect_ratio:
                                continue  # Defect is too heavily skewed

                    # --- FILTER: Instance Caps ---
                    max_img_instances = class_rules.get(
                        "max_instances_per_image",
                        all_rules.get("max_instances_per_image", float("inf")),
                    )
                    max_total_instances = class_rules.get(
                        "max_total_instances",
                        all_rules.get("max_total_instances", float("inf")),
                    )

                    if image_instance_counts[raw_label] >= max_img_instances:
                        continue  # Image level cap reached

                    global_key = f"{dataset_key}_{raw_label}"
                    if global_instance_counts[global_key] >= max_total_instances:
                        continue  # Dataset global cap reached

                    # 3. Validated: Increment counters and extract coordinates
                    image_instance_counts[raw_label] += 1
                    global_instance_counts[global_key] += 1

                    segmentations = ann.get("segmentation", [])
                    if not segmentations or len(segmentations) == 0:
                        if "bbox" in ann:
                            bx, by, bw, bh = ann["bbox"]
                            segmentations = [
                                [bx, by, bx + bw, by, bx + bw, by + bh, bx, by + bh]
                            ]
                        else:
                            continue

                    min_points = config.get("min_polygon_points", 6)

                    for seg in segmentations:
                        if len(seg) < min_points:
                            continue
                        normalized_coords = []
                        for i in range(0, len(seg), 2):
                            nx = seg[i] / img_w
                            ny = seg[i + 1] / img_h
                            if config.get("clip_coordinates", True):
                                nx = max(0.0, min(1.0, nx))
                                ny = max(0.0, min(1.0, ny))
                            normalized_coords.append(f"{nx:.6f}")
                            normalized_coords.append(f"{ny:.6f}")

                        yolo_lines.append(f"{class_idx} " + " ".join(normalized_coords))

                        standard_class = config["target_classes"][class_idx]
                        detected_classes_in_image.add(standard_class)

                if yolo_lines:
                    primary_class = sorted(list(detected_classes_in_image))[0]
                    split_pools[split][primary_class].append(
                        {
                            "src_path": src_img_path,
                            "lines": yolo_lines,
                            "ext": os.path.splitext(img_info["file_name"])[1],
                        }
                    )
    return split_pools


def parse_supervisely_dataset(supervisely_paths, class_mapping, config, split_pools):
    """Scans Supervisely datasets, shuffles, and distributes 80/10/10 across pools."""
    import random

    print("[+] Parsing Supervisely JSON files with dynamic 80/10/10 split...")

    all_valid_items = []
    total_extracted_polygons = 0

    for _, dataset_root_str in supervisely_paths.items():
        dataset_root = Path(dataset_root_str)
        if not dataset_root.exists():
            print(f"[-] Missing Supervisely dataset: {dataset_root}")
            continue

        ann_files = [p for p in dataset_root.rglob("*.json") if p.parent.name == "ann"]
        print(
            f"    -> Found {len(ann_files)} annotation files in '{dataset_root.name}'"
        )

        for ann_file in ann_files:
            img_name = ann_file.name.replace(".json", "")
            img_dir = ann_file.parent.parent / "img"
            src_img_path = img_dir / img_name

            if not src_img_path.exists():
                base_name = Path(img_name).stem
                possible_images = list(img_dir.glob(f"{base_name}.*"))
                if possible_images:
                    src_img_path = possible_images[0]
                else:
                    continue

            with open(ann_file, "r") as f:
                ann_data = json.load(f)

            img_h, img_w = ann_data["size"]["height"], ann_data["size"]["width"]
            yolo_lines = []
            detected_classes_in_image = set()

            for obj in ann_data.get("objects", []):
                raw_label = obj.get("classTitle")

                if raw_label not in class_mapping:
                    continue

                class_idx = class_mapping[raw_label]
                geom_type = obj.get("geometryType")

                if geom_type != "polygon":
                    continue

                exterior = obj.get("points", {}).get("exterior", [])

                min_pairs = config.get("min_polygon_points", 6) / 2
                if len(exterior) < min_pairs:
                    continue

                normalized_coords = []
                for pt in exterior:
                    nx = pt[0] / img_w
                    ny = pt[1] / img_h
                    if config.get("clip_coordinates", True):
                        nx = max(0.0, min(1.0, nx))
                        ny = max(0.0, min(1.0, ny))
                    normalized_coords.append(f"{nx:.6f}")
                    normalized_coords.append(f"{ny:.6f}")

                yolo_lines.append(f"{class_idx} " + " ".join(normalized_coords))

                standard_class = config["target_classes"][class_idx]
                detected_classes_in_image.add(standard_class)
                total_extracted_polygons += 1

            if yolo_lines:
                primary_class = sorted(list(detected_classes_in_image))[0]
                all_valid_items.append(
                    {
                        "primary_class": primary_class,
                        "payload": {
                            "src_path": src_img_path,
                            "lines": yolo_lines,
                            "ext": src_img_path.suffix,
                        },
                    }
                )

    random.seed(42)
    random.shuffle(all_valid_items)

    total_images = len(all_valid_items)
    train_end = int(total_images * 0.8)
    val_end = int(total_images * 0.9)

    train_items = all_valid_items[:train_end]
    val_items = all_valid_items[train_end:val_end]
    test_items = all_valid_items[val_end:]

    for item in train_items:
        split_pools["train"][item["primary_class"]].append(item["payload"])
    for item in val_items:
        split_pools["val"][item["primary_class"]].append(item["payload"])
    for item in test_items:
        split_pools["test"][item["primary_class"]].append(item["payload"])

    print(f"    -> Successfully extracted {total_extracted_polygons} valid polygons.")
    print(
        f"    -> 80/10/10 Split Applied: {len(train_items)} Train | {len(val_items)} Val | {len(test_items)} Test"
    )


def balance_and_write_dataset(split_pools, processed_dir, target_classes):
    """Applies class balancing caps and saves assets sequentially."""
    print("\n[⚙] Enforcing image-level balancing rules & archiving files...")
    global_file_counter = 0
    final_mask_stats = defaultdict(int)
    split_img_stats = defaultdict(lambda: defaultdict(int))

    for yolo_split, classes_dict in split_pools.items():
        print(f"    » Compiling split: [{yolo_split}]")
        for target_class in target_classes:
            img_list = classes_dict[target_class]

            random.seed(42)
            random.shuffle(img_list)

            split_img_stats[yolo_split][target_class] += len(img_list)

            for item in img_list:
                global_file_counter += 1
                unique_img_name = f"car_defect_{global_file_counter:06d}{item['ext']}"
                unique_lbl_name = f"car_defect_{global_file_counter:06d}.txt"

                dest_img_path = processed_dir / yolo_split / "images" / unique_img_name
                dest_lbl_path = processed_dir / yolo_split / "labels" / unique_lbl_name

                shutil.copy(item["src_path"], dest_img_path)

                with open(dest_lbl_path, "w") as lf:
                    lf.write("\n".join(item["lines"]))

                for line in item["lines"]:
                    c_idx = int(line.split()[0])
                    final_mask_stats[target_classes[c_idx]] += 1

    return final_mask_stats, split_img_stats, global_file_counter


def generate_metadata_yaml(processed_dir, target_classes):
    """Generates the official data.yaml manifest for Ultralytics tracking engines."""
    yaml_data = {
        "path": str(processed_dir.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "names": {idx: name for idx, name in enumerate(target_classes)},
    }

    output_yaml = processed_dir / "data.yaml"
    with open(output_yaml, "w") as f:
        yaml.safe_dump(yaml_data, f, default_flow_style=False)
    print(f"\n[✓] Pipeline configuration written to: {output_yaml.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="YOLO Dataset Consolidation Pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration YAML file",
    )
    args = parser.parse_args()

    print("=====================================================")
    print("   INITIALIZING DATA CONSOLIDATION ROUTINE V3")
    print("=====================================================")

    # Load settings from config
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f" Error: {e}")
        return

    processed_dir = Path(config["output_processed_dir"])
    coco_json_paths = config.get("coco_json_paths", {})
    class_mapping = config["class_mapping"]

    target_classes = config["target_classes"]

    clean_and_build_scaffolding(processed_dir)

    pools = collect_and_parse_pools(coco_json_paths, class_mapping, config)

    supervisely_paths = config.get("supervisely_paths", {})
    if supervisely_paths:
        parse_supervisely_dataset(supervisely_paths, class_mapping, config, pools)

    mask_stats, img_stats, total_images = balance_and_write_dataset(
        pools, processed_dir, target_classes
    )

    generate_metadata_yaml(processed_dir, target_classes)

    print("\n======================================================================")
    print("  📊 MLOPS DATASET DISTRIBUTION TELEMETRY")
    print("======================================================================")
    print(f"Total Unique Images Processed: {total_images:,}\n")

    print("[IMAGE COUNT PER SPLIT]")
    splits = ["train", "val", "test"]
    for i, split in enumerate(splits):
        total_in_split = sum(img_stats[split].values())
        is_last_split = i == len(splits) - 1
        split_char = "└──" if is_last_split else "├──"

        print(f"{split_char} {split.upper()} Split ───────── {total_in_split:,} images")

        for j, cls in enumerate(target_classes):
            is_last_cls = j == len(target_classes) - 1
            branch_char = "    └─" if is_last_cls else "    ├─"
            pipe_char = " " if is_last_split else "│"

            print(f"{pipe_char} {branch_char} {cls:<10}: {img_stats[split][cls]:>7,}")

    print("\n[POLYGON MASK DENSITY (ALL SPLITS)]")
    for j, cls in enumerate(target_classes):
        is_last_cls = j == len(target_classes) - 1
        branch_char = "└──" if is_last_cls else "├──"
        print(f"{branch_char} {cls:<10}: {mask_stats[cls]:>7,} instances")
    print("======================================================================\n")


if __name__ == "__main__":
    main()
