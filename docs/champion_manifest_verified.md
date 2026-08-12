# Champion Manifest Verification Results

Version: 0.1
Date: 2026-08-12
Status: Verified with known issues

## Active Repository

```text
REPO_ROOT:
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection

GIT_BRANCH:
stage_3

PHASE_0_COMMIT:
docs: add master plan, architecture, host detection, champion manifest, cleanup plan
```

## Ignored Repository

The following repository is abandoned and must not be used:

```text
/Users/macbook/Documents/ITC8/Internship/AI Farm/Testing/car_defect_detection
```

It was an early broken initialization and is excluded from all future phases.

---

## Stage 1 Champion — Verified

### Champion identity

```text
Stage: Stage 1
Task: Binary salient defect / anomaly pre-screening
Champion run name: Stage1_SOD_FocalLoss_Full
MLflow run ID: f3b8f26d4f5847d2bc57f453253af798
```

### Verified weights

```text
Weights path:
mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt

Absolute path:
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt

Exists: yes
Size: 27.51 MB
Last modified: Jul 20 14:01:39 2026
```

### Verified training arguments

Source:

```text
mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/args.yaml
```

Key parameters:

```text
task: semantic
model: yolo26m-sem.pt
data: data/processed/sod_tiled/sod_data_tiled.yaml
imgsz: 640
epochs: 50
batch: 32
optimizer: auto
lr0: 0.001
lrf: 0.01
weight_decay: 0.0005
seed: 0
deterministic: true
workers: 8
amp: true
device: null
resume: false
patience: 100
multi_scale: 0.0
close_mosaic: 10
pretrained: true
```

### Verified champion config

The true champion config is archived inside the MLflow run artifacts:

```text
mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/configs/stage1-sod.yaml
```

Key parameters:

```text
dataset.processed_dir: data/processed/sod_tiled
dataset.imgsz: 640
logging.experiment_name: Automated_Car_Defect_Stage1_SOD
logging.run_name: Stage1_SOD_FocalLoss_Full
training.backbone: yolo26m-sem.pt
training.epochs: 50
training.batch_size: 32
training.lr0: 0.001
training.weight_decay: 0.0005
training.loss_function: FocalCrossEntropyLoss
training.fl_gamma: 2.0
gating_thresholds.pixel_thresh_high: 0.28
gating_thresholds.pixel_thresh_low: 0.18
gating_thresholds.min_cc_area: 20
gating_thresholds.anomaly_thresh: 0.0005
gating_thresholds.near_miss_margin: 0.20
```

### Verified metrics

Source:

```text
mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/results.csv
```

Best/final metrics:

```text
Best metrics/mIoU: 0.84117 at epoch 50
Best metrics/pixel_acc: 0.92511 at epoch 50
Final train/ce_loss: 0.05122
Final train/dice_loss: 0.09209
Final val/ce_loss: 0.11278
Final val/dice_loss: 0.11858
```

### Stage 1 selection evidence

Candidate A was selected over Candidate B:

```text
Candidate A:
mlruns/1/f3b8f26d4f5847d2bc57f453253af798

Candidate B:
mlruns/1/ba4046a349434a88a5dcade830554f65
```

Comparison:

```text
mIoU:
A = 0.84117
B = 0.82683

pixel_acc:
A = 0.92511
B = 0.91721

val/ce_loss:
A = 0.11278
B = 0.23247
```

Candidate A wins on all major metrics and has the run name:

```text
Stage1_SOD_FocalLoss_Full
```

### Known Stage 1 issues

1. The current repo config is not the champion config:

```text
configs/train/stage1/stage1-sod.yaml
```

It reflects the nano/1024 variant:

```text
training.backbone: yolo26n-sem.pt
dataset.imgsz: 1024
training.batch_size: 16
logging.run_name: Stage1_SOD_FocalLoss_Full_nano_version
gating_thresholds.pixel_thresh_high: 0.47
gating_thresholds.pixel_thresh_low: 0.35
```

2. The true champion config is archived inside the MLflow run artifacts.

3. Focal loss is not visible in `args.yaml`. It was applied via Python patch and is documented in the archived config.

4. The Stage 1 dataset YAML currently contains a MacBook-only absolute path:

```text
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/sod_tiled
```

5. The champion was trained on a different host:

```text
/home/rith/secure_workspace/...
```

The saved `save_dir` also contains a doubled path:

```text
runs/semantic/runs/semantic/...
```

These are portability issues, not champion validity issues.

---

## Stage 2 Champion — Verified

### Champion identity

```text
Stage: Stage 2
Task: 7-class defect instance segmentation
Champion: Model 5 Stage 1 Extended, 7-class
Run name: stage1_head_warmup_7cls_extended
```

### Verified weights

```text
Relative path:
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt

Absolute path:
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt

Exists: yes
Size: 52.02 MB
Last modified: Aug 5 13:43:02 2026
```

### Verified results file

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/results.csv

Exists: yes
```

### Verified training config

Primary config:

```text
configs/train/stage2/model5_stage1_head_warmup_7cls_extended.yaml
```

Run args:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/args.yaml
```

Key parameters:

