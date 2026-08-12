# Car Defect Detection — Master Plan

Version: 0.1
Date: 2026-08-12
Status: Draft for approval

## 1. Goal

Build a standardized, company-ready desktop and backend system for:

1. Operator inspection.
2. Engineer training and experimentation.
3. Local or remote inference.
4. Local or remote training.
5. Automatic host detection.
6. Continuous model improvement through operator feedback.
7. Safe, human-approved model deployment.

The system must support:

- Stage 1: Binary salient defect / anomaly pre-screening.
- Stage 2: 7-class defect instance segmentation.
- Stage 3: 21-class panel/component segmentation.
- Stage 4: Spatial fusion, panel assignment, DSI, factory report.

---

## 2. Product Vision

One application with two functional modes:

### Operator Mode

For daily factory inspection:

```text
Load image
Run inspection
View defects
View panels
View severity
Review detections
Confirm / reject / reclassify
Export report
```

### Engineer Mode

For model improvement:

```text
Inspect datasets
Audit leakage
Launch training
Monitor experiments
Compare models
Promote champion
Deploy model
Rollback model
```

For the first version, Operator Mode and Engineer Mode will be combined into one app for easier debugging.

Later, they can be separated by role:

```text
Operator
Engineer
Supervisor / Admin
```

---

## 3. Core Principles

### 3.1 Standardize before building more UI

The current workspace contains valuable research artifacts, but it is not yet production-standard.

Before adding many new features, we must stabilize:

```text
code layout
configs
datasets
model registry
evaluation
API contracts
documentation
```

### 3.2 Desktop app is a thin client

The desktop UI should not directly manage random files or old experiments.

It should communicate with a standardized backend API.

```text
Desktop UI
    ↓
FastAPI backend
    ↓
Pipeline engine
    ↓
Models / datasets / MLflow / registry
```

### 3.3 Local and remote execution must be first-class

The company desktop may have a built-in GPU.

The system must support:

```text
fully local execution
fully remote execution
hybrid execution
```

Example:

```text
Inference: local desktop GPU
Training: remote GPU server
```

### 3.4 Automatic detection, manual override

The app should automatically detect:

```text
local GPU
CUDA availability
VRAM
disk space
model availability
remote server availability
```

But the user must always be able to override the automatic choice.

### 3.5 Automated training, human-approved deployment

The system can automate:

```text
dataset audit
training
validation
testing
comparison
candidate generation
```

But deployment should require human approval.

```text
Automated pipeline, human-gated release.
```

### 3.6 Operator feedback drives model improvement

The long-term improvement loop is:

```text
Production inference
    ↓
Operator review
    ↓
Confirmed defects / rejected false positives
    ↓
Dataset update
    ↓
Leakage audit
    ↓
Retraining
    ↓
Evaluation gates
    ↓
Human approval
    ↓
Deployment
```

---

## 4. Target Architecture

```text
┌────────────────────────────────────────┐
│          Desktop / Web UI              │
│  Operator + Engineer combined mode     │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│             FastAPI Backend            │
│                                        │
│  Host detection                        │
│  Runtime settings                      │
│  Inference API                         │
│  Review API                            │
│  Dataset API                           │
│  Training API                          │
│  Model registry API                    │
└───────┬───────────────────┬────────────┘
        │                   │
        ▼                   ▼
┌───────────────┐   ┌────────────────────┐
│ Local Backend │   │ Remote Backend     │
│ GPU worker    │   │ GPU server         │
└───────┬───────┘   └─────────┬──────────┘
        │                     │
        ▼                     ▼
┌────────────────────────────────────────┐
│             Pipeline Engine            │
│                                        │
│  Stage 1 binary anomaly                │
│  Stage 2 7-class defect                │
│  Stage 3 panel segmentation            │
│  Stage 4 fusion / IoD / DSI            │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│          Experiment / Registry         │
│                                        │
│  MLflow tracking                       │
│  Dataset manifests                     │
│  Model registry                        │
│  Evaluation reports                    │
│  Deployment manifests                  │
└────────────────────────────────────────┘
```

