# WORKSPACE_REPORT — car_defect_detection

## Overview

Multi-stage AI pipeline for automotive exterior defect detection and industrial quality inspection. Stage 1 is a binary/semantic pre-screening model (SOD), Stage 2 is a 7-class defect instance segmentation model (completed), Stage 3 is a panel/component segmentation model (M_panel, 21 classes, currently in progress), and Stage 4 maps detected defects to vehicle panels using Intersection-over-Defect (IoD) and computes Damage Severity Index (DSI). Development happens on macOS; training runs on an Ubuntu server (RTX 4090) at `/home/lamacpp/Documents/car_defect_detection`.

## Tech Stack & Dependencies

**Core (requirements.txt):** ultralytics (YOLO), torch >= 2.4, torchvision, opencv-python-headless, mlflow, dvc[s3], onnx, onnxruntime, pyyaml, python-dotenv, numpy, pandas, matplotlib, seaborn, tqdm.

**Dev (requirements-dev.txt):** pytest, pytest-cov, pre-commit, yamllint, black, flake8, isort, mypy, mkdocs + mkdocs-material, jupyter.

**Implicit/undeclared deps used in code:** shapely (stage4 spatial mapper), sahi/sam2 (run_sam2_full_dataset.py), PIL.

**Infra:** Python 3.10 (Dockerfile/CI), Docker Compose (MLflow server + MinIO S3), DVC for data versioning, MLflow for experiment tracking, GitHub Actions CI (flake8 + pytest), pre-commit hooks (black, flake8, isort, yaml lint, DVC status).

**Note:** `sam2` and `shapely` are imported in scripts but absent from requirements.txt.

## Directory Tree

```
.
├── AGENTS.md                          # agent workflow rules
├── Dockerfile
├── Makefile                           # main task runner (setup, train, eval, stage3)
├── Proposal.md
├── README.md                          # empty
├── dvc.yaml / dvc.lock                # DVC pipeline stages (stage1 only)
├── opencode.json
├── requirements.txt / requirements-dev.txt
├── run_full_benchmark_matrix.sh
├── run_sam2_full_dataset.py
├── run_server_matrix.sh
├── run_test_evaluation.sh
├── yolo11n-seg.pt                     # weights at repo root (gitignored)
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── artifacts/
│   ├── models/{rt-detr, yolo26s-seg}/
│   ├── ncnn/{benchmarks, bin, param}/
│   ├── onnx/{fp16, fp32, int8}/
│   └── tensorrt/{benchmarks, engine}/
├── configs/
│   ├── data/stage1/{Experiment_v1.yaml, val_splits.yaml}
│   ├── data/stage2/{stage2_combined, stage2_custom_only, stage2_prof_only}.yaml
│   ├── inference/sahi_production.yaml
│   ├── quant/export_config.yaml
│   ├── train/stage1/stage1-sod.yaml
│   ├── train/stage2/ (9 experiment configs)
│   ├── train/stage3/{panel_segmenter_baseline, panel_segmenter_baseline_nano, panel_segmenter_local_smoke}.yaml
│   ├── matrix_test.yaml
│   └── pipeline_config.yaml
├── data/
│   ├── raw/                           # CarDD_release, Roboflow, archives (read-only, DVC-tracked)
│   ├── processed/                     # sod, sod_tiled, stage2, stage3, yolo_seg_clean_2200_7cls, ...
│   ├── calibration/
│   ├── results/stage3/test_predictions/
│   └── raw.dvc / calibration.dvc
├── docs/                              # Jupyter Book config + stage3 server runbook
├── notebooks/report_experiment_inventory.ipynb
├── reports/                           # CSVs, stage2 results, stage4 batch outputs, templates
├── runs/                              # ultralytics training outputs (gitignored)
├── mlruns/ + mlflow.db                # MLflow tracking store
├── src/
│   ├── Diagnost/                      # EDA/inspection notebooks + PDFs
│   ├── stage1/{data, deploy, diagnostics, eval, inference, tests, train, utils}/
│   ├── stage2/{Resume-and-Adapt, annotation, data, eval, inference, train}/
│   ├── stage3/{data, eval, inference, train}/
│   └── stage4/
├── tests/{__init__.py, smoke_test_focal.py, test_data.py}
└── yolo_import/{obj.data, obj.names?, obj_train_data/, train.txt}
```

## Folder-by-Folder Breakdown

| Folder | Purpose |
|---|---|
| `src/stage1/` | Stage 1 binary/semantic pre-screening: SOD data prep, tiling, training (focal loss), benchmarking, export (ONNX/TensorRT), inference router |
| `src/stage2/` | Stage 2 defect segmentation: Resume-and-Adapt transfer learning scripts, CVAT annotation prep, SAHI inference, training |
| `src/stage3/` | Stage 3 panel segmentation: raw-to-YOLO converter, dataset YAML resolver, custom trainer with MLflow |
| `src/stage4/` | Panel-defect spatial mapping: IoD-based assignment, DSI calculation, batch stress-test harness |
| `src/Diagnost/` | Exploratory notebooks: dataset inspection, polygon checks, EDA (mostly gitignored) |
| `configs/train/stage1-3/` | Per-experiment YAML configs (model preset, hyperparams, augmentations) |
| `configs/data/` | Dataset split YAML for each stage |
| `configs/inference/` | SAHI production inference config |
| `configs/quant/` | ONNX/TensorRT export + quantization config |
| `artifacts/` | Exported models (ONNX fp16/fp32/int8, TensorRT engines, NCNN) |
| `data/raw/` | Read-only source datasets (DVC-tracked) |
| `data/processed/` | Generated training datasets per stage (gitignored) |
| `reports/` | Experiment results CSVs, stage4 JSON reports + overlay PNGs |
| `docs/` | Jupyter Book scaffolding + server runbooks for Stage 3 |
| `tests/` | Dataset schema validation tests (env-var driven) |
| `yolo_import/` | Legacy Darknet-format import stub (obj.data, train.txt) |
| `notebooks/` | Experiment inventory reporting |
| `mlruns/`, `mlflow.db`, `minio_data/` | Local experiment tracking / artifact storage |