```text
model:
/home/lamacpp/Documents/car_defect_detection/model5_resume_adapt/model1_remapped_7class_init.pt

data:
/home/lamacpp/Documents/car_defect_detection/data/processed/yolo_seg_clean_2200_7cls/dataset.yaml

imgsz: 1024
epochs: 100
batch: 4
lr0: 0.005
lrf: 0.01
freeze: 23
patience: 30
multi_scale: false
mosaic: 0.0
mixup: 0.0
scale: 0.3
degrees: 15.0
perspective: 0.0005
fliplr: 0.5
erasing: 0.4
close_mosaic: 0
optimizer: SGD
seed: 42
deterministic: true
amp: true
fl_gamma: 2.0
fl_alpha: 0.50
fl_scale: 1.0
run_name: stage1_head_warmup_7cls_extended
```

### Known Stage 2 champion metrics

From final model report:

```text
Best validation Mask mAP50: 0.651
Best epoch: 78
Test Mask mAP50: 0.650
Test Mask mAP50-95: 0.494
Test Precision: 0.666
Test Recall: 0.635
```

### Known Stage 2 issues

1. The config references server-side paths:

```text
/home/lamacpp/Documents/car_defect_detection/...
```

2. The starting weights path is server-side:

```text
/home/lamacpp/Documents/car_defect_detection/model5_resume_adapt/model1_remapped_7class_init.pt
```

3. The dataset path is server-side:

```text
/home/lamacpp/Documents/car_defect_detection/data/processed/yolo_seg_clean_2200_7cls/dataset.yaml
```

These are portability issues, not champion validity issues.

---

## Stage 3 Champion — Verified

### Champion identity

```text
Stage: Stage 3
Task: 21-class panel/component segmentation
Champion: panel_segmenter_baseline
```

### Verified weights

```text
Relative path:
mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt

Absolute path:
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt

Exists: yes
Size: 52.02 MB
Last modified: Aug 12 02:19:17 2026
```

### Verified training config

```text
configs/train/stage3/panel_segmenter_baseline.yaml
```

Key parameters:

```text
model: yolo26m-seg.pt
data: data/processed/stage3/car_damages_panel/car_damages_panel.yaml
imgsz: 640
epochs: 100
batch: 8
lr0: 0.001
lrf: 0.01
freeze: 0
patience: 20
multi_scale: false
mosaic: 0.0
scale: 0.3
degrees: 10.0
fliplr: 0.5
optimizer: AdamW
differential_lr: false
task: segment
run_name: stage3_panel_segmenter_baseline
```

### Verified dataset config

```text
data/processed/stage3/car_damages_panel/car_damages_panel.yaml
```

Dataset split counts:

```text
train: 798 images / 798 labels
val: 100 images / 100 labels
test: 100 images / 100 labels
nc: 21
```

### Known Stage 3 metrics

From Stage 3 report:

```text
Val Mask mAP50: 0.885
Test Mask mAP50: 0.879
Val Mask mAP50-95: 0.630
Test Mask mAP50-95: 0.626
Generalization gap: -0.006
```

### Known Stage 3 issues

1. The Stage 3 dataset YAML contains a MacBook-only absolute path:

```text
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/stage3/car_damages_panel
```

This must be made portable before server training.

---

## Stage 4 Production Files — Verified

### Verified Stage 4 files

```text
src/stage4/spatial_context_mapper.py
Exists: yes
Size: 9.36 KB

src/stage4/batch_mapping_test.py
Exists: yes
Size: 5.59 KB

src/stage2/inference/sahi_inference.py
Exists: yes
Size: 5.69 KB

configs/inference/sahi_production.yaml
Exists: yes
Size: 1.93 KB
```

### Verified SAHI production config

```text
configs/inference/sahi_production.yaml
```

Key fields:

```text
preset: balanced
model_type: yolov8
sahi.slice_size: 1024
sahi.overlap_ratio: 0.15
nms.ios_threshold: 0.50
presets: balanced, safety, max_recall, calib
```

Class rules:

```text
classes 0-4:
conf 0.25
min_area 0

class 5 corrosion:
balanced: conf 0.15, min_area 30
safety: conf 0.10, min_area 30
max_recall: conf 0.05, min_area 30
calib: conf 0.05, min_area 30

class 6 disjoint_part:
balanced: conf 0.15, min_area 200
safety: conf 0.10, min_area 200
max_recall: conf 0.05, min_area 200
calib: conf 0.05, min_area 200
```

### Known Stage 4 issues

1. `model_type: yolov8` is technically mismatched with YOLO26m-seg weights.

2. `model_path` is not present in the SAHI config. It is supplied by calling code.

3. `device` is not present in the SAHI config. It is supplied by calling code.

These are integration/technical-debt issues, not blockers for champion verification.

---

## Cross-Champion Portability Issues

The following issues must be handled later during backend standardization and runtime configuration:

1. Stage 1 dataset YAML has a MacBook-only absolute path.

2. Stage 3 dataset YAML has a MacBook-only absolute path.

3. Stage 2 training config references server paths under:

```text
/home/lamacpp/Documents/car_defect_detection
```

4. Stage 1 champion was trained under:

```text
/home/rith/secure_workspace
```

5. Stage 1 current repo config does not match the champion config.

6. SAHI config does not declare model path or device.

These do not invalidate the champions. They must be resolved by the future runtime/config layer.