---

## 5. Product Modules

## 5.1 Inspection Module

Purpose:

```text
Run full pipeline on a car image.
```

Inputs:

```text
image
runtime preset
model versions
inference settings
```

Outputs:

```text
defects
panels
unclassified anomalies
suppressed detections
DSI
PASS/FAIL verdict
report JSON
overlay image
crops
```

Important features:

- Stage 3 panel context.
- Stage 2 defect detection.
- Stage 1 anomaly rescue.
- Tire suppression.
- Non-car suppression.
- Unclassified anomaly display.
- Model version display.

---

## 5.2 Review Module

Purpose:

```text
Capture operator feedback.
```

Operator actions:

```text
Confirm defect
Reject false positive
Reclassify defect
Mark unclear
Add missing defect
```

Stored feedback:

```text
inspection_id
image_id
detection_id
model_version
predicted_class
predicted_panel
confidence
operator_decision
corrected_class
corrected_polygon
timestamp
```

This becomes the data flywheel.

---

## 5.3 Dataset Module

Purpose:

```text
Manage dataset versions and audits.
```

Features:

```text
list dataset versions
show class distribution
show image count
show split info
run leakage audit
show duplicate image audit
show annotation quality report
create new dataset version
```

Important dataset audit rules:

- Split by source image, not by dataset name.
- Check filename overlap.
- Check exact file hash overlap.
- Optionally check perceptual image hash overlap.
- Ensure test set is never used for training.
- Record dataset manifest.

---

## 5.4 Training Module

Purpose:

```text
Train Stage 1, Stage 2, and Stage 3 models.
```

Features:

```text
select stage
select dataset version
select config
select device
select local or remote execution
start training
stop training
view logs
view metrics
view GPU usage
view MLflow run
```

Training job metadata:

```text
job_id
stage
dataset_version
config_hash
git_commit
base_model
execution_host
device
start_time
end_time
status
final_metrics
artifacts
```

---

## 5.5 Experiment Module

Purpose:

```text
Compare training runs.
```

Metrics to compare:

Stage 1:

```text
recall
false positive rate
mIoU
hairline scratch recall
tire false positives
non-car false positives
latency
```

Stage 2:

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

Stage 3:

```text
Mask mAP50
Mask mAP50-95
per-class panel mAP50
wheel/tire mask quality
close-up degradation behavior
generalization gap
```

---

## 5.6 Model Registry Module

Purpose:

```text
Manage model versions.
```

Model statuses:

```text
candidate
champion
deployed
archived
rejected
```

Each model version should store:

```text
stage
model_name
version
weights path
config hash
dataset version
training run id
metrics
evaluation report
model card
created_at
promoted_at
deployed_at
```

---

## 5.7 Deployment Module

Purpose:

```text
Safely promote and deploy models.
```

Deployment flow:

```text
candidate model
    ↓
automatic evaluation
    ↓
comparison against champion
    ↓
promotion gates
    ↓
human approval
    ↓
deploy
    ↓
monitor
```

Rollback must be supported.

---

## 5.8 Settings Module

Purpose:

```text
Configure runtime, devices, and endpoints.
```

Settings include:

```text
runtime mode
local inference device
local training device
remote server URL
remote API token
model paths
dataset paths
MLflow location
database location
debug mode
```

---

## 5.9 Host / System Module

Purpose:

```text
Show machine capability.
```

Displayed information:

```text
OS
GPU
CUDA
VRAM
CPU
RAM
disk space
local model availability
remote server status
recommended execution mode
warnings
```

This module is defined in detail in:

```text
docs/host_detection_spec.md
```

---

## 6. Standardized Repository Layout

Proposed target layout:

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

Exact migration will be done step by step.

We will not delete old experiments immediately.

Old files should be moved to:

```text
archive/pre_standardization/
```

and listed in:

```text
archive/INVENTORY.md
```

---

## 7. Pipeline Standardization

## 7.1 Inference pipeline

Recommended production inference order:

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

