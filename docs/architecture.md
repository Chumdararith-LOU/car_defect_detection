# Car Defect Detection — System Architecture

Version: 0.1
Date: 2026-08-12
Status: Draft for approval

## 1. Purpose

This document defines the architecture of the `car_defect_detection` system.

The system is a multi-stage AI pipeline for automotive exterior defect detection, operator review, model improvement, and controlled deployment.

It covers:

1. Stage 1 — binary salient defect / anomaly pre-screening.
2. Stage 2 — 7-class defect instance segmentation.
3. Stage 3 — 21-class panel/component segmentation.
4. Stage 4 — spatial fusion, panel assignment, DSI, factory report.
5. Operator dashboard.
6. Engineer training/experiment workbench.
7. Host detection and local/remote runtime selection.
8. Data flywheel and continuous model improvement.
9. Model registry, evaluation gates, and deployment.

This architecture is intended to support:

```text
local company desktop deployment
remote GPU server deployment
hybrid deployment
operator-friendly inspection
engineer-friendly experimentation
human-approved continuous learning
```

---

## 2. System Overview

The product has two main layers:

### 2.1 Inspection Layer

This layer runs the AI pipeline on car images and produces an operator-facing report.

```text
Input image
    ↓
Panel context
    ↓
Defect detection
    ↓
Anomaly rescue
    ↓
Filtering / fusion
    ↓
Factory report
```

### 2.2 Model Improvement Layer

This layer uses operator feedback and engineering tools to improve models over time.

```text
Operator feedback
    ↓
Hard example mining
    ↓
Dataset update
    ↓
Leakage audit
    ↓
Training
    ↓
Evaluation
    ↓
Human approval
    ↓
Deployment
```

The two layers are connected through a shared backend, model registry, and dataset registry.

---

## 3. High-Level Architecture

```text
┌────────────────────────────────────────────┐
│              Desktop / Web UI              │
│                                            │
│  Operator Mode                             │
│  Review Mode                               │
│  Engineer Mode                             │
│  Host / Settings                           │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│              FastAPI Backend               │
│                                            │
│  Health API                                │
│  Host API                                  │
│  Runtime API                               │
│  Inspection API                            │
│  Review API                                │
│  Dataset API                               │
│  Training API                              │
│  Experiment API                            │
│  Model Registry API                        │
│  Deployment API                            │
└───────┬───────────────────────┬────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌────────────────────┐
│  Local Worker   │     │  Remote Worker     │
│  Local GPU/CPU  │     │  GPU Server        │
└───────┬─────────┘     └─────────┬──────────┘
        │                         │
        ▼                         ▼
┌────────────────────────────────────────────┐
│              Pipeline Engine               │
│                                            │
│  Stage 1 binary anomaly                    │
│  Stage 2 7-class defect                    │
│  Stage 3 panel segmentation                │
│  Stage 4 fusion / IoD / DSI                │
└───────┬────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────┐
│          Data / Model Governance           │
│                                            │
│  Dataset manifests                         │
│  MLflow experiment tracking                │
│  Model registry                            │
│  Evaluation reports                        │
│  Deployment manifests                      │
│  Operator feedback database                │
└────────────────────────────────────────────┘
```

---

## 4. Deployment Topologies

The architecture must support three deployment styles.

### 4.1 Fully Local Desktop

```text
Desktop app
FastAPI backend
Inference worker
Training worker
Model registry
Database
```

All components run on the same company desktop.

Best for:

```text
single machine
simple setup
offline operation
```

### 4.2 Remote GPU Server

```text
Operator desktop app
        ↓
Remote FastAPI backend
Remote GPU worker
Remote dataset storage
Remote model registry
```

Best for:

```text
centralized training
centralized model management
multiple operators
```

### 4.3 Hybrid

```text
Local desktop:
    inference
    operator review

Remote server:
    training
    experiment tracking
    model registry
```

Best for:

```text
fast operator experience
centralized GPU training
controlled model release
```

The host detection module decides the recommended topology automatically, but the user can override it.

---

## 5. Core Components

## 5.1 Desktop / Web UI

The UI is the user-facing application.

It is built around the existing React dashboard and will evolve into a combined Operator + Engineer app.

Current frontend foundation:

