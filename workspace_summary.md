# Workspace Summary — Car Defect Detection (Stage 2 Retrain)

## Project Overview

This repository implements an automated car exterior defect detection pipeline.
The current workstream is **Stage 2 retraining only**: a multi-class instance
segmentation model over the locked 7-class taxonomy
(`dent`, `scratch`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion`,
`disjoint_part`). The goal is to beat the current champion (Model 5: 65.0%
test Mask mAP50) while closing the corrosion/disjoint_part gap and reducing
clean-image false positives. Stage 1 (binary pre-screener) and Stage 3
(panel/component segmentation) are out of scope.

Key locked decisions (see `AGENTS.md`):

- Training and SAHI inference resolution must match at 1024×1024.
- Default transfer strategy: frozen-backbone + extended head-only warmup,
  resuming from the Model 1 backbone.
- Mask-level NMS (Mask-IOS) for merging SAHI patch predictions.
- No clean-car images exist in the training set yet (hard-negative injection
  is the highest-priority improvement this round).

---

## Root Directory

### Documentation & Planning

| Path | Description |
|------|-------------|
| `AGENTS.md` | Auto-loaded agent instructions: project scope, locked decisions, data-source manifest facts, conventions, and evaluation requirements for the "best possible" Stage 2 model. |
| `Proposal.md` | Original internship project proposal (AI Farm Robotics / ITC): executive summary, objectives, timeline for the automated visual inspection system. |
| `README.md` | Project README (currently empty). |
| `RESEARCH_LITERATURE.md` | Published-paper backing for each candidate improvement in the brief, cross-referenced by section letter (A–G). |
| `STAGE2_RETRAIN_BRIEF.md` | Input brief for the retraining round: goal definition, prioritized experiments (hard-negative injection, class-balanced sampling, gradual unfreeze, etc.), clean-image sources, and deliverables. |
| `STAGE2_RETRAIN_PLAN.md` | Implementation plan derived from the brief: phased tasks (data pipeline, evaluation metrics, hard-negative injection, class-balanced sampling) and required new metrics. |
| `current_status_summary.md` | Snapshot of current progress and known technical debt (missing clean-image FP-rate metric, dedup status, evaluation protocol gaps). |
| `workspace_summary.md` | This file — workspace and file inventory. |

### Build / Run / Ops

| Path | Description |
|------|-------------|
| `Makefile` | Developer entry points: `setup` (pip installs), `data-consolidate` (runs `src/data/consolidate.py` with `configs/data/Experiment_v1.yaml`), `train` (runs `src/train/train.py` with MLflow), plus clean/eval targets. Loads `.env`. |
| `Dockerfile` | Container image definition for the training/MLOps environment. |
| `docker-compose.yml` | Compose services (e.g., local MLflow tracking server) supporting the pipeline. |
| `dvc.yaml` | DVC pipeline stage definitions (data consolidation → model training), tracking deps/outs such as `data/processed/yolo_seg/` and `artifacts/models/`. |
| `dvc.lock` | Locked hashes/outputs for the DVC pipeline stages. |
| `requirements.txt` | Runtime dependencies (ultralytics/YOLO stack, mlflow, pyyaml, python-dotenv, numpy, pandas, matplotlib, seaborn, tqdm, etc.). |
| `requirements-dev.txt` | Dev dependencies: pytest, pytest-cov, black, flake8, isort, mypy, mkdocs, jupyter. |
| `.env` | Local environment variables (e.g., `MLFLOW_URI`) — not committed. |
| `.env.example` | Empty template for `.env`. |
| `.gitignore` | Ignores for data artifacts, model weights, logs, env files. |
| `.gitattributes` | Git attributes (LFS/binary handling hints for data files). |
| `.dvcignore` | Paths excluded from DVC tracking. |
| `opencode.json` | opencode (agent CLI) configuration for this repo. |
| `skills-lock.json` | Lockfile of installed agent skills. |

---

## `src/` — Source Code

| Path | Description |
|------|-------------|
| `src/data/unify_and_deduplicate.py` | **Phase 1 data pipeline.** Scans raw COCO datasets (CarDD_COCO, Car defect 2000/2200, Roboflow exports), maps all class names onto the 7-class taxonomy, drops unmapped classes (e.g. `tire flat`, `object`, `0`–`5`), deduplicates images by MD5 keeping the copy with the most annotations, and writes `data/processed/annotations/{train,val,test}.json` plus symlinked image dirs under `data/processed/images/`. Excludes the known duplicate `car-damage-detection.v1i.coco`. |
| `src/data/consolidate.py` | Older consolidation script: converts COCO sources into a balanced YOLO-seg layout (`data/processed/yolo_seg/`) driven by `configs/data/Experiment_v1.yaml` (class caps, per-dataset label maps), and writes `data.yaml`. |
| `src/train/train.py` | Training launcher: loads a YAML config from `configs/train/`, starts an MLflow run, and trains an Ultralytics YOLO seg model, archiving weights per project/run. |
| `src/eval/validate.py` | Evaluation/reporting: pulls metrics from MLflow for a run, sets up `reports/figures/<run>` directories, and renders a markdown report via the Jinja2 template. |
| `src/deploy/export.py` | Deployment export: loads a `.pt` model and exports to configured formats (with optional int8 + calibration data), registering each export in MLflow. |
| `src/tests/test_data.py` | Pytest sanity checks on the processed YOLO dataset: split scaffolding exists and polygon label coordinates are within [0, 1]. Skips if `data.yaml` hasn't been generated. |
| `src/inspect_datasets.ipynb` | Exploratory notebook used to inspect/audit raw datasets (class counts, splits, samples). |

---

## `configs/` — YAML Configurations

| Path | Description |
|------|-------------|
| `configs/data/Experiment_v1.yaml` | Dataset consolidation config for `consolidate.py`: paths, per-split image limits (2000/250/250), target classes, and per-Roboflow-export label maps. Note: predates the 7-class taxonomy (uses scratch/dent/stain/rust/broken). |
| `configs/train/yolo26n-seg.yaml` | Training run config for the YOLO26 nano seg model (hyperparameters, dataset path, run naming). |
| `configs/train/yolo26s-seg.yaml` | Training run config for the YOLO26 small seg model. |
| `configs/quant/export_config.yaml` | Export/deployment config consumed by `src/deploy/export.py`: model path, deployment target formats, int8 settings, calibration data. |

---

## `data/` — Datasets

| Path | Description |
|------|-------------|
| `data/raw/` | Raw source datasets (not fully committed; ~large): `CarDD_release/CarDD_COCO` (official train/val/test, 6 classes), `Car defect 2000 new` and `Car defect 2200` (near-duplicate 10-class exports), `Roboflow/` exports (Rust Detection, crack_v2, socarC, car defect, Car Defect Detection, and the excluded duplicate `car-damage-detection.v1i.coco`), `archive/` (Car damages dataset = 21 panel classes → Stage 3; Car parts dataset = 8 damage classes → Stage 2). |
| `data/raw/DATASET_AUDIT.md` | Raw-dataset audit: duplicates, class-name issues, missing clean images, and the proposed 7-class mapping table. |
| `data/processed/unified_annotations.json` | Legacy output of the old unify script (known-broken: 279k annotations but 0 images). Superseded by the new `train/val/test.json` outputs. |

---

## `output/` — Pipeline Artifacts

| Path | Description |
|------|-------------|
| `output/test_data/{train,val,test,unified_annotations}.json` | COCO JSON outputs from test runs of the unify/deduplicate script. |
| `output/test_images/` | Image outputs produced by test runs. |

---

## `reports/` — Reporting

| Path | Description |
|------|-------------|
| `reports/dataset_raw.md` | Detailed raw-dataset report: per-source image/annotation counts, formats, licenses (~71,500 total images incl. overlaps). |
| `reports/templates/experiment_report.md.j2` | Jinja2 markdown template rendered by `src/eval/validate.py` into per-run experiment reports. |

---

## Tooling & CI

| Path | Description |
|------|-------------|
| `.github/workflows/ci.yml` | GitHub Actions CI ("MLOps Lite"): runs lint/quality and pytest on push/PR to `main`. |
| `.pre-commit-config.yaml` | Pre-commit hooks: YAML validation, end-of-file/trailing-whitespace fixes, black formatting. |
| `.agents/skills/` | Local agent skills installed for this repo (fine-tuning-expert, ml-pipeline, test-master, debugging-wizard). |
| `.dvc/` | DVC local configuration/cache. |
