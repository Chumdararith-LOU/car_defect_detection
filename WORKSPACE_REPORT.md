# WORKSPACE_REPORT — car_defect_detection

## Overview

Multi-stage AI pipeline for automotive exterior defect detection and industrial quality inspection. Stage 1 is a binary/semantic pre-screening model (SOD) using Focal Loss and overlapping tiling. Stage 2 is a 7-class defect instance segmentation model (completed) using Resume-and-Adapt transfer and SAHI at 1024px. Stage 3 is a 21-class panel/component segmentation model (M_panel, currently in progress). Stage 4 fuses Stage 2 defects with Stage 3 panels using Intersection-over-Defect (IoD) and computes Damage Severity Index (DSI) for panel-aware diagnostics. Development happens on macOS; training runs on an Ubuntu server (RTX 4090) at `/home/lamacpp/Documents/car_defect_detection`. A FastAPI backend provides orchestration, inspection, dataset management, and training APIs.

## Tech Stack & Dependencies

**Core (requirements.txt):** ultralytics (YOLO), torch >= 2.4, torchvision, opencv-python-headless, mlflow, dvc[s3], onnx, onnxruntime, sahi, shapely, pyyaml, python-dotenv, numpy, pandas, matplotlib, seaborn, tqdm, fastapi, uvicorn[standard], pydantic, pydantic-settings, psutil, python-multipart.

**Dev (requirements-dev.txt):** pytest, pytest-cov, pre-commit, yamllint, black, flake8, isort, mypy, mkdocs + mkdocs-material, jupyter.

**Infra:** Python 3.10 (Dockerfile/CI), Docker Compose (MLflow server on :5001 + MinIO S3 on :9000/:9001), DVC for data versioning, MLflow for experiment tracking, GitHub Actions CI (flake8 + pytest), pre-commit hooks (black, flake8, isort, yamllint, DVC status).

**Environment variables (.env / .env.example):** MLFLOW_URI, MLFLOW_TRACKING_URI, PROJECT_NAME, RUN_NAME, CONFIG_PATH, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, WORKSPACE_PATH, BACKEND_PORT.

**Note:** `sam2` is imported in `run_sam2_full_dataset.py` but only commented in requirements-dev.txt (typically installed from GitHub source).

## Directory Tree

```
.
├── AGENTS.md                          # agent workflow rules (mandatory for AI assistants)
├── Dockerfile                         # Python 3.10 container for MLflow server
├── Makefile                           # main task runner (setup, train, eval, stage3 targets)
├── Proposal.md                        # project proposal document
├── README.md                          # project overview and architecture docs
├── WORKSPACE_REPORT.md                # this file
├── dvc.yaml / dvc.lock               # DVC pipeline stages (stage1 data prep, tiling, pseudo-labels)
├── opencode.json                      # opencode agent configuration
├── requirements.txt                   # core + backend dependencies
├── requirements-dev.txt               # dev/testing/linting dependencies
├── docker-compose.yml                 # MLflow tracker + MinIO services
├── mlflow.db                          # MLflow SQLite backend store
├── skills-lock.json                   # agent skills lock file
├── yolo11n-seg.pt                     # pretrained weights (gitignored)
├── yolo26m-seg.pt                     # pretrained weights for Stage 3 (gitignored)
├── run_full_benchmark_matrix.sh       # benchmark matrix runner
├── run_sam2_full_dataset.py           # SAM2 baseline comparison script
├── run_server_matrix.sh               # server-side benchmark runner
├── run_test_evaluation.sh             # test set evaluation runner
├── .github/workflows/ci.yml           # GitHub Actions: flake8 + pytest
├── .pre-commit-config.yaml            # pre-commit hook config
├── .env / .env.example                # environment config (gitignored)
├── artifacts/                         # exported model artifacts (onnx, tensorrt, ncnn)
│   ├── models/{rt-detr, yolo26s-seg}/
│   ├── ncnn/{benchmarks, bin, param}/
│   ├── onnx/{fp16, fp32, int8}/
│   └── tensorrt/{benchmarks, engine}/
├── backend/                           # FastAPI application (Phase 5 orchestration)
│   ├── main.py                        # FastAPI app entry point
│   ├── config.py                      # legacy config (superseded by core/config.py)
│   ├── api/                           # route handlers (13 routers)
│   ├── core/                          # settings, model manager, system metrics
│   ├── schemas/                       # Pydantic request/response models
│   ├── services/                      # business logic (stages 1-4, training, datasets)
│   ├── configs/                       # runtime config templates
│   ├── models/                        # model weight storage
│   └── data/                          # runtime data (inspections, logs, configs, DBs)
├── configs/                           # training/inference/pipeline YAML configs
│   ├── data/stage1/                   # stage1 dataset configs
│   ├── data/stage2/                   # stage2 dataset configs
│   ├── inference/sahi_production.yaml # SAHI inference config
│   ├── matrix_test.yaml               # benchmark matrix definition
│   ├── pipeline_config.yaml           # global pipeline parameters
│   ├── quant/export_config.yaml       # model export/quantization config
│   └── train/stage{1,2,3}/            # training configs per stage
├── data/                              # all datasets (gitignored, DVC-tracked)
│   ├── raw/                           # original datasets (read-only)
│   ├── processed/                     # generated/converted datasets
│   ├── calibration/                   # calibration images
│   └── results/                       # inference results
├── docs/                              # project documentation
│   ├── architecture.md
│   ├── champion_manifest.md
│   ├── champion_manifest_verified.md
│   ├── host_detection_spec.md
│   ├── master_plan.md
│   └── workspace_cleanup_plan.md
├── notebooks/                         # analysis notebooks
│   └── report_experiment_inventory.ipynb
├── reports/                           # evaluation reports and benchmarks
│   ├── stage2/                        # stage2 results CSVs
│   ├── stage4_batch/                  # stage4 batch mapping JSON reports
│   ├── stage4_mapping/                # stage4 single-image mapping reports
│   └── templates/                     # Jinja2 report template
├── runs/                              # YOLO training runs (gitignored)
│   └── segment/                       # segmentation training outputs
├── src/                               # source code by stage
│   ├── stage1/                        # binary SOD pre-screener
│   │   ├── data/                      # dataset preparation scripts
│   │   ├── deploy/                    # model export
│   │   ├── diagnostics/               # failure analysis, heatmaps, stitching
│   │   ├── eval/                      # evaluation and benchmarking
│   │   ├── inference/                 # inference router, test-set inference
│   │   ├── tests/                     # stage1-specific test harnesses
│   │   ├── train/                     # training scripts (focal loss, SOD)
│   │   └── utils/                     # config helpers
│   ├── stage2/                        # 7-class defect segmentation
│   │   ├── Resume-and-Adapt/          # transfer learning scripts
│   │   ├── annotation/                # CVAT annotation prep
│   │   ├── eval/                      # benchmark/diagnostic notebooks
│   │   ├── inference/                 # SAHI inference
│   │   └── train/                     # training script
│   ├── stage3/                        # 21-class panel segmentation
│   │   ├── data/                      # dataset conversion (COCO→YOLO, YAML resolution)
│   │   ├── eval/                      # visual validation notebook
│   │   └── train/                     # custom trainer with MLflow integration
│   └── stage4/                        # spatial fusion (IoD mapping)
│       ├── spatial_context_mapper.py  # core IoD/DSI mapper
│       └── batch_mapping_test.py      # batch test harness
├── tests/                             # pytest test suite
│   ├── test_data.py                   # dataset validation tests
│   └── smoke_test_focal.py            # focal loss smoke test
└── archive/                           # superseded pre-standardization materials
    ├── INVENTORY.md
    └── pre_standardization/
        ├── configs/stage2/            # old stage2 training configs
        ├── legacy_import/             # legacy YOLO import files
        ├── mlruns_legacy/             # old MLflow run artifacts
        └── notebooks/                 # diagnostic/EDA notebooks
```