```text
React 19
TanStack Router / Start
Tailwind CSS v4
shadcn/ui
FastAPI backend client
SVG overlay rendering
```

Future UI modules:

```text
Inspection
Review
Datasets
Training
Experiments
Models
Deployment
Settings
Host / System
```

UI principles:

1. Operator screens must be simple.
2. Engineer screens can be technical.
3. The UI must not directly manage messy files.
4. The UI must show model versions and host status.
5. The UI must support operator feedback.
6. The UI must work with local and remote backends.

---

## 5.2 FastAPI Backend

The backend is the central service.

It owns:

```text
configuration
runtime selection
host detection
pipeline execution
training jobs
model registry access
review feedback
report generation
```

The backend should expose stable APIs consumed by the UI.

The UI should never directly invoke training scripts or read arbitrary model folders.

---

## 5.3 Host Detection and Runtime Manager

The host detection module detects the current machine and decides what operations are safe.

It detects:

```text
OS
CPU
RAM
disk space
GPU
CUDA availability
VRAM
local model availability
local dataset availability
remote server availability
```

It produces:

```text
host profile
capability flags
warnings
recommended runtime mode
```

Runtime modes:

```text
auto
local
remote
hybrid
```

Example recommendation:

```text
Local GPU detected:
    inference = local CUDA
    training = local CUDA

No local GPU but remote server available:
    inference = local CPU or remote
    training = remote
```

The user can override the recommendation.

---

## 5.4 Pipeline Engine

The pipeline engine runs inference.

It coordinates:

```text
Stage 1
Stage 2
Stage 3
Stage 4
```

It applies:

```text
model loading
tiling / SAHI
threshold presets
panel context filtering
tire suppression
non-car suppression
Stage 1 rescue
IoD panel assignment
DSI severity calculation
report generation
```

---

## 5.5 Training Orchestrator

The training orchestrator manages training jobs.

It supports:

```text
Stage 1 training
Stage 2 training
Stage 3 training
dataset version selection
config selection
device selection
local/remote execution
log streaming
job stopping
result collection
```

Training jobs must record:

```text
stage
dataset version
config hash
git commit
base model
execution host
device
start time
end time
metrics
artifacts
MLflow run ID
```

---

## 5.6 Dataset Registry

The dataset registry tracks dataset versions.

Each dataset version must contain:

```text
manifest.json
class_map.json
split.json
annotation_rules.md
quality_report.json
leakage_audit.json
```

Dataset statuses:

```text
raw
quarantine
curated
released
archived
```

Only `released` datasets may be used for official training.

---

## 5.7 Model Registry

The model registry tracks model versions per stage.

Model statuses:

```text
candidate
champion
deployed
archived
rejected
```

Each model version stores:

```text
stage
model name
version
weights path
config hash
dataset version
training run ID
metrics
evaluation report
model card
promotion history
deployment history
```

MLflow is used for experiment tracking.

The model registry is the source of truth for deployment.

---

## 5.8 Review / Feedback Database

The review database stores operator feedback.

Stored events:

```text
inspection_id
image_id
detection_id
model_version
stage
predicted_class
predicted_panel
confidence
operator_decision
corrected_class
corrected_polygon
timestamp
```

Operator decisions:

```text
confirm
reject
reclassify
mark_unclear
add_missing_defect
```

This database powers the data flywheel.

---

## 6. ML Pipeline Stages

## 6.1 Stage 1 — Binary SOD Pre-Screener

### Purpose

Stage 1 is a class-agnostic anomaly detector.

It answers:

```text
Is there any possible defect here?
```

### Current champion

```text
M3: YOLO26m, 640 tiled, Focal Loss
```

Known champion metrics:

| Metric | Value |
|---|---:|
| Recall | 95.2% |
| False positive rate | 50% |
| mIoU | 43.8% |
| p95 latency | 33.8 ms |
| Memory footprint | 170.1 MB |

### Locked principles

```text
15% overlapping coarse tiling
Focal Loss gamma = 2.0
leakage-free validation
threshold calibration separate from evaluation
```

### Role in production

Stage 1 is used as:

```text
high-recall anomaly screener
Stage 2 rescue engine
hard-example miner
```

It is not used to provide defect class labels.

---