## Key Files & Entry Points

| File | Description |
|---|---|
| `Makefile` | Primary orchestrator: `setup`, `train`, `eval`, `export`, `start-mlflow`, and full Stage 3 workflow (`stage3-local-smoke`, `stage3-server-one-shot`) |
| `src/stage1/train/train.py` | Stage 1 generic trainer |
| `src/stage1/train/train_sod.py` | Stage 1 SOD semantic segmentation trainer |
| `src/stage2/train/train.py` | Stage 2 defect segmentation trainer |
| `src/stage2/Resume-and-Adapt/stage1_head_warmup.py` | Head-only warmup transfer (Stage 2 champion strategy) |
| `src/stage2/inference/sahi_inference.py` | SAHI sliced inference module (reused by stage4) |
| `src/stage3/train/train.py` | Stage 3 panel segmenter trainer (custom SegmentationTrainer, focal loss option, MLflow) |
| `src/stage3/data/convert_car_damages_to_yolo.py` | Converts Car damages dataset to Stage 3 YOLO panel format (seed 42 split) |
| `src/stage3/data/resolve_dataset_yaml.py` | Rewrites dataset YAML paths for server portability |
| `src/stage4/spatial_context_mapper.py` | Maps defects to panels via IoD (theta=0.50), computes DSI, emits JSON factory report |
| `src/stage4/batch_mapping_test.py` | Batch stress-test harness for the spatial mapper |
| `configs/train/stage3/panel_segmenter_baseline.yaml` | Stage 3 baseline config (yolo26m-seg, 100 epochs, AdamW, mild aug) |
| `run_sam2_full_dataset.py` | SAM2-based annotation refinement for CVAT dataset |
| `run_test_evaluation.sh` / `run_server_matrix.sh` / `run_full_benchmark_matrix.sh` | Stage 1 model evaluation shells |
| `dvc.yaml` | DVC pipeline: prep_sod_data → tile_data → train → evaluate (stage1) |
| `tests/test_data.py` | Pytest dataset structure validator (requires `DATA_YAML` env var) |

## Observations for Refactoring

### Secrets & Environment
- `.env` exists (gitignored) but `.env.example` is **empty** — no documented env vars.
- `docker-compose.yml` contains a **hardcoded MinIO root password** (`secure_vault_password_2026`). Should move to `.env` / secrets manager.
- `run_sam2_full_dataset.py:20` has a **hardcoded MacBook absolute path** to a SAM2 checkpoint.

### Structure / Duplication
- `Makefile` references `src/data/consolidate.py`, `src/train/train.py`, `src/eval/validate.py`, `src/deploy/export.py` — these paths no longer exist (code moved to `src/stage1/...`). Legacy targets (`train`, `eval`, `export`, `data-consolidate`, `train-sod`) are stale.
- `dvc.yaml` references `src/data/prep_sod.py` and `src/data/create_tiles.py` — actually at `src/stage1/data/`. DVC pipeline is broken.
- `configs/train/stage2/` has 9 configs; several appear superseded (e.g., non-7cls variants of model4/model5). Candidates for archival.
- `src/Diagnost/` has duplicate notebooks (`analyze_train_dataset.ipynb` vs `analyze_train_dataset (1).ipynb`, same for `study_stage2_tiled_dataset`).
- `yolo_seg_clean_2200_` (trailing underscore) alongside `yolo_seg_clean_2200_7cls` in data/processed looks like a leftover/partial directory.
- `yolo_import/` appears to be an unused Darknet-format stub.
- `reports/stage2/` contains directories with **trailing spaces** in names (`yolo26m_1024_stage2_baseline `), which is fragile for shell tooling.

### Missing / Inconsistent
- `shapely` and `sam2` imported in code but not in `requirements.txt`.
- CI runs `pytest src/tests/` but tests live at `./tests/` — CI test step likely fails or tests nothing.
- `README.md` is empty.
- `src/stage3/inference/` is an empty directory.
- `src/stage1/utils/config_helpers.py` is imported cross-stage by `src/stage3/train/train.py` (`from stage1.utils.config_helpers import resolve_device`) — coupling between stages; consider a shared `src/common/` module.

### Suggestions
1. Fix stale Makefile/dvc.yaml paths or add a `src/data` → `src/stage1/data` compatibility note.
2. Move MinIO credentials to `.env`; populate `.env.example` with `MLFLOW_URI`, `DATA_YAML`, `MLFLOW_TRACKING_URI`, MinIO creds.
3. Add `shapely` (and optionally `sam2`) to requirements.
4. Fix CI test path (`pytest tests/`).
5. Remove duplicate `(1)` notebooks and the trailing-space report directories.
6. Archive superseded Stage 2 configs into `configs/train/stage2/archived/`.