## Folder-by-Folder Breakdown

| Folder | Purpose |
|--------|---------|
| `backend/api/` | FastAPI route handlers: health, host detection, inspection, datasets, dataset images/import/prep, models, reviews, system metrics, training, experiments |
| `backend/core/` | App settings (pydantic-settings), model weight manager, system metrics (psutil) |
| `backend/schemas/` | Pydantic v2 request/response models for all API endpoints |
| `backend/services/` | Business logic: stage1-4 inference orchestration, dataset building/tiling/import/registry, training worker (background subprocess), inspection store, review DB, host detection, experiment service |
| `backend/data/` | Runtime artifacts: inspection payloads (images + JSON), training logs, training config snapshots, SQLite DBs (reviews.db, training_jobs.db) |
| `configs/` | All YAML configs: dataset definitions, training hyperparameters, inference params, pipeline globals, export/quantization settings |
| `data/raw/` | Read-only original datasets: CarDD_release, Car defect 2000/2200, Roboflow, archive |
| `data/processed/` | Generated datasets: SOD, tiled variants, stage2 YOLO, stage3 car_damages_panel, calibration |
| `src/stage1/` | Binary SOD pre-screener: data prep, focal-loss training, evaluation, diagnostics (Grad-CAM, heatmaps), ONNX export, inference router |
| `src/stage2/` | 7-class defect segmentation: Resume-and-Adapt transfer scripts, SAHI inference, CVAT annotation prep, training |
| `src/stage3/` | 21-class panel segmenter: COCO→YOLO conversion, dataset YAML resolution, custom trainer with MLflow logging |
| `src/stage4/` | Spatial fusion: IoD-based defect→panel mapper, DSI computation, batch testing |
| `tests/` | Pytest suite: dataset schema validation, focal loss smoke test |
| `reports/` | Evaluation outputs: benchmark CSVs, stage4 mapping JSON reports, Jinja2 report template |
| `docs/` | Architecture, champion manifests, master plan, cleanup plan |
| `notebooks/` | Experiment inventory analysis |
| `artifacts/` | Exported model formats: ONNX (fp16/fp32/int8), TensorRT engines, NCNN |
| `runs/` | YOLO training run outputs (weights, logs, results) |
| `archive/` | Superseded configs, legacy MLflow runs, diagnostic notebooks from pre-standardization era |
| `.agents/skills/` | Agent skill definitions: debugging-wizard, fastapi-expert, fine-tuning-expert, ml-pipeline, test-master |
| `.opencode/` | OpenCode agent configuration and project rules |

