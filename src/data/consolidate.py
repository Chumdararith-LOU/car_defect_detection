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


def collect_and_parse_pools(raw_data_dir, dataset_maps, target_classes):
    """Scans all source directories and pools instances based on mapped rules."""
    class_to_idx = {cls: idx for idx, cls in enumerate(target_classes)}

    split_pools = {
        "train": defaultdict(list),
        "val": defaultdict(list),
        "test": defaultdict(list),
    }
    print("[+] Scanning raw dataset directories and validating text mappings...")

    if not raw_data_dir.exists():
        raise FileNotFoundError(
            f"Source directory missing. Ensure data exists at: {raw_data_dir.resolve()}"
        )

    for dataset_name in os.listdir(raw_data_dir):
        dataset_path = raw_data_dir / dataset_name
        if not dataset_path.is_dir():
            continue

        if dataset_name not in dataset_maps:
            print(f"Skipping directory (No explicit translation rules): {dataset_name}")
            continue

        current_label_map = dataset_maps[dataset_name]

        # Normalize incoming validation variations cleanly into the MLOps pipeline
        for split in ["train", "valid", "val", "test"]:
            split_dir = dataset_path / split
            if not split_dir.exists() and split in ["valid", "val"]:
                # Cross-check naming variations dynamically
                alt_split = "val" if split == "valid" else "valid"
                split_dir = dataset_path / alt_split

            if not split_dir.exists():
                continue

            json_file = split_dir / "_annotations.coco.json"
            if not json_file.exists():
                continue

            with open(json_file, "r") as f:
                coco_data = json.load(f)

            categories = {
                cat["id"]: cat["name"] for cat in coco_data.get("categories", [])
            }
            images = {img["id"]: img for img in coco_data.get("images", [])}

            img_to_anns = defaultdict(list)
            for ann in coco_data.get("annotations", []):
                img_to_anns[ann["image_id"]].append(ann)

            # Direct the internal routing to match 'train', 'val', or 'test'
            yolo_split = "val" if split in ["valid", "val"] else split

            for img_id, anns in img_to_anns.items():
                img_info = images[img_id]
                src_img_path = split_dir / img_info["file_name"]
                if not src_img_path.exists():
                    continue

                yolo_lines = []
                detected_classes_in_image = set()

                for ann in anns:
                    raw_label = categories.get(ann["category_id"])
                    target_class = current_label_map.get(raw_label)

                    if not target_class:
                        continue

                    if "segmentation" not in ann or not ann["segmentation"]:
                        continue

                    class_idx = class_to_idx[target_class]
                    img_w, img_h = img_info["width"], img_info["height"]

                    for seg in ann["segmentation"]:
                        if len(seg) < 6:
                            continue
                        normalized_coords = []
                        for i in range(0, len(seg), 2):
                            nx = max(0.0, min(1.0, seg[i] / img_w))
                            ny = max(0.0, min(1.0, seg[i + 1] / img_h))
                            normalized_coords.append(f"{nx:.6f}")
                            normalized_coords.append(f"{ny:.6f}")

                        yolo_lines.append(f"{class_idx} " + " ".join(normalized_coords))
                        detected_classes_in_image.add(target_class)

                if yolo_lines:
                    primary_class = sorted(list(detected_classes_in_image))[0]
                    split_pools[yolo_split][primary_class].append(
                        {
                            "src_path": src_img_path,
                            "lines": yolo_lines,
                            "ext": os.path.splitext(img_info["file_name"])[1],
                        }
                    )
    return split_pools


def balance_and_write_dataset(split_pools, processed_dir, target_classes, limits):
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

            if yolo_split == "train" and len(img_list) > limits["max_images_train"]:
                img_list = img_list[: limits["max_images_train"]]
            elif yolo_split == "val" and len(img_list) > limits["max_images_val"]:
                img_list = img_list[: limits["max_images_val"]]
            elif yolo_split == "test" and len(img_list) > limits["max_images_test"]:
                img_list = img_list[: limits["max_images_test"]]

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

    # Extract configs into Path objects / variables
    raw_data_dir = Path(config["paths"]["raw_data_dir"])
    processed_dir = Path(config["paths"]["processed_dir"])
    target_classes = config["target_classes"]
    dataset_maps = config["dataset_maps"]
    limits = config["limits"]

    # Execute Pipeline
    clean_and_build_scaffolding(processed_dir)

    pools = collect_and_parse_pools(raw_data_dir, dataset_maps, target_classes)

    mask_stats, img_stats, total_images = balance_and_write_dataset(
        pools, processed_dir, target_classes, limits
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