Stage 4 fusion rules:

```text
1. Suppress detections mostly on tire.
2. Suppress anomalies outside car context.
3. Match Stage 1 anomalies with Stage 2 detections.
4. If matched, keep Stage 2 class.
5. If unmatched but on car body, create unclassified_anomaly.
6. Assign panel using IoD.
7. Compute DSI.
8. Output JSON, overlay, crops.
```

Important locked rules from prior work:

- Stage 2 champion uses 1024px.
- SAHI should use native 1024 slices.
- Mask-IOS NMS is required for thin defects.
- Stage 3 provides tire masks: `Front-wheel`, `Back-wheel`.
- `Boundary/Trim` is a safe fallback for low-context inputs.

---

## 7.2 Training pipeline

Each stage needs standard commands.

Examples:

```bash
cardefect audit dataset --stage stage2
cardefect train stage1 --config configs/stage1/train/sod_v2.yaml
cardefect train stage2 --config configs/stage2/train/head_warmup_v1.yaml
cardefect train stage3 --config configs/stage3/train/panel_baseline_v1.yaml
cardefect evaluate stage2 --model stage2:v1.0.0
cardefect compare --stage stage2 --runs run_001,run_002
cardefect promote stage2 --run run_003
cardefect deploy stage2 --model stage2:v1.1.0
```

These commands will be wrapped by the backend API and UI.

---

## 8. Dataset Governance

Every dataset version must have:

```text
manifest.json
class_map.json
split.json
annotation_rules.md
quality_report.json
leakage_audit.json
```

Manifest fields:

```text
dataset_id
stage
version
created_at
source_datasets
image_count
instance_count
class_distribution
size_distribution
included_images
excluded_images
known_issues
hash_method
split_method
```

Dataset status:

```text
raw
quarantine
curated
released
archived
```

Only `released` datasets should be used for official training.

---

## 9. Model Improvement Loop

```text
1. Model runs in production.
2. Operator reviews detections.
3. Confirmed rare defects become hard positives.
4. Rejected false positives become hard negatives.
5. Unclassified Stage 1 anomalies become labeling candidates.
6. Reviewed examples enter dataset builder.
7. Dataset audit checks leakage and class balance.
8. Training job runs.
9. Evaluation compares candidate to champion.
10. Human approves promotion.
11. Model is deployed.
12. Monitoring continues.
```

This loop should be semi-automatic first.

Fully automatic deployment is not recommended initially.

---

## 10. Evaluation Gates

A candidate model should not be promoted unless it passes gates.

Example gates:

```yaml
promotion_gates:
  stage2:
    require_clean_leakage_audit: true
    min_test_mask_map50: champion - 0.005
    max_rare_class_recall_regression: 0.05
    max_false_positives_per_image: 1.5
    max_latency_ms: 1500
    require_visual_audit: true
    require_human_approval: true
```

Exact thresholds will be tuned.

---

## 11. Desktop App Strategy

## 11.1 First version: local web app

Before packaging as a desktop installer, run the system as:

```text
FastAPI backend on localhost
React frontend on localhost
```

This is easier to debug.

## 11.2 Later: desktop wrapper

After stabilization, wrap the app using one of:

```text
Tauri
Electron
```

Recommendation:

- Use Tauri if lightweight native packaging is preferred.
- Use Electron if compatibility and ecosystem simplicity are more important.

Final choice can be decided after checking company machine policies.

---

## 12. Role Plan

For now:

```text
Combined mode for debugging.
```

Later:

```text
Operator role
Engineer role
Supervisor role
```

Even in combined mode, the backend should already separate permissions logically.

Example:

```text
/operator endpoints
/engineer endpoints
/admin endpoints
```

Authentication can be added later.

---

## 13. Phased Roadmap

## Phase 0 — Planning and Confirmation

Goals:

```text
Approve master plan.
Approve host detection spec.
Confirm target hardware.
Confirm local/remote requirements.
```

Deliverables:

```text
docs/master_plan.md
docs/host_detection_spec.md
```