## Key Files & Entry Points

| File | Role |
|------|------|
| `backend/main.py` | FastAPI app entry point; mounts 12 routers, CORS middleware |
| `backend/core/config.py` | Pydantic Settings for backend configuration |
| `backend/core/model_manager.py` | Model weight loading and lifecycle management |
| `backend/services/training_worker.py` | Background training subprocess with config snapshotting |
| `backend/services/stage1.py` – `stage4.py` | Per-stage inference orchestration services |
| `backend/services/experiment_service.py` | Experiment tracking service (new, untracked) |
| `src/stage1/train/train.py` | Stage 1 SOD training entry |
| `src/stage1/train/train_stage1_focal_full.py` | Focal loss full training variant |
| `src/stage2/train/train.py` | Stage 2 defect segmentation training |
| `src/stage2/Resume-and-Adapt/stage1_head_warmup.py` | Head-only warmup transfer (champion approach) |
| `src/stage2/inference/sahi_inference.py` | SAHI tiled inference for stage 2 |
| `src/stage3/train/train.py` | Stage 3 custom trainer (imports stage1.utils.config_helpers) |
| `src/stage3/data/convert_car_damages_to_yolo.py` | COCO→YOLO panel dataset converter |
| `src/stage3/data/resolve_dataset_yaml.py` | Dataset YAML path resolution (local vs server) |
| `src/stage4/spatial_context_mapper.py` | IoD/DSI spatial mapper (core stage 4 logic) |
| `src/stage4/batch_mapping_test.py` | Batch evaluation harness for stage 4 |
| `Makefile` | Task runner: setup, data-consolidate, train targets, stage3-preflight/train |
| `dvc.yaml` | DVC pipeline: prep_sod_data, tile_data, pseudo-labels, validation |
| `run_sam2_full_dataset.py` | SAM2 baseline comparison (requires sam2 from GitHub) |
| `configs/train/stage3/panel_segmenter_baseline.yaml` | Stage 3 baseline training config |
| `configs/pipeline_config.yaml` | Global pipeline parameters and gating thresholds |
| `tests/test_data.py` | Dataset schema validation tests |
| `.github/workflows/ci.yml` | CI: flake8 lint + pytest tests/ |

## Observations for Refactoring

### Code Smells & Structural Issues

1. **Cross-stage coupling:** `src/stage3/train/train.py` imports `from stage1.utils.config_helpers import resolve_device` — coupling between stages. Consider extracting to `src/common/`.
2. **Duplicate config files:** `backend/config.py` (legacy) coexists with `backend/core/config.py` (pydantic-settings). The legacy one appears unused.
3. **Stale DVC/Makefile paths:** `dvc.yaml` references `src/data/prep_sod.py` and `src/data/create_tiles.py` but actual scripts are under `src/stage1/data/`. Makefile `data-consolidate` target references `src/data/consolidate.py` (non-existent).
4. **Untracked new backend files:** `backend/api/experiments.py`, `backend/schemas/experiments.py`, `backend/services/experiment_service.py`, `backend/data/configs/training/058fd366-*.yaml` are untracked in git.
5. **`src/stage3/inference/` is missing** — no inference script for panel model yet (noted in AGENTS.md as future work).
6. **Archive bloat:** `archive/pre_standardization/` contains ~40 notebooks, legacy configs, and MLflow artifacts that add noise.
7. **Report directories with trailing spaces:** `reports/stage2/yolo26m_1024_stage2_baseline ` and `yolo26m_1024_stage2_clean_multiscale_v2 ` have trailing spaces in directory names.
8. **backend/data/ not fully gitignored:** Only `*.db` files are excluded; inspection images, logs, and config snapshots may accumulate.

### Dependency Notes

- `shapely` and `sahi` are now declared in requirements.txt (previously missing).
- `sam2` remains undeclared (comment-only in requirements-dev.txt); acceptable since it's only used in one comparison script.
- Backend uses `pydantic-settings` for config but `python-dotenv` is also in requirements (potential overlap).

### CI & Testing

- CI runs `pytest tests/` (correct path).
- Only 2 test files exist (`test_data.py`, `smoke_test_focal.py`) — minimal coverage for the backend and stage 1-4 logic.

### Suggestions

1. Extract shared utilities (config_helpers, device resolution) into `src/common/` to break cross-stage imports.
2. Remove or archive `backend/config.py` if superseded by `backend/core/config.py`.
3. Fix DVC stage paths to point to actual script locations (`src/stage1/data/`).
4. Commit or `.gitignore` the new experiment service files.
5. Add `backend/data/inspections/`, `backend/data/logs/`, `backend/data/configs/` to `.gitignore` if not needed in version control.
6. Rename trailing-space report directories.
7. Add backend API tests (health endpoint, basic schema validation) to `tests/`.
8. Consider consolidating `Makefile` stage1 targets that reference non-existent paths.
