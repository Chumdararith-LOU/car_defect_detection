# Car Defect Detection Pipeline

A multi-stage AI pipeline for automotive exterior defect detection and industrial quality inspection.

## Architecture Overview

The system uses a cascaded architecture to balance high recall for micro-defects with precise classification and spatial context:

- **Stage 1 (Binary SOD Pre-Screener):** Class-agnostic anomaly detection using overlapping tiling and Focal Loss to catch hairline scratches and micro-defects.
- **Stage 2 (7-Class Defect Segmentation):** Instance segmentation (dent, scratch, crack, glass_shatter, broken_lamp, corrosion, disjoint_part) using Resume-and-Adapt transfer learning and SAHI (Slicing Aided Hyper Inference) at 1024px native resolution.
- **Stage 3 (21-Class Panel Segmenter):** Spatial context mapping to identify vehicle components (Hood, Doors, Bumpers, Wheels, etc.).
- **Stage 4 (Spatial Fusion & Reporting):** Fuses Stage 2 defects with Stage 3 panels using Intersection-over-Defect (IoD), computes Damage Severity Index (DSI), and generates factory reports.

## Repository Structure

```text
car_defect_detection/
├── src/
│   ├── stage1/          # Binary SOD pre-screening
│   ├── stage2/          # 7-class defect segmentation
│   ├── stage3/          # 21-class panel segmentation
│   └── stage4/          # Spatial fusion and reporting
├── configs/
│   ├── train/           # Training configurations per stage
│   ├── data/            # Dataset split configurations
│   └── inference/       # SAHI production inference configs
├── data/                # Raw and processed datasets (gitignored)
├── runs/                # Ultralytics training outputs (gitignored)
├── mlruns/              # MLflow tracking store (gitignored)
├── tests/               # Pytest test suite
├── archive/             # Archived legacy experiments and notebooks
└── docs/                # Architecture and planning documents
```

## Setup

1. Ensure you have Python 3.10+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. For development tools (linting, testing):
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Copy the environment template and configure your local paths:
   ```bash
   cp .env.example .env
   ```

## Infrastructure

The project uses Docker Compose to run local infrastructure:

```bash
docker compose up -d
```

This starts:
- **MLflow Tracking Server** (port 5001) for experiment logging.
- **MinIO** (ports 9000/9001) for S3-compatible artifact storage.

## Usage

### Training
Training is configured via YAML files in `configs/train/`.

Example for Stage 2:
```bash
yolo segment train --config configs/train/stage2/model5_stage1_head_warmup_7cls_extended.yaml
```

### Inference
Production inference uses SAHI to recover micro-defects. Configuration is in `configs/inference/sahi_production.yaml`.

## Documentation

Detailed architecture, host detection specs, and champion model manifests are located in the `docs/` directory.
