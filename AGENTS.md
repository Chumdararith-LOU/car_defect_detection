# AGENTS.md — car_defect_detection

## 0. OpenCode Initialization Rules

- Read this entire file before proposing or applying any change.
- If any rule here conflicts with an automatic refactor, shortcut, or code generation habit, follow this file.
- If information is missing, stop and ask. Do not guess.
- Do not assume file contents, paths, weights, dataset locations, server state, or installed packages.
- Prefer small, verifiable steps over large rewrites.

---

## 1. Project Mission

This repository implements a multi-stage AI pipeline for automotive exterior defect detection and industrial quality inspection.

The pipeline has multiple specialized models:

- Stage 1: Binary / salient pre-screening model.
- Stage 2: Multi-class defect instance segmentation model.
- Stage 3: Panel/component segmentation model for spatial context mapping.
- Later integration: Map defects to vehicle panels using Intersection over Defect, not normal IoU.

The final system should output panel-aware diagnostics such as:

- scratch on Front-door
- dent on Hood
- corrosion on Quarter-panel

---

## 2. Non-Negotiable Workflow Rules

### 2.1 Step-by-step execution

- Move one step at a time.
- Do not advance to the next phase until the current step is verified.
- When giving instructions, provide:
  - the command or edit,
  - expected output,
  - what to paste back if verification is needed.

### 2.2 Pinpoint edits only

For existing files:

- Never tell the user to replace the entire file.
- Never output a full existing file as a replacement.
- Provide:
  - file path,
  - exact location or surrounding context,
  - original snippet,
  - replacement snippet.

If the exact file content is unknown:

- Ask for a targeted command such as grep, nl, sed, or cat.
- Do not guess line numbers or code structure.

For new files:

- It is acceptable to provide the full new file content.
- Always state the full file path.

### 2.3 Git discipline

After every meaningful change, provide a short informal commit message.

Examples:

- feat(stage3): add panel segmenter baseline config
- fix(stage3): correct dataset yaml path
- docs: add agent rules

Rules:

- Do not commit large datasets.
- Do not commit model weights unless explicitly instructed.
- Do not commit generated images, labels, caches, or run outputs.
- Respect existing pre-commit hooks.
- If a pre-commit hook fails, diagnose the failing file before bypassing anything.
- Never use destructive Git commands without explicit approval.

### 2.4 No assumptions

Do not assume:

- file existence,
- folder structure,
- server paths,
- local paths,
- dataset location,
- checkpoint location,
- GPU availability,
- installed Python packages,
- OpenCode configuration format.

If unsure, ask for a verification command or file snippet.

### 2.5 Environment awareness

Development flow:

- Code is written on the MacBook.
- Code is committed and pushed to GitHub.
- Training is executed on the Ubuntu server with an RTX 4090.

Therefore:

- Do not put MacBook-only absolute paths into training configs unless explicitly for local debugging.
- Server paths must be verified before training.
- Dataset artifacts may need to be transferred separately with rsync, scp, or DVC.
- Generated datasets under data/processed should generally not be committed to Git.

Known server repo path from previous Stage 2 configs:

/home/lamacpp/Documents/car_defect_detection

This path is likely correct but must still be verified before use.

---

## 3. Repository Context

### 3.1 Stage 2 is complete

The Stage 2 defect segmentation champion is:

runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended

Best weights:

runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt

Stage 2 production defect classes (canonical taxonomy):

0 dent (panel deformation)
1 scratch (surface abrasion)
2 crack (fracture line)
3 glass_shatter (broken glass)
4 broken_part (damaged-but-attached component incl. lamps/mirrors/trim — canonical; models may emit legacy "broken_lamp", alias at boundary)
5 corrosion (oxidation/rust)
6 disjoint_part (detached/missing part ONLY)

Governance: models use DIFFERENT class orders (alphabetical vs canonical
families). Always resolve classes by NAME (name-keyed rules,
CANONICAL_ALIASES), never by raw id.

Important Stage 2 lessons:

- Generic COCO weights were not enough for defect segmentation.
- Resume-and-Adapt transfer from Model 1 was essential.
- Merging dent and deform improved performance.
- Head-only warmup outperformed full fine-tuning on the small defect dataset.
- Multi-scale training caused instability and was disabled.
- Stable augmentations were mosaic 0.0, scale 0.3, degrees 15.0, multi_scale false.

Do not reuse Stage 2 defect weights for Stage 3 panel segmentation.

---

## 4. Stage 3 Context

Stage 3 trains a separate panel/component segmentation model.

This model is called M_panel.

Its purpose:

- Segment vehicle panels/components.
- Provide global panel masks.
- Allow later mapping of defects to panels using IoD.

Stage 3 dataset:

Dataset A: Car damages dataset

Converted YOLO dataset output:

data/processed/stage3/car_damages_panel

Dataset YAML:

data/processed/stage3/car_damages_panel/car_damages_panel.yaml

Split:

train: 798
val: 100
test: 100
seed: 42

Panel classes:

0 Quarter-panel
1 Front-wheel
2 Back-window
3 Trunk
4 Front-door
5 Rocker-panel
6 Grille
7 Windshield
8 Front-window
9 Back-door
10 Headlight
11 Back-wheel
12 Back-windshield
13 Hood
14 Fender
15 Tail-light
16 License-plate
17 Front-bumper
18 Back-bumper
19 Mirror
20 Roof

Stage 3 training baseline:

- Use fresh pretrained segmentation weights, preferably yolo26m-seg.pt.
- Do not use Stage 2 defect checkpoints.
- Do not use Model 1 remapped checkpoints.
- Do not enable differential learning rate unless explicitly running an ablation.
- Do not freeze the backbone unless explicitly running an ablation.
- Baseline should train the full model with differential_lr false and freeze 0.

Stage 3 custom trainer:

src/stage3/train/train.py

Stage 3 baseline config:

configs/train/stage3/panel_segmenter_baseline.yaml

Custom trainer config keys include:

task
model_preset
project_name
run_name
dataset_config
epochs
imgsz
batch_size
patience
device
workers
amp
freeze
lr0
lrf
optimizer
multi_scale
differential_lr
augmentations

---

## 5. Stage 3 Spatial Mapping Rules

When implementing panel assignment later:

- Use Intersection over Defect, IoD, not standard IoU.
- IoD formula: Area(defect intersect panel) / Area(defect).
- Assign defect to argmax panel IoD.
- Use containment threshold theta_containment = 0.50.
- If max IoD is below threshold, label as Boundary/Trim.
- Damage Severity Index: DSI percent = Area(defect) / Area(panel) * 100.

---

## 6. Data Rules

### 6.1 Raw data

Do not modify:

data/raw/archive/Car damages dataset

Treat raw archives as read-only.

### 6.2 Processed data

Generated datasets should be placed under:

data/processed/

Stage 3 generated dataset:

data/processed/stage3/car_damages_panel

Do not commit generated datasets to Git unless explicitly using DVC.

### 6.3 Dataset YAML paths

Dataset YAML files must be portable to the training server.

Do not leave MacBook-only paths such as /Users/macbook/... inside training dataset YAMLs unless explicitly debugging locally.

Server dataset path should be verified, but the intended Stage 3 dataset location is:

/home/lamacpp/Documents/car_defect_detection/data/processed/stage3/car_damages_panel

---

## 7. Training Rules

Before launching training:

1. Verify the correct branch.
2. Verify the config file.
3. Verify the dataset YAML.
4. Verify the dataset exists on the server.
5. Verify image and label counts.
6. Verify the model weights path.
7. If possible, perform a dry-run or short smoke test.
8. Get explicit user approval before launching long training jobs.

Default Stage 3 baseline direction:

task: segment
differential_lr: false
freeze: 0
multi_scale: false
mosaic: 0.0
mixup: 0.0
erasing: 0.0

Prefer mild augmentations for panel segmentation:

degrees: 10.0
scale: 0.3
fliplr: 0.5
perspective: 0.0005

---

## 8. Code Style Rules

- Prefer clear, minimal changes.
- Do not refactor unrelated code while fixing a specific issue.
- Do not introduce new dependencies without asking.
- Use quoted paths when paths contain spaces.
- Use pathlib.Path for Python path handling where practical.
- Use deterministic seeds for dataset splits and experiments.
- Add comments only when they explain why, not merely what.
- Avoid huge notebook outputs in Git-tracked notebooks when possible.

---

## 9. Agent Response Template

When asked to make a change, respond using this structure:

1. Understanding
   - Restate the task briefly.

2. Missing Information
   - List anything unknown that blocks safe progress.

3. Plan
   - Provide the smallest safe next step.

4. Exact Edit or Command
   - For existing files: pinpoint edit only.
   - For new files: full path and content.

5. Verification
   - Provide the command to verify the change.

6. Git Commit Message
   - Provide a short commit message.

---

## 10. Prohibited Actions

Do not:

- Replace entire existing files.
- Guess paths or file contents.
- Commit datasets, weights, or large binary files to Git.
- Use Stage 2 defect checkpoints for Stage 3 panel segmentation.
- Enable differential LR or freeze unless explicitly requested.
- Launch long training jobs without confirmation.
- Modify raw data.
- Bypass pre-commit hooks without diagnosis.
- Delete user data or run folders without explicit approval.
- Assume the MacBook and server paths are identical.
