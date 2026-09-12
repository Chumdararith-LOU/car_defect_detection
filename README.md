# Car Defect Detection

> Multi-stage automated visual inspection pipeline for detecting, segmenting,
> and assessing car body defects. Built for automotive quality control and
> insurance damage assessment.

## Architecture (4-Stage Pipeline)

| Stage | Name | Function | Model |
|---|---|---|---|
| 1 | Pre-Screener | Binary saliency detector; routes clean cars to PASS | SOD (binary) |
| 2 | Defect Segmentation | Multi-class instance segmentation (7 defect types) | YOLOv8-seg |
| 3 | Panel Mapping | Assigns defects to specific car panels | Panel-seg model |
| 4 | Fusion & Severity | Computes IoD and Damage Severity Index (DSI) | Rule-based |

## Defect Taxonomy (7 Classes)

| ID | Class | Description |
|---|---|---|
| 0 | broken_lamp | Damaged or missing headlight/taillight |
| 1 | corrosion | Rust or oxidized metal patches |
| 2 | crack | Surface cracks in body panels or glass |
| 3 | dent | Dents and deformations |
| 4 | disjoint_part | Detached or misaligned components |
| 5 | glass_shatter | Shattered or broken glass |
| 6 | scratch | Scratches and paint damage |

## Dataset

- Sources: CarDD_COCO, car_defect_2000/2200, Roboflow exports, clean-car pool
- Unified 7-class taxonomy with alphabetical ordering
- ~6,366 training images, ~1,018 val, ~593 test
- 999 clean-car training images (empty labels) + 150 clean-eval images
- Labels: YOLO segmentation format in data/processed/yolo_seg_clean/

## Repository Structure

```
.
├── AGENTS.md
├── README.md
├── archive
│   ├── INVENTORY.md
│   ├── experiment_configs
│   ├── experiment_scripts
│   └── pre_standardization
├── backend
│   ├── api
│   ├── core
│   ├── data
│   ├── main.py
│   ├── models
│   ├── schemas
│   └── services
├── configs
│   ├── data
│   ├── inference
│   ├── matrix_test.yaml
│   ├── models
│   ├── pipeline_config.yaml
│   ├── quant
│   └── train
├── data
│   ├── calibration
│   ├── calibration.dvc
│   ├── processed
│   ├── raw
│   ├── raw.dvc
│   ├── results
│   └── training_jobs.db
├── docs
│   ├── Consolidated Project Report.md
│   ├── Proposal.md
│   ├── Stage 2 Training Platform.md
│   ├── WORKSPACE_REPORT.md
│   ├── architecture.md
│   ├── champion_manifest.md
│   ├── champion_manifest_verified.md
│   ├── host_detection_spec.md
│   ├── master_plan.md
│   ├── reports
│   └── workspace_cleanup_plan.md
├── fig
│   ├── four_pillars.png
│   ├── objectness_weights.png
│   └── routing_winners.png
├── frontend
│   ├── AGENTS.md
│   ├── DESIGN_AUDIT.md
│   ├── FRONTEND_REPORT.md
│   ├── WORKSPACE_REPORT.md
│   ├── bun.lock
│   ├── bunfig.toml
│   ├── components.json
│   ├── eslint.config.js
│   ├── images
│   ├── opencode.json
│   ├── package.json
│   ├── plan.md
│   ├── skills-lock.json
│   ├── src
│   ├── tsconfig.json
│   └── vite.config.ts
├── opencode.json
├── reports
│   ├── benchmark_results
│   ├── figures
│   ├── inspection-tab-analysis.md
│   ├── inspection_tab_backend_report.md
│   ├── operator_guide.md
│   ├── slides
│   └── system_guide.md
├── requirements-dev.txt
├── requirements.txt
├── server.log
├── skills-lock.json
├── src
│   ├── stage1
│   ├── stage2
│   ├── stage3
│   └── stage4
├── tests
│   ├── __init__.py
│   ├── smoke_test_focal.py
│   └── test_data.py
└── tools
    ├── eval_rare_thresholds.py
    ├── video_stage2_live.py
    └── xray_diag.py

42 directories, 51 files
```

