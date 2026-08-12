# Workspace Archive Inventory

Version: 0.1
Date: 2026-08-12
Status: In progress

## Purpose

This directory contains files archived from the active workspace during the Phase 3 cleanup.

Rule:

```text
Archive first.
Delete only after explicit approval.
Never touch champion artifacts.
```

## Archive Categories

```text
archive/pre_standardization/notebooks/
    Duplicate and exploratory Jupyter notebooks.

archive/pre_standardization/configs/
    Superseded or legacy experiment configs.

archive/pre_standardization/reports/
    Old report folders and stale outputs.

archive/pre_standardization/legacy_scripts/
    Old shell scripts and standalone scripts.

archive/pre_standardization/legacy_import/
    Unused Darknet/import stubs.

archive/pre_standardization/misc/
    Other archived items.
```

## Archived Items

| Original Path | Archive Path | Reason | Status |
|---|---|---|---|
| yolo_import/ | archive/pre_standardization/legacy_import/yolo_import/ | Unused Darknet-format import stub; no connection to any champion model | Archived |
| src/Diagnost/analyze_train_dataset (1).ipynb | archive/pre_standardization/notebooks/analyze_train_dataset (1).ipynb | Duplicate notebook (copy with "(1)" suffix) | Archived |
| src/Diagnost/study_stage2_tiled_dataset (1).ipynb | archive/pre_standardization/notebooks/study_stage2_tiled_dataset (1).ipynb | Duplicate notebook (copy with "(1)" suffix) | Archived |
| src/Diagnost/study_stage2_tiled_dataset (1).pdf | archive/pre_standardization/notebooks/study_stage2_tiled_dataset (1).pdf | Duplicate notebook (copy with "(1)" suffix) | Archived |
| configs/train/stage2/Stage2-training.yaml | archive/pre_standardization/configs/stage2/Stage2-training.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model4_control_no_multiscale.yaml | archive/pre_standardization/configs/stage2/model4_control_no_multiscale.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model4_control_no_multiscale_7cls.yaml | archive/pre_standardization/configs/stage2/model4_control_no_multiscale_7cls.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model4_control_no_multiscale_7cls_unfreeze.yaml | archive/pre_standardization/configs/stage2/model4_control_no_multiscale_7cls_unfreeze.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model5_stage1_head_warmup.yaml | archive/pre_standardization/configs/stage2/model5_stage1_head_warmup.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model5_stage1_head_warmup_7cls.yaml | archive/pre_standardization/configs/stage2/model5_stage1_head_warmup_7cls.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model5_stage2_differential.yaml | archive/pre_standardization/configs/stage2/model5_stage2_differential.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
| configs/train/stage2/model5_stage2_differential_7cls.yaml | archive/pre_standardization/configs/stage2/model5_stage2_differential_7cls.yaml | Superseded Stage 2 experiment config (champion is model5_stage1_head_warmup_7cls_extended.yaml) | Archived |