## 6.2 Stage 2 — 7-Class Defect Instance Segmentation

### Purpose

Stage 2 detects and classifies defects.

Production taxonomy:

| Class ID | Class Name |
|---:|---|
| 0 | dent |
| 1 | scratch |
| 2 | crack |
| 3 | glass_shatter |
| 4 | broken_lamp |
| 5 | corrosion |
| 6 | disjoint_part |

### Champion model

```text
Model 5 Stage 1 Extended, 7-class
```

Run folder:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended
```

Weights:

```text
runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt
```

### Champion metrics

| Metric | Value |
|---|---:|
| Best validation Mask mAP50 | 0.651 |
| Best epoch | 78 |
| Test Mask mAP50 | 0.650 |
| Test Mask mAP50-95 | 0.494 |
| Test Precision | 0.666 |
| Test Recall | 0.635 |

### Locked training principles

```text
Resume-and-Adapt transfer from Model 1 backbone
freeze: 23
extended head-only warmup
imgsz: 1024
multi_scale: false
mosaic: 0.0
scale: 0.3
degrees: 15.0
```

### Locked inference principles

```text
Native resolution rule: 1024px
SAHI slice size: 1024
SAHI overlap: 15%
Mask-IOS NMS
operator presets:
    balanced
    safety
    max_recall
```

### Role in production

Stage 2 is the primary defect classifier.

It provides:

```text
defect class
defect mask
confidence
```

---

## 6.3 Stage 3 — Panel/Component Segmenter

### Purpose

Stage 3 segments vehicle panels and components.

It provides spatial context for:

```text
panel assignment
tire suppression
non-car suppression
DSI calculation
close-up fallback behavior
```

### Champion model

```text
panel_segmenter_baseline
```

Known weights location:

```text
mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt
```

Server-side run folder:

```text
TO_VERIFY
```

### Dataset

```text
998 images
21 panel/component classes
split: 798 train / 100 val / 100 test
seed: 42
```

### Champion metrics

| Metric | Val | Test |
|---|---:|---:|
| Mask mAP50 | 0.885 | 0.879 |
| Mask mAP50-95 | 0.630 | 0.626 |
| Mask Precision | 0.882 | 0.885 |
| Mask Recall | 0.841 | 0.824 |

### Locked training principles

```text
fresh yolo26m-seg.pt
imgsz: 640
batch: 8
AdamW
epochs: 100
patience: 20
mild augmentation
hole subtraction for panel openings
```

### Important classes for filtering

```text
Front-wheel
Back-wheel
```

These are used for tire suppression.

---

## 6.4 Stage 4 — Spatial Context Mapper

### Purpose

Stage 4 fuses defect detections with panel context.

It produces:

```text
panel assignment
DSI severity
Boundary/Trim fallback
factory report JSON
overlay image
auto-crops
```

### Core module

```text
src/stage4/spatial_context_mapper.py
```

Batch test harness:

```text
src/stage4/batch_mapping_test.py
```

### Core math

Intersection over Defect:

```text
IoD(defect, panel) =
    area(defect ∩ panel)
    /
    area(defect)
```

Assignment rule:

```text
assigned_panel = argmax IoD
if max IoD >= 0.50
else Boundary/Trim
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

### Locked defaults

```text
theta_containment = 0.50
panel_conf default = 0.25
Boundary/Trim fallback = safe behavior
```

---

## 7. Production Inference Flow

The recommended production inference order is:

```text
Input image
    ↓
Stage 3 panel segmentation
    ↓
Build car_context_mask and tire_mask
    ↓
Stage 1 binary anomaly detection
    ↓
Stage 2 7-class defect detection
    ↓
Stage 4 fusion
    ↓
Factory report
```

Stage 1 and Stage 2 may run in parallel after Stage 3 if performance optimization is needed.

---

## 8. Fusion Rules

Stage 4 should apply the following rules.

### 8.1 Tire suppression

```text
If defect overlaps tire mask strongly:
    suppress
    reason = tire
```

Recommended starting rule:

```text
tire_mask = union(Front-wheel, Back-wheel)
tire_ignore_iod >= 0.50
```

### 8.2 Non-car suppression

```text
If Stage 1 anomaly is mostly outside car panel context:
    suppress
    reason = non_car_context
```

