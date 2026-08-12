# Champion Manifest

Version: 0.1
Date: 2026-08-12
Status: Draft for approval

## Purpose

This document freezes the current known-good models, configs, datasets, and inference rules before workspace standardization.

During cleanup, these artifacts must not be moved, renamed, deleted, or modified unless explicitly approved.

---

## 1. Stage 1 Champion — Binary SOD Pre-Screener

### Model identity

```text
Stage: Stage 1
Task: Binary salient defect / anomaly pre-screening
Champion variant: M3 — YOLO26m, 640 tiled, Focal Loss
```

### Known champion metrics

From Week 2 evaluation:

| Metric | Value |
|---|---:|
| Recall | 95.2% |
| False positive rate | 50% |
| mIoU | 43.8% |
| p95 latency | 33.8 ms |
| Memory footprint | 170.1 MB |

### Locked training/inference principles

```text
Input strategy:
    15% overlapping coarse tiling

Loss:
    Focal Loss, gamma = 2.0

Reason:
    Solves hairline-scratch blindness caused by Stride-8 receptive-field dilution.

Thresholding:
    Calibrated using leakage-free validation.
    Calibration images must not be used for final evaluation.
```

### Artifact status

```text
Weights path: TO_VERIFY
Config path: TO_VERIFY
MLflow run: TO_VERIFY
Dataset version: Dataset D / CarDD_SOD
```

### Action required

Before cleanup, locate and lock:

1. Stage 1 champion weights.
2. Stage 1 training config.
3. Stage 1 threshold config.
4. Stage 1 tiling config.
5. Stage 1 evaluation script or notebook.

---

## 2. Stage 2 Champion — 7-Class Defect Instance Segmentation

### Model identity

```text
Stage: Stage 2
Task: 7-class defect instance segmentation
Champion: Model 5 Stage 1 Extended, 7-class
Run name: stage1_head_warmup_7cls_extended
```

### Champion run folder

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended
```

### Champion weights

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt
```

### Starting weights

```text
model1_remapped_7class_init.pt
```

### Dataset

```text
Clean 7-class dataset
Approximately 2,200 images
```

### Final 7-class taxonomy

| Class ID | Class Name |
|---:|---|
| 0 | dent |
| 1 | scratch |
| 2 | crack |
| 3 | glass_shatter |
| 4 | broken_lamp |
| 5 | corrosion |
| 6 | disjoint_part |

### Champion metrics

| Metric | Value |
|---|---:|
| Best validation Mask mAP50 | 0.651 |
| Best epoch | 78 |
| Test Mask mAP50 | 0.650 |
| Test Mask mAP50-95 | 0.494 |
| Test Precision | 0.666 |
| Test Recall | 0.635 |

### Locked training configuration

| Parameter | Value |
|---|---|
| Image size | 1024 |
| Epochs configured | 100 |
| Best epoch | 78 |
| Batch size | 4 |
| Initial LR | 0.005 |
| Freeze | 23 |
| Multi-scale | False |
| Mosaic | 0.0 |
| Scale augmentation | 0.3 |
| Rotation augmentation | 15.0 |
| Patience | 30 |

### Locked inference rules

```text
Native resolution rule:
    Stage 2 must use 1024px native-resolution slicing.

SAHI:
    slice size: 1024
    overlap: 15%

NMS:
    Mask-IOS NMS
    IOS = intersection(mask_A, mask_B) / min(area(mask_A), area(mask_B))

Presets:
    Balanced
    Safety
    Max Recall
```

### Important conclusion

The Stage 2 champion uses:

```text
Frozen backbone + extended head-only warmup
```

It should not be replaced by full differential fine-tuning unless a future experiment clearly proves improvement.

---

## 3. Stage 3 Champion — Panel/Component Segmenter

### Model identity

```text
Stage: Stage 3
Task: 21-class panel/component segmentation
Champion: panel_segmenter_baseline
```

### Known weights location

Mac-side MLflow artifact:

```text
mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt
```

Server-side run folder:

```text
TO_VERIFY
```

### Dataset

```text
Car damages dataset converted to YOLO panel format
998 images
21 classes
Split: 798 train / 100 val / 100 test
Seed: 42
```

### Champion metrics

| Metric | Val | Test |
|---|---:|---:|
| Mask mAP50 | 0.885 | 0.879 |
| Mask mAP50-95 | 0.630 | 0.626 |
| Mask Precision | 0.882 | 0.885 |
| Mask Recall | 0.841 | 0.824 |

### Locked training configuration

| Parameter | Value |
|---|---|
| Starting weights | fresh `yolo26m-seg.pt` |
| Image size | 640 |
| Batch size | 8 |
| Optimizer | AdamW |
| Epochs | 100 |
| Patience | 20 |
| Freeze | 0 |
| Differential LR | false |
| Multi-scale | false |
| Mosaic | 0.0 |
| Scale augmentation | 0.3 |
| Degrees | 10.0 |
| fliplr | 0.5 |

### Locked dataset engineering rules

```text
Interior polygon holes:
    Subtracted using Shapely.
    Example: door window openings.

Filename sanitization:
    Spaces converted to underscores.
    Collision handling required.

Split level:
    Image-level split, not polygon-level.
```

---

## 4. Stage 4 Champion — Spatial Context Mapper

### Module identity

```text
Stage: Stage 4
Task: Fuse Stage 2 defects with Stage 3 panels
Module: src/stage4/spatial_context_mapper.py
Batch test: src/stage4/batch_mapping_test.py
```

### Locked inference dependencies

```text
Stage 2 SAHI inference:
    src/stage2/inference/sahi_inference.py

SAHI production config:
    configs/inference/sahi_production.yaml
```

### Locked math

Intersection over Defect:

```text
IoD(defect, panel) =
    area(defect ∩ panel)
    /
    area(defect)
```

Assignment threshold:

```text
theta_containment = 0.50
```

Fallback:

```text
If max IoD < 0.50:
    assign Boundary/Trim
```

Damage Severity Index:

```text
DSI (%) =
    area(defect)
    /
    area(assigned_panel)
    *
    100
```

### Locked operational defaults

```text
panel confidence default: 0.25
Boundary/Trim fallback: safe behavior, not a bug
Close-up domain gap: documented limitation
```

---

## 5. Frozen Production Pipeline

The current production pipeline is:

```text
Input image
    ↓
Stage 3 panel segmentation
    ↓
Stage 2 SAHI defect segmentation
    ↓
Stage 4 IoD/DSI fusion
    ↓
Factory Report JSON + overlays + crops
```

Future addition:

```text
Stage 1 binary anomaly rescue
```

This will be added after standardization and must not disturb the frozen Stage 2/3/4 champion behavior.

---

## 6. Cleanup Protection Rules

During workspace cleanup:

1. Do not delete champion run folders.
2. Do not rename champion weights.
3. Do not modify locked configs.
4. Do not move test datasets used for champion evaluation.
5. Do not archive MLflow artifacts unless a verified backup exists.
6. Do not change taxonomy mapping without approval.
7. Do not alter SAHI production config without approval.

---

## 7. Verification Tasks Before Major Cleanup

Before moving files, verify:

```text
Stage 1 champion weights path
Stage 1 threshold config path
Stage 2 champion weights checksum
Stage 2 config snapshot
Stage 3 server run folder
Stage 3 dataset YAML
Stage 4 SAHI config
MLflow artifact integrity
```

Suggested output:

```text
docs/champion_manifest_verified.md
```
```
