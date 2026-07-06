# src/data/consolidate.py
import os
import json
import shutil
import random
from pathlib import Path
from collections import defaultdict
import yaml

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed/yolo_seg")

TARGET_CLASSES = ["scratch", "dent", "stain", "rust", "broken"]
CLASS_TO_IDX = {cls: idx for idx, cls in enumerate(TARGET_CLASSES)}

DATASET_MAPS = {
    "Car defect detection.v2i.coco": {
        "Scratch": "scratch", "Dent": "dent", "Glass-Break": "broken", "Accident": "broken", "car-defect": "broken"
    },
    "Car defect detection.v6i.coco": {
        "Scratch": "scratch", "Dent": "dent", "Glass-Break": "broken", "Accident": "broken", "car-defect": "broken"
    },
    "Rust Detection.v1i.coco": {
        "Rust": "rust", "rust": "rust", "copper corrosion": "rust", "corroded-part": "rust", 
        "corrosion": "rust", "iron rust": "rust", "mild-corrosion": "rust", "moderate-corrosion": "rust", 
        "severe-corrosion": "rust"
    },
    "crackbird detection 3.v6-v1.coco": {
        "Bird Drop": "stain", "Cracked": "broken"
    },
    "dd.v1i.coco": {
        "dent": "dent"
    },
    "scarcth_2.v9i.coco": {
        "scratch": "scratch", "scarcth-2": "scratch", "dent": "dent"
    },
    "socarC.v1i.coco": {
        "Scratched": "scratch", "Crushed": "dent", "Breakage": "broken", "Separated": "broken"
    },
    "YoloForCarDefect.v1i.coco": {
        "-": "dent", 
        "Roboflow is an end-to-end computer vision platform that helps you": "scratch", 
        "Car defect detection - v7 2024-04-12 10-29pm": "dent"
    }
}

MAX_IMAGES_PER_CLASS_TRAIN = 2000


def clean_and_build_scaffolding():
    """Wipes old data builds and creates uniform YOLOv8/26-seg directories."""
    if PROCESSED_DIR.exists():
        print(f"🧹 Clearing obsolete data build at: {PROCESSED_DIR}")
        shutil.rmtree(PROCESSED_DIR)
        
    print("📁 Creating structured YOLO segmentation folders...")
    for split in ['train', 'val', 'test']:
        (PROCESSED_DIR / split / 'images').mkdir(parents=True, exist_ok=True)
        (PROCESSED_DIR / split / 'labels').mkdir(parents=True, exist_ok=True)


def collect_and_parse_pools():
    """Scans all source directories and pools instances based on mapped rules."""
    split_pools = {
        'train': defaultdict(list),
        'val': defaultdict(list),
        'test': defaultdict(list)
    }

    print("🔍 Scanning raw dataset directories and validating text mappings...")
    
    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Source directory missing. Ensure data exists at: {RAW_DATA_DIR.resolve()}")

    for dataset_name in os.listdir(RAW_DATA_DIR):
        dataset_path = RAW_DATA_DIR / dataset_name
        if not dataset_path.is_dir():
            continue
            
        if dataset_name not in DATASET_MAPS:
            print(f"Skipping directory (No explicit translation rules): {dataset_name}")
            continue
            
        current_label_map = DATASET_MAPS[dataset_name]
        
        # Normalize incoming validation variations cleanly into the MLOps pipeline
        for split in ['train', 'valid', 'val', 'test']:
            split_dir = dataset_path / split
            if not split_dir.exists() and split in ['valid', 'val']:
                # Cross-check naming variations dynamically
                alt_split = 'val' if split == 'valid' else 'valid'
                split_dir = dataset_path / alt_split
                
            if not split_dir.exists():
                continue
                
            json_file = split_dir / '_annotations.coco.json'
            if not json_file.exists():
                continue
                
            with open(json_file, 'r') as f:
                coco_data = json.load(f)
                
            categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
            images = {img['id']: img for img in coco_data.get('images', [])}
            
            img_to_anns = defaultdict(list)
            for ann in coco_data.get('annotations', []):
                img_to_anns[ann['image_id']].append(ann)
                
            # Direct the internal routing to match 'train', 'val', or 'test'
            yolo_split = 'val' if split in ['valid', 'val'] else split
            
            for img_id, anns in img_to_anns.items():
                img_info = images[img_id]
                src_img_path = split_dir / img_info['file_name']
                if not src_img_path.exists():
                    continue
                    
                yolo_lines = []
                detected_classes_in_image = set()
                
                for ann in anns:
                    raw_label = categories.get(ann['category_id'])
                    target_class = current_label_map.get(raw_label)
                    
                    if not target_class:
                        continue
                        
                    if 'segmentation' not in ann or not ann['segmentation']:
                        continue
                        
                    class_idx = CLASS_TO_IDX[target_class]
                    img_w, img_h = img_info['width'], img_info['height']
                    
                    for seg in ann['segmentation']:
                        if len(seg) < 6: 
                            continue
                        normalized_coords = []
                        for i in range(0, len(seg), 2):
                            nx = max(0.0, min(1.0, seg[i] / img_w))
                            ny = max(0.0, min(1.0, seg[i+1] / img_h))
                            normalized_coords.append(f"{nx:.6f}")
                            normalized_coords.append(f"{ny:.6f}")
                        
                        yolo_lines.append(f"{class_idx} " + " ".join(normalized_coords))
                        detected_classes_in_image.add(target_class)
                
                if yolo_lines:
                    primary_class = sorted(list(detected_classes_in_image))[0]
                    split_pools[yolo_split][primary_class].append({
                        'src_path': src_img_path,
                        'lines': yolo_lines,
                        'ext': os.path.splitext(img_info['file_name'])[1]
                    })
    return split_pools