Recommended starting rule:

```text
car_context_min_iod >= 0.30
```

### 8.3 Stage 2 classified defect

```text
If Stage 2 detects a defect on a valid panel:
    keep Stage 2 class
    assign panel
    compute DSI
```

### 8.4 Stage 1 rescue

```text
If Stage 1 detects an anomaly on car body
and Stage 2 has no matching detection:
    create unclassified_anomaly
```

### 8.5 Matching Stage 1 and Stage 2

Use Intersection over Smaller mask area:

```text
IoS =
    area(stage1_mask ∩ stage2_mask)
    /
    min(area(stage1_mask), area(stage2_mask))
```

Recommended starting threshold:

```text
stage1_stage2_match_ios >= 0.30
```

### 8.6 Low-context fallback

```text
If panel context is weak or close-up image is out of distribution:
    use Boundary/Trim or low_context flag
    do not silently misassign
```

---

## 9. Inspection Output Contract

The final inspection result should include:

```text
inspection_id
image_id
timestamp
model_versions
runtime_mode
execution_host
pass_fail verdict
panels
defects
unclassified_anomalies
suppressed_detections
report_assets
```

Example defect object:

```json
{
  "defect_id": "DEF_001",
  "class": "scratch",
  "confidence": 0.71,
  "panel": "Front-door",
  "iod": 0.98,
  "dsi": 5.2,
  "source": "stage2",
  "stage1_matched": true,
  "suppressed": false
}
```

Example rescued anomaly:

```json
{
  "defect_id": "DEF_021",
  "class": "unclassified_anomaly",
  "confidence": 0.63,
  "panel": "Rocker-panel",
  "source": "stage1_rescue",
  "stage2_matched": false,
  "suppressed": false
}
```

Example suppressed detection:

```json
{
  "defect_id": "DEF_030",
  "class": "scratch",
  "confidence": 0.44,
  "panel": "Front-wheel",
  "source": "stage2",
  "suppressed": true,
  "suppression_reason": "tire"
}
```

---

## 10. Training Architecture

## 10.1 Training Inputs

Every training job must define:

```text
stage
dataset_version
config
base_model
device
execution_host
git_commit
seed
```

## 10.2 Training Outputs

Every training job must produce:

```text
weights
metrics.json
config snapshot
dataset manifest reference
MLflow run ID
model card
evaluation report
failure examples
```

## 10.3 Stage-Specific Training

### Stage 1 training

Task:

```text
binary defect / anomaly segmentation
```

Important metrics:

```text
recall
false positive rate
mIoU
hairline scratch recall
tree/wall false positives
tire false positives
latency
```

### Stage 2 training

Task:

```text
7-class defect instance segmentation
```

Important metrics:

```text
Mask mAP50
Mask mAP50-95
precision
recall
per-class recall
corrosion recall
disjoint_part recall
micro-defect recall
false positives per image
latency
```

### Stage 3 training

Task:

```text
21-class panel segmentation
```

Important metrics:

```text
Mask mAP50
Mask mAP50-95
per-class panel mAP50
wheel/tire mask quality
close-up degradation behavior
generalization gap
```

---

## 11. Evaluation Gates

Candidate models must pass evaluation gates before promotion.

Example gates:

```yaml
promotion_gates:
  stage1:
    require_clean_leakage_audit: true
    min_recall: 0.90
    max_false_positives_per_image: configurable
    require_hairline_scratch_audit: true

  stage2:
    require_clean_leakage_audit: true
    min_test_mask_map50: champion - 0.005
    max_rare_class_recall_regression: 0.05
    max_false_positives_per_image: configurable
    require_visual_audit: true

  stage3:
    require_clean_leakage_audit: true
    min_test_mask_map50: champion - 0.005
    require_wheel_mask_audit: true
    require_close_up_behavior_check: true
```

Deployment requires human approval.

---

## 12. Data Flywheel Architecture

```text
Production inference
    ↓
Operator review
    ↓
Confirmed defects / rejected false positives
    ↓
Hard example queue
    ↓
Dataset builder
    ↓
Leakage audit
    ↓
Released dataset version
    ↓
Training job
    ↓
Evaluation gates
    ↓
Human approval
    ↓
Deployment
```