---

## Phase 1 — Freeze Current Champions

Goals:

```text
Protect current working models.
Document champion configs.
Prevent cleanup from breaking production.
```

Deliverables:

```text
docs/champion_manifest.md
```

Champions to freeze:

- Stage 1 selected model.
- Stage 2 Model 5 Stage 1 Extended 7-class.
- Stage 3 panel segmenter baseline.
- Stage 4 spatial context mapper config.
- SAHI production config.

---

## Phase 2 — Workspace Cleanup

Goals:

```text
Archive old experiments.
Fix stale paths.
Fix dependencies.
Fix secrets.
Create README.
Create architecture docs.
```

Known cleanup items from workspace report:

- Stale Makefile targets.
- Broken DVC paths.
- Missing `shapely` dependency.
- Missing `sam2` dependency if kept.
- Hardcoded MinIO password.
- Duplicate notebooks.
- Superseded Stage 2 configs.
- Trailing-space report directories.
- Empty README.
- CI test path mismatch.
- Cross-stage import coupling.

Deliverables:

```text
archive/pre_standardization/
archive/INVENTORY.md
README.md
docs/architecture.md
```

---

## Phase 3 — Backend Foundation

Goals:

```text
Create clean FastAPI backend.
Create host detection module.
Create runtime settings.
Create health endpoint.
Create local/remote execution adapter.
```

Deliverables:

```text
backend/api/health.py
backend/api/host.py
backend/api/runtime.py
src/cardefect/host/profile.py
src/cardefect/host/decision.py
```

---

## Phase 4 — Combined UI Shell

Goals:

```text
Create one app with tabs.
Integrate current production dashboard.
Replace hardcoded API URL.
Add host/status page.
Add settings page.
```

Tabs:

```text
Inspection
Review
Datasets
Training
Experiments
Models
Deployment
Settings
Host
```

Deliverables:

```text
app shell
host status page
runtime settings page
```

---

## Phase 5 — Inspection MVP

Goals:

```text
Run full inference pipeline from UI.
Show panels, defects, anomalies, suppressed detections.
Export report.
```

Deliverables:

```text
/api/inspect
Stage 4 fusion integration
UI overlay updates
report export
```

---

## Phase 6 — Operator Review Loop

Goals:

```text
Store operator feedback.
Create review queue.
Export hard examples.
```

Deliverables:

```text
review database schema
/api/reviews
review queue UI
hard example export
```

---

## Phase 7 — Training and Experiment Module

Goals:

```text
Launch training from UI.
Monitor jobs.
Compare experiments.
Use MLflow results.
```

Deliverables:

```text
/api/training/jobs
training worker
experiment comparison UI
```

---

## Phase 8 — Model Registry and Deployment

Goals:

```text
Promote champion models.
Deploy with approval.
Support rollback.
```

Deliverables:

```text
model registry UI
promotion gates
deployment manifest
rollback support
```

---

## Phase 9 — Packaging and Company Deployment

Goals:

```text
Package desktop app.
Create installer.
Create local service launcher.
Create company deployment guide.
```

Deliverables:

```text
desktop build
installer
deployment docs
operator guide
engineer guide
```

---

## 14. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Building UI around messy workspace | Standardize backend first |
| Local/remote path differences | Use config and host detection |
| GPU availability differences | Auto-detect and allow override |
| Dataset leakage | Image-level leakage audit |
| False positives from Stage 1 | Stage 3 context filtering and operator review |
| Tire false positives | Stage 3 wheel/tire suppression |
| Training job instability | Job queue and logs |
| Accidental bad deployment | Human approval gates |
| Old experiments breaking new code | Archive, not delete |
| Secrets in repo | Move to `.env` and secret handling |

---

## 15. Immediate Next Steps

1. Approve this master plan.
2. Approve host detection specification.
3. Freeze current champion models.
4. Audit workspace and create archive inventory.
5. Build backend health/host endpoint.
6. Build UI shell with Host/Settings page.
7. Integrate existing inspection dashboard.
```
