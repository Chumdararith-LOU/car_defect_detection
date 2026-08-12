# File 2: `docs/workspace_cleanup_plan.md`

```markdown
# Workspace Cleanup Plan

Version: 0.1
Date: 2026-08-12
Status: Draft for approval

## Purpose

The current workspace contains valuable research artifacts, but also many stale, duplicated, and non-standard files.

This plan defines how to clean the repository safely without destroying experiment history.

The rule is:

```text
Archive first.
Delete only after verification.
Never touch champion artifacts.
```

---

## 1. Cleanup Goals

The cleanup must achieve:

1. Protect champion models and configs.
2. Remove randomness from the active repository.
3. Archive old experiments safely.
4. Fix broken paths.
5. Fix dependency issues.
6. Remove hardcoded secrets.
7. Prepare the repository for the new backend/desktop app.
8. Create clear documentation.

---

## 2. Non-Goals

This cleanup does **not** yet:

1. Rewrite the training pipeline.
2. Build the desktop UI.
3. Refactor all Python modules.
4. Change model architectures.
5. Modify champion weights.
6. Modify Stage 2/3/4 evaluation logic.
7. Retrain any model.

---

## 3. Archive Strategy

Create:

```text
archive/
    pre_standardization/
        notebooks/
        configs/
        reports/
        legacy_scripts/
        legacy_import/
        misc/
```

Also create:

```text
archive/INVENTORY.md
```

Every moved file/folder should be listed in the inventory:

```text
original path
new archive path
reason for move
status:
    obsolete
    historical
    needs_review
    keep_archive_only
```

---

## 4. Known Cleanup Backlog

Based on the workspace report, these are the known issues.

### 4.1 Stale Makefile targets

Issue:

```text
Makefile references old paths:
    src/data/consolidate.py
    src/train/train.py
    src/eval/validate.py
    src/deploy/export.py
```

Actual code has moved to stage-specific folders.

Action:

```text
Mark legacy Makefile targets as deprecated.
Later replace Makefile with standardized CLI/backend commands.
```

Priority:

```text
Medium
```

---

### 4.2 Broken DVC pipeline

Issue:

```text
dvc.yaml references:
    src/data/prep_sod.py
    src/data/create_tiles.py

Actual locations:
    src/stage1/data/...
```

Action:

```text
Either fix DVC paths or temporarily disable DVC pipeline stages.
Do not block standardization on DVC if dataset manifests can replace it short-term.
```

Priority:

```text
Medium
```

---

### 4.3 Missing dependencies

Issue:

```text
Code imports shapely and sam2, but requirements.txt does not include them.
```

Action:

```text
Add shapely to requirements.
Decide whether sam2 is required for production.
If sam2 is only experimental, move it to optional requirements.
```

Priority:

```text
High
```

---

### 4.4 Hardcoded MinIO password

Issue:

```text
docker-compose.yml contains a hardcoded MinIO root password.
```

Action:

```text
Move secrets to .env.
Create .env.example.
Remove secret from tracked file if possible.
Rotate password if repository was shared.
```

Priority:

```text
High
```

---

### 4.5 Duplicate notebooks

Issue:

```text
Duplicate notebooks exist, such as:
    analyze_train_dataset.ipynb
    analyze_train_dataset (1).ipynb

Also:
    study_stage2_tiled_dataset duplicates
```

Action:

```text
Archive duplicates.
Keep only the most complete version in active workspace or docs/notebooks.
```

Priority:

```text
Low
```

---

### 4.6 Superseded Stage 2 configs

Issue:

```text
configs/train/stage2/ contains multiple old experiment configs.
Some are superseded by final 7-class champion configs.
```

Action:

```text
Move non-champion legacy configs to:
    archive/pre_standardization/configs/stage2/

Keep champion-related configs active.
```

Priority:

```text
Medium
```

---

### 4.7 Trailing-space report directories

Issue:

```text
Some report directories have trailing spaces in names.
This is fragile for shell tooling.
```

Action:

```text
Rename or archive with normalized names.
Replace spaces with underscores.
```

Priority:

```text
Low
```

---

### 4.8 Unused legacy Darknet import folder

Issue:

```text
yolo_import/ appears to be an unused Darknet-format stub.
```

Action:

```text
Archive to:
    archive/pre_standardization/legacy_import/yolo_import/
```

Priority:

```text
Low
```

---

### 4.9 Empty README

Issue:

```text
README.md is empty.
```

Action:

```text
Create a minimal production README.
```

README should contain:

```text
project overview
stage overview
repository layout
setup instructions
environment variables
how to run backend
how to run frontend
where champion models live
```

Priority:

```text
High
```

---

### 4.10 CI test path mismatch

Issue:

```text
CI runs:
    pytest src/tests/