def balance_and_write_dataset(split_pools):
    """Applies class balancing caps and saves assets sequentially."""
    print("\nEnforcing image-level balancing rules & archiving files...")
    global_file_counter = 0
    final_mask_stats = defaultdict(int)

    for yolo_split, classes_dict in split_pools.items():
        print(f" └─ Compiling split: [{yolo_split}]")
        for target_class in TARGET_CLASSES:
            img_list = classes_dict[target_class]
            
            # Enforce determinism during random shuffling
            random.seed(42)
            random.shuffle(img_list)
            
            if yolo_split == 'train' and len(img_list) > MAX_IMAGES_PER_CLASS_TRAIN:
                img_list = img_list[:MAX_IMAGES_PER_CLASS_TRAIN]
                
            for item in img_list:
                global_file_counter += 1
                unique_img_name = f"car_defect_{global_file_counter:06d}{item['ext']}"
                unique_lbl_name = f"car_defect_{global_file_counter:06d}.txt"
                
                dest_img_path = PROCESSED_DIR / yolo_split / 'images' / unique_img_name
                dest_lbl_path = PROCESSED_DIR / yolo_split / 'labels' / unique_lbl_name
                
                # Execute file copy operations cleanly using path objects
                shutil.copy(item['src_path'], dest_img_path)
                
                with open(dest_lbl_path, 'w') as lf:
                    lf.write("\n".join(item['lines']))
                
                for line in item['lines']:
                    c_idx = int(line.split()[0])
                    final_mask_stats[TARGET_CLASSES[c_idx]] += 1
                    
    return final_mask_stats


def generate_metadata_yaml():
    """Generates the official data.yaml manifest for Ultralytics tracking engines."""
    yaml_data = {
        'path': str(PROCESSED_DIR.resolve()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'names': {idx: name for idx, name in enumerate(TARGET_CLASSES)}
    }
    
    output_yaml = PROCESSED_DIR / "data.yaml"
    with open(output_yaml, 'w') as f:
        yaml.safe_dump(yaml_data, f, default_flow_style=False)
    print(f"Pipeline configuration written to: {output_yaml.resolve()}")


def main():
    print("=====================================================")
    print("🛡️  INITIALIZING DATA CONSOLIDATION ROUTINE V2")
    print("=====================================================")
    
    clean_and_build_scaffolding()
    pools = collect_and_parse_pools()
    stats = balance_and_write_dataset(pools)
    generate_metadata_yaml()
    
    print("\n=============================================")
    print("📊 CUSTOM RULE CONSOLIDATION COMPLETE")
    for cls in TARGET_CLASSES:
        print(f" ├─ {cls}: {stats[cls]} polygon masks written")
    print("=============================================\n")


if __name__ == "__main__":
    main()