## Training

Stage 2 configs: configs/train/stage2/
- Stage2-training.yaml (main production config)
- objectness_branch.yaml (production model)
- model5_stage1_head_warmup_7cls_extended.yaml (baseline_m5)

Key training decisions:
- Loss: Plain BCE (Seesaw Loss was tested and rejected — BCE control outperformed)
- Fine-tuning: Surgical early_texture mode (unfreeze layers 0-4 + head)
- Optimizer: AdamW, lr0=0.001
- Image size: 1024x1024

## Inference (SAHI Pipeline)

Production inference uses Slicing Aided Hyper Inference (SAHI):
- Slice size: 1024x1024, overlap: 15%
- NMS: Mask-IoS, threshold 0.50
- Device: MPS (Apple Metal) or CUDA
- Multi-model routing: balanced / safety / max_recall presets

## Production Model Registry

| Preset | Model | Role |
|---|---|---|
| objectness_branch_new | Best overall | Primary detector |
| baseline_m5 | Head-class specialist | Safety preset routing |

## Quickstart (Clone & Run)

### Prerequisites

* Python 3.10 (Conda recommended)
* Git LFS — champion weights are stored via LFS: `git lfs install` (one-time)
* Bun (frontend): [bun.sh](https://bun.sh?utm_source=chatgpt.com)

### 1. Clone & Create Environment

```bash
git clone https://github.com/Chumdararith-LOU/car_defect_detection.git
cd car_defect_detection

conda create -n car_defect python=3.10
conda activate car_defect
```

### 2. Install Dependencies

```bash
# Ubuntu + NVIDIA GPU: You MUST install the CUDA build of PyTorch FIRST.
# (The default pip version is CPU-only and will result in 'no_gpu' warnings).
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Then install the rest of the dependencies
pip install -r requirements.txt
```

### 3. Model Weights (~132 MB)

Champion weights are tracked with Git LFS. If they were not downloaded automatically:

```bash
git lfs install
git lfs pull
```

Then verify checksums and create deployment symlinks:

```bash
python scripts/setup_models.py
```

### 4. Run the Backend

The backend runs on port `8010`:

```bash
cd backend
uvicorn main:app --reload --port 8010
```

### 5. Run the Frontend

Open a **new terminal**:

```bash
cd frontend
bun install
bun run dev
```

Open:

```text
http://localhost:8080
```

The frontend expects the backend at:

```text
http://localhost:8010
```

---

## Evaluation

### Quick Evaluation

```bash
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml
```

### Evaluation Modes

| Mode | Description |
|---|---|
| `benchmark` | Per-class mAP, precision, recall, size-bucketed metrics |
| `clean_fpr` | False positive rate on clean (defect-free) images |
| `latency` | Inference timing (preprocess/inference/NMS) |
| `memory` | Peak VRAM/RAM usage |
| `full` | Run all modes |

### Multi-Model Comparison

```bash
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml --mode full
```

This generates comparison reports in `reports/eval/` with:
- Markdown report for human reading
- JSON results for CI/regression checks
- Optional MLflow logging

### Evaluation Modules

```
src/stage2/eval/
├── evaluate.py          # Single CLI entry point
├── sahi_eval.py         # SAHI inference + NMS-IOS
├── report.py            # Report generation
├── metrics/
│   ├── classwise.py     # Per-class P/R/F1/AP
│   ├── size_bucketed.py # Small/Medium/Large breakdown
│   └── clean_fpr.py     # Production hallucination rate
└── perf/
    ├── latency.py       # Timing instrumentation
    └── memory.py        # VRAM/RAM tracking
```

## Training

### Quick Training Run

```bash
python src/train/train.py --config configs/train/stage2/Stage2-training.yaml
```

### Training with Objectness Branch

```bash
python src/train/train.py --config configs/train/stage2/objectness_branch.yaml
```

### Key Training Parameters

| Parameter | Value | Description |
|---|---|---|
| loss_type | bce | Default loss (Seesaw was rejected) |
| imgsz | 1024 | Training image size |
| optimizer | AdamW | Recommended for fine-tuning |
| lr0 | 0.001 | Initial learning rate |
| surgical_mode | early_texture | Unfreeze layers 0-4 + head |

### Training Configs

| Config | Purpose |
|---|---|
| `configs/train/stage2/Stage2-training.yaml` | Main production training |
| `configs/train/stage2/objectness_branch.yaml` | Objectness branch model |
| `configs/train/stage2/model5_stage1_head_warmup_7cls_extended.yaml` | Baseline reference |

## Inference (SAHI Pipeline)

Production inference uses Slicing Aided Hyper Inference (SAHI):

| Parameter | Value | Description |
|---|---|---|
| slice_size | 1024 | Patch size in pixels |
| overlap_ratio | 0.15 | Overlap between patches |
| NMS metric | IOS | Intersection over Smaller (for thin boxes) |
| NMS threshold | 0.50 | Suppression threshold |

```bash
# Run SAHI inference on an image
python src/stage2/inference/sahi_inference.py --image path/to/image.jpg --weights runs/segment/best.pt
```

## Production Model Registry

| Preset | Model | Role |
|---|---|---|
| objectness_branch_new | Best overall | Primary detector |
| baseline_m5 | Head-class specialist | Safety preset routing |
| surgical_early | Texture specialist | Corrosion detection |

## Repository Structure

```
car_defect_detection/
├── README.md                    # This file
├── HANDOVER.md                  # Experiment history + lessons
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Dev dependencies
├── .env.example                 # Environment template
├── configs/
│   ├── data/                    # Dataset configs
│   ├── train/                   # Training configs
│   ├── eval/                    # Evaluation configs
│   └── inference/               # Inference configs
├── src/
│   ├── models/                  # Custom model components
│   │   ├── heads.py             # Segment26WithObjectness
│   │   ├── losses.py            # ScaledFocalBCE, SeesawBCE
│   │   └── segment_head_with_obj.py
│   ├── train/                   # Training pipeline
│   ├── stage1/                  # SOD pre-screener
│   ├── stage2/                  # Defect segmentation
│   │   ├── eval/                # Evaluation harness
│   │   ├── inference/           # SAHI inference
│   │   └── train/               # Training scripts
│   ├── stage3/                  # Panel segmentation
│   └── stage4/                  # Fusion & severity
├── vendor/
│   └── ultralytics/             # Forked Ultralytics (see MODIFICATIONS.md)
├── backend/                     # FastAPI server
├── frontend/                    # Web UI
├── scripts/                     # Utility scripts
├── data/                        # Dataset (gitignored)
├── runs/                        # Training outputs (gitignored)
└── reports/                     # Evaluation reports
```

## Critical Warnings

1. **Do NOT run `pip install ultralytics`** — it will overwrite the vendored fork. Use `pip install -e vendor/ultralytics` instead.

2. **Seesaw Loss was REJECTED** — Plain BCE outperformed all Seesaw configurations by >2×. Use `loss_type: bce` as default.

3. **Class ordering is ALPHABETICAL** — 0:broken_lamp, 1:corrosion, 2:crack, 3:dent, 4:disjoint_part, 5:glass_shatter, 6:scratch.

4. **Corrosion is the HEAD class** (13,961 instances) — It's a texture/feature-learning problem, not a rare-class problem. Surgical fine-tuning of early layers is the solution.

5. **MPS (MacBook) does NOT support amp=True** — Use `amp: false` on MacBook to avoid NaN divergence.
