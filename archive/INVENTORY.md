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