But tests live in:
    tests/
```

Action:

```text
Update CI to:
    pytest tests/
```

Priority:

```text
High
```

---

### 4.11 Cross-stage coupling

Issue:

```text
Stage 3 imports from Stage 1:
    from stage1.utils.config_helpers import resolve_device
```

Action:

```text
Later create shared module:
    src/cardefect/common/

Move shared helpers there.
```

Priority:

```text
Medium
```

---

### 4.12 Empty `.env.example`

Issue:

```text
.env exists but .env.example is empty.
```

Action:

```text
Document required environment variables.
```

Example variables:

```text
MLFLOW_TRACKING_URI
DATA_YAML
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
CARDEFECT_API_BASE
CARDEFECT_MODEL_REGISTRY_PATH
```

Priority:

```text
High
```

---

## 5. Cleanup Phases

### Phase A — Freeze champions

Tasks:

```text
Create docs/champion_manifest.md
Verify champion paths
Do not touch champion artifacts
```

Exit condition:

```text
Champion models/configs are documented and protected.
```

---

### Phase B — Inventory workspace

Tasks:

```text
List top-level directories
List legacy configs
List duplicate notebooks
List report folders
List unused scripts
List broken paths
```

Exit condition:

```text
archive/INVENTORY.md is created.
```

---

### Phase C — Archive old artifacts

Tasks:

```text
Move duplicates to archive/
Move legacy configs to archive/
Move old reports to archive/
Move yolo_import to archive/
```

Exit condition:

```text
Active workspace contains only current-stage code/configs/docs.
```

---

### Phase D — Fix environment and secrets

Tasks:

```text
Update requirements.txt
Add .env.example
Move MinIO secret out of docker-compose.yml
Verify local install command
```

Exit condition:

```text
Environment setup is reproducible and secret-safe.
```

---

### Phase E — Fix broken tooling

Tasks:

```text
Fix CI test path
Fix or disable stale Makefile targets
Fix or disable broken DVC pipeline
Add minimal README
```

Exit condition:

```text
Basic repository tooling is not misleading.
```

---

### Phase F — Prepare for backend standardization

Tasks:

```text
Define future repo layout
Define backend module locations
Define common module
Define config schema location
Define model registry location
```

Exit condition:

```text
Repository is ready for FastAPI backend and host detection implementation.
```

---

## 6. Proposed Active Repository After Cleanup

After cleanup, the active repo should look more like:

```text
car_defect_detection/
│
├── docs/
│   ├── master_plan.md
│   ├── host_detection_spec.md
│   ├── champion_manifest.md
│   ├── workspace_cleanup_plan.md
│   └── architecture.md
│
├── configs/
│   ├── stage1/
│   ├── stage2/
│   ├── stage3/
│   ├── stage4/
│   ├── inference/
│   └── runtime/
│
├── src/
│   ├── stage1/
│   ├── stage2/
│   ├── stage3/
│   ├── stage4/
│   └── common/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── released/
│   └── manifests/
│
├── tests/
│
├── reports/
│
├── archive/
│   ├── INVENTORY.md
│   └── pre_standardization/
│
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── README.md
```

This is a target layout, not an immediate forced migration.

---

## 7. Safety Rules

During cleanup:

1. Do not delete champion model weights.
2. Do not delete champion configs.
3. Do not delete clean test datasets.
4. Do not delete MLflow artifacts.
5. Do not rename paths used by final reports.
6. Do not commit secrets.
7. Do not move large binary files without verifying backups.
8. Archive instead of delete whenever unsure.

---

## 8. Acceptance Criteria

Cleanup is complete when:

```text
Champion models are frozen and documented.
Old artifacts are archived with inventory.
No hardcoded secrets remain in tracked files.
Requirements include all required production dependencies.
CI test path is correct.
README explains the repository.
Stale Makefile/DVC targets are fixed or clearly disabled.
Workspace is ready for backend standardization.
```
```

---

# Next step after these documents

Once you approve these two documents, the next practical step is:

```text
Create archive inventory
```

Before moving anything, we should produce:

```text
archive/INVENTORY.md
```

But to do that safely, I need to know the exact repository root you want to clean.

Please tell me which workspace we are standardizing first:

1. **Main ML repo**: `car_defect_detection`
2. **Frontend app**: `Application React`
3. **Both**

If it is the main ML repo, please provide the repo path on your MacBook, or run:

```bash
pwd
```

inside the repo and paste the result.
