# Current State of Car Defect Detection Project

## Overview
This is a Stage 2 multi-class instance segmentation model retraining project focused on improving the model's performance on a 7-class defect detection task. The project is working toward beating the current champion model (Model 5: 65.0% test Mask mAP50, 49.4% mAP50-95, 66.6% precision, 63.5% recall).

## Key Components Identified

### 1. Dataset Sources
We have multiple data sources in `data/raw/`:
- **CarDD_release/CarDD_COCO/** - Official CarDD benchmark (2,816 train, 810 val, 374 test images with 6 defect classes)
- **Car defect 2000 new/** and **Car defect 2200/** - Near-duplicates with 10-class taxonomy
- **Roboflow/** - 6 Roboflow exports with various formatting issues
- **archive/** - 2 mask-based datasets (car damages and car parts)

### 2. Dataset Structure
The CarDD dataset follows COCO format:
- `data/raw/CarDD_release/CarDD_COCO/train2017/` - contains 2,816 jpg images 
- `data/raw/CarDD_release/CarDD_COCO/annotations/` - contains annotation files:
  - `instances_train2017.json` 
  - `instances_val2017.json`
  - `instances_test2017.json`
  - `image_info.xlsx`

### 3. Key Challenges
- **Dataset duplication** - Found that `Roboflow/car-damage-detection.v1i.coco` is identical to `CarDD_COCO/train2017`
- **Class taxonomy inconsistency** - Roboflow exports have messy category names (numeric/hash labels) that need resolution
- **Missing clean images** - No clean/undamaged car images in training set, leading to potential false positives
- **Weak classes** - Corrosion and disjoint_part remain near-zero performance despite taxonomy fix

## Important Constraints from AGENTS.md
- Training resolution must be 1024×1024 tiles (640px training destroyed thin defects)
- Default transfer strategy is frozen-backbone + extended head-only warmup, resuming from Model 1 backbone
- Mask-level NMS (Mask-IOS) required, not bounding-box NMS 
- 7-class unified taxonomy: `dent`, `scratch`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion`, `disjoint_part`
- Corrosion and disjoint_part are known weak classes

## Current Files & Structure
- `STAGE2_RETRAIN_BRIEF.md` - Detailed retraining brief with priority experiments
- `AGENTS.md` - Locked decisions and project scope
- `reports/dataset_raw.md` - Raw dataset analysis report
- `src/train/train.py` - Training script
- `src/eval/validate.py` - Evaluation script

## Next Steps
Based on the STAGE2_RETRAIN_BRIEF.md, the priority experiments to try are:
1. **Hard-negative injection** - Add clean/undamaged car images with empty annotation files 
2. **Class-balanced sampling** for corrosion/disjoint_part 
3. **Gradual/partial backbone unfreeze** - Unfreeze last 1-2 backbone stages
4. **Train on native-resolution tiles** directly
5. **Copy-paste augmentation** for corrosion

The project needs:
1. A DATASET_AUDIT.md file to document dataset sources and processing
2. Enhanced evaluation script to compute clean-image false-positive rate
3. Data pipeline scripts for taxonomy remap, deduplication, and negative-ratio injection
4. Training run logs for experiments with metrics and verdicts

Key technical debt to address:
- Dataset duplication not yet resolved (Roboflow/data consistency issues)
- No clean-image false-positive rate calculation implemented yet
- Missing proper evaluation protocol implementation
- Need to understand training configuration format (Yolo26-seg CLI format)