### Sources of new training data

1. Operator-confirmed rare defects.
2. Operator-rejected false positives.
3. Stage 1 rescued anomalies missed by Stage 2.
4. Tire false positives.
5. Tree/wall/background false positives.
6. Close-up low-context cases.

### Important rule

Pseudo-labels from Stage 1 should be human-reviewed before entering official Stage 2 training data.

---

## 13. Host Detection Architecture

The host detection module is a backend service.

It should expose:

```text
GET /api/health
GET /api/host/profile
POST /api/host/detect
GET /api/runtime/config
PUT /api/runtime/config
POST /api/remote/test-connection
GET /api/system/metrics
```

The host profile contains:

```text
machine info
CPU/RAM/disk
GPU/CUDA info
model availability
dataset availability
remote server status
capability flags
warnings
recommendations
```

The UI displays this information in the Host/System page.

Full details are defined in:

```text
docs/host_detection_spec.md
```

---

## 14. API Architecture

The backend API is grouped by domain.

## 14.1 System APIs

```text
GET /api/health
GET /api/host/profile
POST /api/host/detect
GET /api/system/metrics
GET /api/runtime/config
PUT /api/runtime/config
```

## 14.2 Inspection APIs

```text
GET  /api/models
POST /api/inspect
GET  /api/inspections/{id}
GET  /api/inspections/{id}/report
```

## 14.3 Review APIs

```text
GET   /api/review-queue
POST  /api/reviews
GET   /api/reviews/{id}
PATCH /api/reviews/{id}
```

## 14.4 Dataset APIs

```text
GET  /api/datasets
GET  /api/datasets/{id}
POST /api/datasets/audit
POST /api/datasets/build
```

## 14.5 Training APIs

```text
POST /api/training/jobs
GET  /api/training/jobs
GET  /api/training/jobs/{id}
GET  /api/training/jobs/{id}/logs
POST /api/training/jobs/{id}/stop
```

## 14.6 Experiment APIs

```text
GET /api/experiments
GET /api/experiments/compare
GET /api/experiments/{id}
```

## 14.7 Model Registry APIs

```text
GET  /api/models
GET  /api/models/{id}
POST /api/models/promote
POST /api/models/deploy
POST /api/models/rollback
```

---

## 15. Frontend Architecture

The frontend evolves from the current operator dashboard into a combined desktop/web app.

## 15.1 Current Foundation

```text
React 19
TanStack Router / Start
Tailwind CSS v4
shadcn/ui
FastAPI backend
SVG overlay rendering
```

## 15.2 Target UI Modules

```text
Inspection
Review
Datasets
Training
Experiments
Models
Deployment
Settings
Host / System
```

## 15.3 Frontend Principles

1. API base URL must be configurable.
2. TypeScript types should be generated from FastAPI OpenAPI.
3. UI must not hardcode model paths.
4. UI must show model versions.
5. UI must show host/device status.
6. UI must support operator feedback.
7. UI must display suppressed detections for auditability.
8. UI must support local and remote backend modes.

## 15.4 Recommended Refactor Priorities

```text
replace hardcoded API_BASE
rename mockPipeline to pipelineClient or runPipeline
generate API types from OpenAPI
add review/feedback actions
add host status page
add settings page
prune unused UI primitives
improve accessibility
```

---

## 16. Desktop App Strategy

The first version should run as a local web app:

```text
FastAPI backend on localhost
React frontend on localhost
```

After stabilization, package it as a desktop app using:

```text
Tauri
or
Electron
```

Recommendation:

```text
Use Tauri if lightweight packaging is preferred.
Use Electron if broader compatibility and simpler web runtime packaging are preferred.
```

The desktop app should manage:

```text
local backend lifecycle
remote backend configuration
host detection display
operator inspection
engineer tools
```

Training should run through a backend worker, not directly inside the UI process.

---

## 17. Repository Layout Target

Proposed standardized layout:

```text
car_defect_detection/
│
├── app/
│   ├── frontend/
│   └── desktop/
│
├── backend/
│   ├── api/
│   ├── core/
│   ├── services/
│   ├── workers/
│   └── schemas/
│
├── src/
│   └── cardefect/
│       ├── common/
│       ├── host/
│       ├── stage1/
│       ├── stage2/
│       ├── stage3/
│       ├── stage4/
│       ├── pipelines/
│       ├── datasets/
│       ├── evaluation/
│       └── registry/
│
├── configs/
│   ├── runtime/
│   ├── stage1/
│   ├── stage2/
│   ├── stage3/
│   ├── stage4/
│   ├── inference/
│   └── pipeline/
│
├── data/
│   ├── raw/
│   ├── quarantine/
│   ├── curated/
│   ├── released/
│   └── manifests/
│
├── model_registry/
│
├── experiments/
│
├── reports/
│
├── tests/
│
├── docs/
│
└── archive/
    └── pre_standardization/
```

Migration should be incremental.

Old experiments should be archived, not deleted immediately.

---

## 18. Configuration Architecture

Configuration is separated into:

```text
runtime config
inference config
training config
dataset config
deployment config
```

Example runtime config:

```yaml
runtime:
  mode: auto

local:
  inference_device: auto
  training_device: auto
  allow_cpu_inference: true
  allow_cpu_training: false

remote:
  enabled: false
  base_url: ""
  api_token_env: CARDEFECT_REMOTE_TOKEN
  timeout_seconds: 10

thresholds:
  min_training_vram_gb: 8
  min_inference_vram_gb: 4
  min_free_disk_gb: 20

paths:
  model_registry: model_registry
  datasets: data/released
  mlflow: mlruns
  logs: experiments/logs
```

Secrets must not be stored in tracked config files.

---

## 19. Observability and Auditing

Every inspection should record:

```text
image ID
timestamp
model versions
runtime mode
execution host
inference preset
latency
result summary
operator feedback
```

Every training job should record:

```text
stage
dataset version
config hash
git commit
base model
device
host
metrics
artifacts
MLflow run ID
```

Every deployment should record:

```text
model version
approved_by
deployed_at
deployment_target
rollback_target
```

---

## 20. Security Architecture

1. Local backend should bind to `127.0.0.1` by default.
2. Remote backend should require authentication.
3. API tokens must be stored in environment variables or secure storage.
4. Secrets must not appear in frontend code or logs.
5. Dataset access should be restricted to approved paths.
6. Operator feedback should be stored with traceability.
7. Deployment should require human approval.
8. Host detection must not upload images or sensitive data.

---

## 21. Known Constraints and Limitations

### 21.1 Rare classes remain difficult

```text
corrosion
disjoint_part
```

These classes have limited training examples.

Mitigations:

```text
SAHI native-resolution inference
Stage 1 rescue
operator review
data flywheel
```

### 21.2 Close-up images can weaken panel context

Stage 3 was trained mostly on whole/side car views.

On extreme close-ups, the system may fall back to:

```text
Boundary/Trim
```

This is safe behavior, not a silent failure.

### 21.3 Stage 1 can produce false positives

Possible false positives:

```text
tree
wall
shadow
reflection
tire texture
background objects
```

Mitigations:

```text
Stage 3 car context filtering
tire suppression
threshold calibration
operator review
```

### 21.4 Binary Stage 1 cannot classify defects

Stage 1 can improve recall, but it cannot replace Stage 2 when the operator needs defect type.

Unmatched Stage 1 anomalies should be reported as:

```text
unclassified_anomaly
```

---

## 22. Future Extensions

Possible future extensions:

1. Guided tiling using Stage 1 saliency.
2. Fully automatic retraining triggers.
3. Multi-user authentication.
4. Centralized Postgres database.
5. Model drift monitoring.
6. Automatic rollback based on operator rejection rate.
7. ONNX/TensorRT optimization for local desktop inference.
8. Mobile/tablet review interface.
9. PDF export for factory inspection reports.
10. Active learning queue prioritized by rare classes.

---

## 23. Architecture Principles Summary

1. Stage 1 provides recall.
2. Stage 2 provides defect class.
3. Stage 3 provides spatial context.
4. Stage 4 provides fusion and reporting.
5. Operator feedback drives improvement.
6. Training can be automated, deployment must be approved.
7. Local and remote execution must be configurable.
8. Host detection must be automatic but overridable.
9. The UI should be a thin client over a stable backend.
10. Champion models must be frozen and protected during refactoring.
```
