# 📋 Consolidated Project Report — Car Defect Detection System

**Project:** Car Defect Detection Platform
**Date:** Monday, August 17, 2026
**Backend Repo:** `car_defect_detection` (branch `stage_3`)
**Frontend Repo:** `Application React` (branch `main`)
**Status:** Phases 0–12 Complete | Phase 13 Next

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Stage-by-Stage Technical Breakdown](#3-stage-by-stage-technical-breakdown)
4. [Production Deployment Workflow](#4-production-deployment-workflow)
5. [Supervisor Feedback & Detailed Response](#5-supervisor-feedback--detailed-response)
6. [Draft Reply to Supervisor](#6-draft-reply-to-supervisor)
7. [Leakage Audit Protocol](#7-leakage-audit-protocol)
8. [Revised Development Plan (Post-Supervisor)](#8-revised-development-plan)
9. [Backend API Surface (Complete)](#9-backend-api-surface-complete)
10. [Desktop Application Productionization Plan](#10-desktop-application-productionization-plan)
11. [Training Infrastructure (Detailed)](#11-training-infrastructure)
12. [Phase 12 Session Report — Model Registry & Deployment](#12-phase-12-session-report)
13. [Workspace Cleanup Status](#13-workspace-cleanup-status)
14. [Full Project Status Report](#14-full-project-status-report)
15. [Git Commit History](#15-git-commit-history)
16. [Critical Outstanding Issues & Debt](#16-critical-outstanding-issues--debt)
17. [Next Steps & Roadmap](#17-next-steps--roadmap)

---

## 1. Executive Summary

This document consolidates all planning, supervisor feedback, technical reports, session work logs, and deployment notes for the **Car Defect Detection System** — a 4-stage AI pipeline designed for factory-floor automotive exterior inspection with operator-in-the-loop review, continuous model improvement, and human-approved deployment.

### Core Design Philosophy

The system is built as a **team of specialists**, not one monolithic model. Each stage compensates for another's weakness:

| Stage | Nickname | Role | Model | Resolution | Key Metric |
|-------|----------|------|-------|-----------|------------|
| Stage 1 | The Gatekeeper | Binary anomaly pre-screener (recall-first) | YOLO26m-sem, Focal Loss | 640px tiled | 95.2% recall, 50% FPR, ~34ms |
| Stage 2 | The Specialist | 7-class defect segmenter (classification) | YOLO26m-seg, SAHI, Resume-and-Adapt | 1024px | Test Mask mAP50 = 0.650 |
| Stage 3 | The Mapmaker | 21-class panel/component segmenter (context) | YOLO26m-seg, AdamW | 640px | Val Mask mAP50 = 0.885 |
| Stage 4 | The Judge | Spatial fusion & decision logic (no ML) | Shapely geometry | N/A | Pure Python rules |

### Key Principles

- **Recall over precision** at Stage 1; classification at Stage 2; context at Stage 3; judgment at Stage 4.
- **Operator-in-the-loop**: False positives are acceptable; missed defects are not.
- **Human-approved deployment**: Training can be automated; promotion requires sign-off.
- **Data flywheel**: Operator corrections feed back into retraining.
- **Archive first**: Never delete champion models or experiments.

### Repository Layout

| Repo | Path | Purpose |
|------|------|---------|
| `car_defect_detection` | `/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection` | ML pipeline, FastAPI backend, models, configs, datasets |
| `Application React` | `/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/Application React` | React frontend UI, TanStack Router, shadcn components |

### Key Configuration

| Setting | Value |
|---------|-------|
| Backend port | `8010` (port 8000 reserved for user's existing services) |
| Frontend env var | `VITE_API_BASE=http://localhost:8010` |
| Python env | `car_defect` conda, Python 3.10 |
| Champion weights | Symlinked into `backend/models/stage{1,2,3}/` |
| Database | SQLite at `backend/data/reviews.db`, `backend/data/model_registry.db`, `backend/data/training_jobs.db` |
| Desktop packaging | Tauri (planned, Phase 13) |
| MLflow tracking | `http://192.168.50.17:5000` (remote Ubuntu) + local `./mlruns` |
| Frontend dev server | `bun run dev` (port 8080) |
| Backend run | `cd backend && conda activate car_defect && uvicorn main:app --reload --port 8010` |
| OS | macOS, Apple Silicon M5 |

---

## 2. System Architecture

### 2.1 High-Level Pipeline Diagram

```text
Input Image
    │
    ▼
┌─────────────────────────────────────────────────┐
│  STAGE 3 — Panel Segmenter (640px)              │
│  "Where is the car and its parts?"              │
│  Output: car_context_mask + tire_mask           │
└────────────────────┬────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ STAGE 1  │  │   STAGE 2    │  │  (parallel)  │
│ Binary   │  │  7-Class     │  │              │
│ SOD      │  │  Defect Seg  │  │              │
│ (Tiled)  │  │  (SAHI 1024) │  │              │
└────┬─────┘  └──────┬───────┘  └──────────────┘
     │               │
     ▼               ▼
┌─────────────────────────────────────────────────┐
│  STAGE 4 — Fusion & Filtering Engine            │
│  (Pure Python/Shapely — no neural network)      │
│                                                 │
│  • Suppress tire defects                        │
│  • Suppress non-car anomalies                   │
│  • Match Stage 1 ↔ Stage 2                     │
│  • Rescue unmatched Stage 1 anomalies           │
│  • Assign panels (IoD)                          │
│  • Compute severity (DSI)                       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Final Factory Report JSON & Dashboard UI       │
└─────────────────────────────────────────────────┘
```

### 2.2 Software Stack Architecture

```text
┌─────────────────────────────────────────────────┐
│         React App (Frontend)                     │
│         Tabs: Inspection / Host / Review /       │
│               Datasets / Training / Models /     │
│               Experiments / Settings             │
└──────────────────┬──────────────────────────────┘
                   │  HTTP localhost:8010
                   ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend                          │
│         api/ core/ services/ schemas/            │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         4-Stage ML Pipeline                      │
│         + MLflow + SQLite + Model Registry       │
│         + Training Worker + Candidate Collector  │
└─────────────────────────────────────────────────┘
```

### 2.3 Design Principles Established

| Principle | Rationale |
|-----------|-----------|
| Modular over monolithic | Backend: `api/`, `core/`, `services/`, `schemas/` |
| Operator options by condition/scenario | Don't overwhelm with irrelevant choices |
| SAHI presets belong to pipeline, not model | Model is just weights; pipeline decides slicing |
| Disable with tooltip, don't hide | Transparency for operators |
| Label modes by outcome, not mechanism | "Safety" not "low_threshold_mode" |
| Dynamic model discovery from `/api/models` | No hardcoded paths in frontend |
| Honest UI — no fake placeholders | If it's not built, don't pretend |
| Native Resolution Rule | SAHI at 1024, Stage 3 at 640 |
| Pinned dependencies | ultralytics 8.4.115, sahi 0.12.4, opencv 5.0.0.93 |
| Standard Ultralytics checkpoints | eval-mode APIs only |
| Stage 1 anomaly mask always in payload | Even if PASS, keep raw mask for audit |
| Archive first, never delete | Protects research history and champions |

### 2.4 Workflow Rules (MUST Follow)

| # | Rule | Details |
|---|------|---------|
| 1 | **Step-by-Step** | One verified step at a time; never advance until confirmed working |
| 2 | **Pinpoint Edits Only** | For EXISTING files, give exact "Find / Replace" blocks. Never full rewrites |
| 3 | **New Files** | Full content with exact target path |
| 4 | **Simple Git Commits** | Short informal messages after each verified change |
| 5 | **No Assumptions** | Never guess file contents/paths. If unsure, ask to paste/run |
| 6 | **Environment Awareness** | Paths have spaces ("AI Farm", "Application React") — use quoting |

### 2.5 Frontend Modularity Rules (9 Rules)

| # | Rule | Details |
|---|------|---------|
| 1 | One component per file | Never multiple React components in one file |
| 2 | Feature-folder structure | `src/components/<feature>/` with `index.ts` barrel |
| 3 | Strict layer separation | schema → constants → apiClient → hooks → components → routes |
| 4 | Extract before duplicating | If JSX/logic appears twice, extract it |
| 5 | ~200 lines max per file | Split before delivering |
| 6 | Local `interface Props` | Named exports, PascalCase components, camelCase utils |
| 7 | Tailwind v4 | Never dynamic class names; use full literals, `cn()`, or explicit maps |
| 8 | Delivery format | New files = full content; existing = Find/Replace only |
| 9 | Plan first | Show file breakdown before writing code; wait for approval |

---

## 3. Stage-by-Stage Technical Breakdown

### 3.1 Stage 1 — The Gatekeeper (Recall Above All)

| Attribute | Detail |
|-----------|--------|
| **Model** | YOLO26m semantic segmentation |
| **Input** | 640px tiles, 15% overlap |
| **Loss** | FocalCrossEntropyLoss (γ=2.0) |
| **Champion metrics** | 95.2% recall, 50% FPR, ~34ms inference |
| **Thresholds** | `tau_pixel=0.7`, `tau_anomaly=0.0005` |
| **Dataset** | `sod_tiled` (16,000 images, 2 classes: clean/damage) |
| **Trainer script** | `src/stage1/train/train_sod.py` |
| **Output** | Saliency score + binary anomaly mask |

**Job:** Answer one question: *"Is there ANY possible defect here?"*

- If saliency score < τ_anomaly → `PASS` (car is clean, stop early, ~34ms total)
- If ACTIVE → proceed to Stage 2/3

**How it helps other stages:**
1. **Efficiency valve:** Clean cars never touch expensive Stage 2/3.
2. **Safety net:** Raw binary mask is handed to Stage 4 for rescue logic.

**Accepted weakness:** Fires on trees, walls, reflections (50% FPR). Other stages clean this up.

**Defect visual signatures it must detect (class-agnostic):**

| Defect Type | Visual Signature |
|-------------|-----------------|
| Scratch | Thin line |
| Crack | Branching thin structure |
| Corrosion | Textured patch / discoloration |
| Dent | Shading / surface deformation |
| Broken lamp | Structural component damage |
| Glass shatter | High-frequency shattered texture |
| Disjoint part | Structural gap / misalignment |

**Key training details:**
- Uses **semantic segmentation** (one mask per image), NOT instance segmentation
- Trained with grayscale PNG masks (0=clean, 1=damage)
- 15% overlapping coarse tiling solves Stride-8 dilution problem
- Threshold calibration ensures high recall without excessive false alarms

---

### 3.2 Stage 2 — The Specialist (Classification)

| Attribute | Detail |
|-----------|--------|
| **Model** | YOLO26m-seg "Model 5" (Resume-and-Adapt) |
| **Input** | 1024px (Direct or SAHI slices, 15% overlap) |
| **Loss** | ScaledFocalBCEWithLogitsLoss (γ=2.0, α=0.50) |
| **Champion metrics** | Test Mask mAP50 = 0.650 |
| **Training** | Frozen backbone (`freeze: 23`) + extended head warmup |
| **Base model** | `model1_remapped_7class_init.pt` |
| **Dataset** | `yolo_seg_clean_2200_7cls` (2,019 images, 7 classes) |
| **Trainer script** | `src/stage2/train/train.py` |
| **Output** | Classified defect masks (7 classes) |
| **Multi-scale** | Disabled (prevent OOM) |
| **Mosaic** | 0.0 (stability) |

**7 Defect Classes:**
`dent`, `scratch`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion`, `disjoint_part`

**How it helps other stages:** Only stage that provides *class labels*. Its detections are the candidates Stage 4 validates, assigns to panels, or suppresses.

**Key training details:**
- Uses **instance segmentation** (YOLO polygons per detection)
- **Resume-and-Adapt transfer**: frozen backbone from Model 1, freshly trained 7-class head
- `freeze: 23` is critical — freezes backbone, trains only head
- Optionally applies **differential learning rate** (backbone 10× slower than head)
- imgsz locked at 1024px (never lower)
- Runs Direct (fast, conf=0.15) or SAHI (1024 slices, Mask-IOS NMS) for micro-defect recovery

**Why 1024px matters:**
```text
Direct inference at global scale:  micro-corrosion probability ≈ 0.04
Native-resolution crop / SAHI:     probability > 0.25
```

---

### 3.3 Stage 3 — The Mapmaker (Spatial Context)

| Attribute | Detail |
|-----------|--------|
| **Model** | YOLO26m-seg |
| **Input** | 640px |
| **Classes** | 21 panel/component classes |
| **Champion metrics** | Val Mask mAP50 = 0.885 |
| **Optimizer** | AdamW (not SGD) |
| **freeze** | 0 (train everything from scratch) |
| **Dataset** | `car_damages_panel` (998 images, 21 classes) |
| **Trainer script** | `src/stage3/train/train.py` |
| **Output** | Panel polygons (incl. wheels) |
| **Differential LR** | false |

**Job:** Segment the car's components. Never looks at defects.

**Critical outputs for Stage 4:**
- `car_context_mask` = union of ALL body panels (morphologically closed, fills gaps like lamps/trim) → "where the car is"
- `tire_mask` = union of Front-wheel + Back-wheel → "where tire texture lives"

**Key training details:**
- Uses **instance segmentation** (YOLO polygons)
- Trains from scratch (`freeze: 0`, AdamW optimizer)
- No focal loss patch — uses standard BCE
- Mild augmentations only
- `mosaic: 0.0`

---

### 3.4 Stage 4 — The Judge (Fusion, No Model)

Pure Python/Shapely geometry. Consumes all three model outputs and applies locked rules:

| Rule | Inputs Used | Effect |
|------|-------------|--------|
| **Tire suppression** | S2 defect ∩ S3 tire_mask | IoD ≥ 0.50 → suppress (`tire`) — kills tire-texture FPs |
| **Non-car suppression** | S2 defect ∩ S3 car_context | IoD < 0.30 → suppress (`non_car_context`) — kills tree/wall FPs |
| **Panel assignment** | S2 defect ∩ each S3 panel | argmax IoD; assign if ≥ 0.50, else "Unknown" (kept) |
| **S1↔S2 matching** | S1 blob ∩ S2 mask | IoS ≥ 0.30 → already explained by Stage 2, skip |
| **S1 rescue** | Unmatched S1 blob ∩ car_context | On car (≥0.30) → `unclassified_anomaly`; off car → suppress |
| **Mask bleed fix** | Uses bounding box for car-context check | Prevents real defects from being suppressed due to mask bleed |

**Decision Table (Final Output):**

| Condition | Final Behavior |
|-----------|---------------|
| Stage 2 detects defect on car panel | Report classified defect |
| Stage 2 detects defect mostly on tire | Suppress as `tire` |
| Stage 1 anomaly matches Stage 2 | Keep Stage 2 class |
| Stage 1 anomaly on car body, no Stage 2 match | Report `unclassified_anomaly` |
| Stage 1 anomaly mostly on tire | Suppress as `tire` |
| Stage 1 anomaly outside car panels | Suppress as `non_car_context` |
| Stage 1 anomaly in low-context close-up | Mark `low_context`, do not silently suppress |

**Why This Design Works:**
- **Each stage compensates for another's weakness:** Stage 1's 50% FPR is cleaned by Stage 3's context; Stage 2's missed micro-defects are rescued by Stage 1's mask; Stage 2's tire FPs are killed by Stage 3's wheel masks.
- **Different tasks need different tools:** recall needs tiling + Focal Loss (S1), classification needs 1024px resolution (S2), context is fine at 640px (S3), and validation is pure geometry (S4).
- **Cheap early exit:** clean cars cost ~34ms total.

---

### 3.5 Concrete Example (`000085.jpg`)

1. **Stage 1** sees saliency 0.011 > 0.0005 → ACTIVE. Mask lights up on dent, broken lamp, *and* trees.
2. **Stage 2** classifies: dent (0.88), broken_lamp (0.59), plus faint scratches.
3. **Stage 3** draws 20 panels → car_context covers body; tire_mask covers wheels.
4. **Stage 4** fuses:
   - Dent → IoD 1.0 with front_bumper → **kept**, panel assigned, DSI computed.
   - Broken lamp → bbox mostly on car → **kept** (not suppressed despite messy mask).
   - Tree blobs → car_context IoD ≈ 0 → **suppressed** (`non_car_context`).
   - Any on-car S1 blob S2 missed → **rescued** as `unclassified_anomaly`.

---

## 4. Production Deployment Workflow

### 4.1 Execution Order (Factory Floor)

> Models do NOT run in numerical order (1→2→3). They run in the order that makes logical sense for filtering and fusion.

```text
Step 1: Stage 3 (Panel Segmenter, 640px)
    → Outputs: car_context_mask + tire_mask
    → Why first: Need spatial context before defect detection

Step 2: Stage 1 & Stage 2 (Parallel or back-to-back)
    → Stage 1: Tiled binary SOD → anomaly masks (high recall)
    → Stage 2: SAHI 1024px → classified defect masks

Step 3: Stage 4 (Fusion Logic — Python, no ML)
    → Action A: Suppression Filter (tire, non-car)
    → Action B: Stage 1 Rescue (match or flag unclassified)
    → Action C: Panel Assignment (IoD) + Severity (DSI)

Step 4: Final Output
    → Factory Report JSON + Dashboard UI overlays
```

### 4.2 Detailed Step Descriptions

#### Step 1: Stage 3 (Panel & Component Segmenter)
- **What runs:** The 21-class panel model (runs fast at 640px).
- **Why it runs first:** Before we look for defects, we need to know **where the car is** and **where the tires are**.
- **Output:** It generates the spatial context map. We extract two critical masks:
  1. `car_context_mask` (union of all body panels like Hood, Doors, Bumpers)
  2. `tire_mask` (union of Front-wheel and Back-wheel)

#### Step 2: Stage 1 & Stage 2 (The Defect Detectors)
*These two can technically run in parallel or back-to-back. They are the heavy lifters.*

- **Stage 1 (Binary Anomaly Screener):** Runs using overlapping tiles. It outputs a list of raw **"anomaly"** masks (high recall, doesn't care about class).
- **Stage 2 (7-Class Defect Segmenter):** Runs using SAHI (1024px slices). It outputs a list of **"classified"** defect masks (dent, scratch, crack, etc.).

#### Step 3: Stage 4 (The Fusion & Filtering Engine)
*Stage 4 is not a neural network; it is the Python logic layer that takes the outputs from Steps 1 and 2 and makes the final industrial decisions.*

- **Action A: The Suppression Filter (Using Stage 3)**
  - Look at all Stage 1 and Stage 2 detections.
  - *Rule 1 (Tire Ignore):* If a defect overlaps the `tire_mask` by >50%, **suppress it** (ignore it completely).
  - *Rule 2 (Non-Car Ignore):* If a Stage 1 anomaly is completely outside the `car_context_mask` (e.g., on a tree, wall, or garage floor), **suppress it**.

- **Action B: The Stage 1 Rescue (Fusion)**
  - Compare the surviving Stage 1 anomalies with the Stage 2 classified defects.
  - *Match:* If a Stage 1 anomaly overlaps a Stage 2 defect, keep the **Stage 2 class** (e.g., "scratch").
  - *Rescue:* If Stage 1 found an anomaly on a valid car panel, but Stage 2 completely missed it, flag it as an **`unclassified_anomaly`**.

- **Action C: Panel Assignment & Severity (IoD & DSI)**
  - For every surviving defect, calculate the **IoD (Intersection over Defect)** against the Stage 3 panel masks to assign it to a specific part (e.g., "Front-door", "Hood").
  - Calculate the **DSI (Damage Severity Index)** based on the size of the defect relative to the panel.

#### Step 4: The Final Output (Dashboard / Factory Report)
The system packages the surviving, filtered, and fused data into the final JSON report and UI overlays for the operator.

### 4.3 Operator Alert Types

The operator sees three types of alerts:

| Alert Type | Example | Source |
|-----------|---------|--------|
| **Confirmed Defect** | `"scratch"` on `Front-door` | Stage 2 found, verified by Stage 1 |
| **Rescued Anomaly** | `"unclassified_anomaly"` on `Rocker-panel` | Stage 1 found, Stage 2 missed → operator reviews |
| **Suppressed** | *(nothing shown)* | Tire/background silently dropped by Stage 4 |

### 4.4 Inference-Time Confidence Rescue

```text
Normal region:
    Stage 2 conf threshold = 0.15

Inside Stage 1 anomaly region:
    Stage 2 conf threshold = 0.10 or 0.05
```

This focuses extra recall only in suspicious regions. Fits existing presets:

| Preset | Stage 2 Behavior |
|--------|-----------------|
| Balanced | Normal threshold (0.15) |
| Safety | Lower threshold inside Stage 1 anomaly regions (0.10) |
| Max Recall | Much lower threshold inside Stage 1 anomaly regions (0.05) |

This should be validated carefully because Stage 1 false positives can cause Stage 2 false positives. That is why Stage 3 panel/tire/non-car filtering is important.

### 4.5 Example Rescue Output

```json
{
  "defect_id": "DEF_031",
  "class": "unclassified_anomaly",
  "source": "stage1_rescue",
  "panel": "Front-door",
  "stage2_matched": false,
  "confidence_source": "stage1"
}
```

This improves **system recall** without changing Stage 2's official class metrics. It is also very suitable for the dashboard because the operator sees: *"Possible defect, class not confirmed"* instead of nothing.

### 4.6 Summary Flowchart

```text
[ Raw Car Image ]
  │
  ├──►  (1) STAGE 3: Panel Segmenter (640px)
  │   └─►  Outputs: Car Body Mask + Tire Mask
  │
  ├──►  (2) STAGE 1: Binary SOD (Tiled)
  │   └─►  Outputs: Anomaly Masks
  │
  └──►  (3) STAGE 2: 7-Class Defect (SAHI 1024px)
      └─►  Outputs: Classified Defect Masks
  │
  ▼
[ (4) STAGE 4: FUSION LOGIC ]
  │
  ├─►  Drop defects on Tire Mask
  ├─►  Drop anomalies outside Car Body Mask
  ├─►  Match Stage 1 & Stage 2 (Keep Class or Flag as Unclassified)
  ├─►  Assign to specific Panel (IoD)
  └─►  Calculate Severity (DSI)
  │
  ▼
[ Final Factory Report JSON & Dashboard UI ]
```

> This order ensures that we don't waste compute time running heavy SAHI slicing on trees/walls, and it guarantees that the operator is never bothered by false positives on the tires!

---

## 5. Supervisor Feedback & Detailed Response

### 5.1 Three Key Points from Supervisor

1. **Merging all defects into one class is useful for recall, but does not remove the need for a specialized multi-class Stage 2.**
2. **Small-defect detection is mostly a resolution/tiling problem, not a class-count problem.**
3. **The biggest risk in retraining Stage 1 with combined data is image-level leakage between CarDD_SOD and CarDD_COCO / Stage 2 source images.**

> ⚠️ Point 3 is the most critical new warning.

---

### 5.2 Response to Point A: Class Merging

**Agreed.** A single `defect` class improves recall because the model only answers *"Is this abnormal or not?"* But defect types are visually heterogeneous:

| Defect | Visual Signature |
|--------|-----------------|
| scratch | thin line |
| crack | branching thin structure |
| corrosion | textured patch / discoloration |
| dent | shading / surface deformation |
| broken_lamp | structural component damage |
| glass_shatter | high-frequency shattered texture |
| disjoint_part | structural gap / misalignment |

So a single `defect` class can improve recall but may produce less specialized, less tightly localized masks for some defect types.

**Decision:** Keep the cascade design. Use the binary model as a **recall booster** and **anomaly miner**, not a Stage 2 replacement.

```text
Stage 1: class-agnostic, high-recall anomaly screener
Stage 2: specialized multi-class defect segmenter
Stage 3: panel/component spatial context
Stage 4: fusion and reporting
```

---

### 5.3 Response to Point B: Small-Defect Detection

**Agreed.** Evidence from our own project:

| Week | Problem | Fix | Result |
|------|---------|-----|--------|
| Week 2 (S1) | Hairline scratch blindness | 15% overlap tiling + Focal Loss + threshold calibration | Solved Stride-8 dilution |
| Week 5–6 (S2) | Thin defects sub-pixel at 640px | SAHI at native 1024px | Restored micro-defect signal |

Quantified example:
```text
Direct inference at global scale:  micro-corrosion probability ≈ 0.04
Native-resolution crop / SAHI:     probability > 0.25
```

**Conclusion:** Class merging affects recall/confusion. Tiling/resolution affects small-object visibility. They are separate levers.

---

### 5.4 Response to Point C: Leakage Warning

**Critical.** If CarDD_SOD and CarDD_COCO share source images, we cannot split by dataset — we must split by **source image**.

**Risk scenario:**
```text
Image X in Stage 1 validation/test
  + same Image X in Stage 2 training data
  + convert Stage 2 labels to binary
  + train Stage 1 on Image X
  = Stage 1 validation has leaked training data
```

**Action:** Image-level overlap audit is now **Step 1** before any merging. (See §7.)

---

### 5.5 Stage 1 v2 Role Definition

**Stage 1 v2 IS:**
- A class-agnostic anomaly recall engine
- Catches defects Stage 2 may miss
- Provides unclassified anomaly proposals
- Mines hard examples for Stage 2 retraining
- Acts as a production safety net

**Stage 1 v2 IS NOT:**
- The final defect classifier
- Expected to output `scratch` / `crack` / `corrosion`
- A replacement for Stage 2

It only outputs: `defect / anomaly`

---

### 5.6 Label Conversion for Stage 1 Retraining

Use **binary masks** (not just boxes) to match Stage 1's semantic segmentation format:

```text
Stage 2 polygon → Render filled binary mask (all defect classes → 1, background → 0)
```

| Stage 2 Class | Binary Stage 1 Label |
|---------------|---------------------|
| dent | defect |
| scratch | defect |
| crack | defect |
| glass_shatter | defect |
| broken_lamp | defect |
| corrosion | defect |
| disjoint_part | defect |

If we only use boxes, we may lose mask localization quality. So we recommend: *Use Stage 2 polygons to render binary defect masks.*

---

### 5.7 Expected Trade-Off

> Recall increases usually come with matching increases in false positives.

This is acceptable because the operator dashboard absorbs the cost:
- Missing a defect = **bad**
- Flagging a false alarm = operator spends a few seconds checking

**Recommended metrics to report:**

| Category | Metrics |
|----------|---------|
| **Recall-side** | S2 recall alone; S2+S1 system recall; S1 rescue rate on S2 missed defects; micro-defect recall; small-defect recall; corrosion recall; disjoint_part recall |
| **Precision / operator burden** | FP per image; unclassified anomalies per image; tire FP; non-car FP; operator review count per image |
| **Classification coverage** | % of S1 anomalies S2 can classify; % remaining unclassified |

This lets us say clearly: *"We deliberately traded some precision for higher system recall because the operator dashboard allows human review."* — a strong, honest engineering statement.

---

### 5.8 Guided Tiling (Deferred)

**Status:** Deferred. Uniform SAHI (1024px, 15% overlap) is validated and safe.

**Guided tiling would mean:** Use Stage 1 saliency mask to decide where to tile more densely.

**Possible benefit:** Less compute, faster inference, more resolution where Stage 1 thinks damage exists.

**Risk:** If Stage 1 misses a defect, guided tiling also misses it.

**Revisit only if:**
1. Inference speed becomes a real problem.
2. Stage 1 recall is proven very high.
3. Strong evaluation shows guided tiling does not drop defects.

For now, uniform SAHI is safer.

---

## 6. Draft Reply to Supervisor

> Thanks — that clarifies the trade-offs well. I agree that merging into a single defect class can improve recall but may reduce localization tightness because defect types are visually heterogeneous. I also agree that small-defect detection is mainly governed by resolution/tiling, not class count, which matches what we observed in Stage 1 and Stage 2.
>
> The leakage point is important. Since CarDD_SOD and CarDD_COCO may share source images, I will first run an image-level overlap audit using filenames and hashes before merging any Stage 2 annotations into Stage 1 training. The combined Stage 1 dataset will be built only from non-overlapping train images, and the held-out test set will remain untouched.
>
> For Stage 1's role, I plan to keep it as a class-agnostic high-recall anomaly screener, not a replacement for Stage 2. I will implement inference-time rescue so that unmatched Stage 1 anomalies are surfaced as "unclassified defect" in the operator dashboard. For durable improvement, I will use Stage 1 for human-reviewed hard-example mining: Stage 1 proposes suspicious regions, operators confirm/classify them, and the confirmed examples are added to Stage 2's training set for Model 6. Guided tiling can be revisited later as an efficiency optimization.
>
> I will also report the precision/recall trade-off explicitly, since higher recall from Stage 1 will likely increase false positives, but the operator-in-the-loop dashboard is designed to absorb that cost.

---

## 7. Leakage Audit Protocol

### 7.1 Mandatory Pre-Merge Checks

Before combining Stage 1 and Stage 2 data:

1. Which images belong to CarDD_SOD?
2. Which images belong to CarDD_COCO?
3. Which images belong to the clean Stage 2 dataset?
4. Which images belong to Stage 1 train/val/test?
5. Which images belong to Stage 2 train/val/test?
6. Are there duplicate filenames?
7. Are there duplicate file hashes?
8. Are there perceptually duplicate images (different filenames/resolutions)?

### 7.2 Expected Audit Output

```text
Dataset D images:        N1
Stage 2 images:          N2
Filename overlaps:       N3
Exact hash overlaps:     N4
Perceptual duplicates:   N5
Stage 1 test leaks:      N6
Stage 2 test leaks:      N7
```

### 7.3 The Golden Rule

> **The held-out test set must never contribute training pixels, masks, boxes, or labels to any model being evaluated on that test set.**

If any Stage 1 test image appears in Stage 2 training data → exclude from combined training.
If any Stage 2 test image appears in Stage 1 training data → exclude carefully.

---

## 8. Revised Development Plan

### 8.1 Safer Plan (Post-Supervisor Feedback)

| Step | Action | Details |
|------|--------|---------|
| 1 | Audit image overlap between all datasets | Mandatory before any retraining |
| 2 | Build a leakage-free combined binary dataset | Only non-overlapping train images |
| 3 | Retrain Stage 1 v2 as high-recall anomaly screener | YOLO26m, tiled, Focal Loss, calibrated |
| 4 | Use Stage 1 for inference-time rescue | Surface unclassified anomalies |
| 5 | Use Stage 1 for human-reviewed hard-example mining / pseudo-labeling | Operator confirms/classifies |
| 6 | Retrain Stage 2 Model 6 with enriched data | Data flywheel |

### 8.2 Human-Reviewed Pseudo-Labeling Workflow

```text
1. Run Stage 1 v2 on unlabeled images or legacy corpus
2. Find Stage 1 anomalies
3. Filter using Stage 3:
   - Must overlap car panels
   - Must not be mostly tire
4. Check whether Stage 2 already detects it
5. If Stage 2 misses it → send to operator review
6. Operator decides:
   - Real defect? Which class? Polygon correction? Reject?
7. Add confirmed defects to Stage 2 training dataset
8. Retrain Stage 2 Model 6
```

> This creates the **data flywheel** — the only method that permanently improves Stage 2.

### 8.3 Why Human-Reviewed (Not Fully Automatic)

Because Stage 1 can produce false positives on:
- trees, walls, shadows, reflections
- tire texture, dirty surfaces
- background objects

Also, Stage 1 does not know the defect class. So human review is essential.

### 8.4 Stage 1 v2 Training Recipe

Start from the proven Stage 1 recipe:
```text
YOLO26m
tiled input
15% overlap
Focal Loss (γ=2.0)
leakage-free validation
threshold calibration
```

Then optionally test: `640 tiled` vs `1024 tiled / native-resolution slicing`

### 8.5 Final Answer to Supervisor's Advice

```text
Do not merge datasets yet.
First audit image-level overlap.
Then retrain Stage 1 as a binary high-recall anomaly screener.
Use Stage 1 for inference-time rescue and hard-example mining.
Keep Stage 2 as the multi-class defect classifier.
Use Stage 3 to suppress tire/non-car false positives.
Report the precision/recall trade-off explicitly.
```

The most important next concrete step is:
> **Run a leakage audit between Stage 1 Dataset D, CarDD_COCO / Stage 2 source images, and all train/val/test splits.**

---

## 9. Backend API Surface (Complete)

### 9.1 Host/System APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/api/host/profile` | Hardware detection + model availability |
| GET | `/api/system/metrics` | Live CPU/RAM/GPU polling |
| GET | `/api/system/devices` | Available compute devices |
| GET | `/api/runtime/mode` | Get current runtime mode |
| POST | `/api/runtime/mode` | Set runtime mode |

### 9.2 Inference APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/models` | Champion weight discovery |
| POST | `/api/inspect` | Full 4-stage inspection pipeline (persists to disk) |
| GET | `/api/inspections/{id}` | Get inspection result |
| GET | `/api/inspections/{id}/report` | Get factory report JSON |

### 9.3 Review APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/reviews` | Submit operator review |
| GET | `/api/reviews` | List all reviews |
| GET | `/api/review-queue` | Get pending review items |
| PATCH | `/api/reviews/{id}` | Update review |
| DELETE | `/api/reviews/{id}` | Delete review |

### 9.4 Dataset APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/datasets` | List all datasets |
| GET | `/api/datasets/{id}` | Dataset detail + class distribution |
| POST | `/api/datasets/{id}/audit` | Leakage audit |
| POST | `/api/datasets/build` | Build from reviews (flywheel) |
| DELETE | `/api/datasets/{id}` | Delete dataset |
| POST | `/api/datasets/create` | Create new empty dataset |
| GET | `/api/datasets/{id}/images?page=&size=` | Paginated image list |
| GET | `/api/datasets/{id}/images/{filename}` | Serve image (FileResponse) |
| GET | `/api/datasets/{id}/images/{filename}/labels` | Parsed labels (YOLO or semantic mask) |
| PATCH | `/api/datasets/{id}/images/{filename}/labels/{idx}` | Reclassify annotation |
| DELETE | `/api/datasets/{id}/images/{filename}/labels/{idx}` | Delete annotation |

### 9.5 Dataset Import APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/import/inspections` | List saved inspections |
| POST | `/api/datasets/{id}/import/inspection` | Import from flywheel |
| POST | `/api/datasets/{id}/import/upload` | Single image upload |
| POST | `/api/datasets/{id}/import/zip` | ZIP archive import |

### 9.6 Training APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/training/jobs` | Launch training job |
| GET | `/api/training/jobs` | List all training jobs |
| GET | `/api/training/jobs/{id}` | Get job detail |
| GET | `/api/training/jobs/{id}/logs` | Stream training logs |
| POST | `/api/training/jobs/{id}/stop` | Stop training job |

### 9.7 Experiment APIs

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/experiments` | List MLflow experiments |
| GET | `/api/experiments/{id}/runs` | List runs in experiment |
| POST | `/api/experiments/compare` | Compare multiple runs |

### 9.8 Model Registry APIs (Phase 12)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/model-registry` | List all model versions |
| GET | `/api/model-registry/{id}` | Get model detail |
| POST | `/api/model-registry/register` | Register new model version |
| POST | `/api/model-registry/{id}/evaluate` | Run evaluation gates |
| POST | `/api/model-registry/{id}/promote` | Promote candidate to champion |
| POST | `/api/model-registry/{id}/deploy` | Deploy champion to production |
| POST | `/api/model-registry/{id}/rollback` | Rollback to previous champion |

### 9.9 API Surface Summary

```text
Total endpoints: 45+
Backend port: 8010
Auth: None (local deployment)
Format: JSON (Pydantic schemas)
Database: SQLite (reviews, model_registry, training_jobs)
```

---

## 10. Desktop Application Productionization Plan

### 10.1 Vision

```text
One desktop app
  → Operator Mode (inspect cars, confirm/reject defects)
  → Engineer Mode (train models, manage datasets, promote champions)
  → Local or remote training/inference
  → Automatic host detection
  → Standardized pipeline
  → Continuous model improvement
```

### 10.2 Architecture Layers

```text
┌─────────────────────────────────────────────────┐
│         Desktop App UI (React)                   │
│         Operator + Engineer Combined             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend                          │
│         Local service or remote service          │
└──────┬───────────────────────────┬──────────────┘
       │                           │
       ▼                           ▼
┌─────────────┐         ┌─────────────────────┐
│ Local Host  │         │ Remote Host          │
│ Detector    │         │ Connection Manager   │
└──────┬──────┘         └─────────┬───────────┘
       │                          │
       ▼                          ▼
┌─────────────────────────────────────────────────┐
│         Execution Engine                         │
│   Inference / Training / Audit / Eval / Registry │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│         ML Pipeline Modules                      │
│   Stage 1 / Stage 2 / Stage 3 / Stage 4         │
└─────────────────────────────────────────────────┘
```

### 10.3 UI Tab Structure (Combined Mode)

| Tab | Role | Features |
|-----|------|----------|
| **Inspection** | Operator | Upload, run pipeline, view defects/panels/anomalies, export report |
| **Review** | Operator | Confirm/reject/reclassify, review queue, hard-example export |
| **Datasets** | Engineer | List versions, class distribution, leakage audit, build new, import, tile, re-split |
| **Training** | Engineer | Select stage/dataset/config/device, launch, monitor logs, stop |
| **Experiments** | Engineer | Compare runs, loss curves, per-class metrics, failure examples, best highlighting |
| **Models** | Engineer/Supervisor | Registry, promote, deploy, rollback, model cards, evaluation gates |
| **Settings** | Both | Runtime mode, URLs, paths, theme, debug |
| **Host / System** | Both | GPU status, disk, API health, model availability, recommendations |

### 10.4 Host Detection

The app auto-detects:

**Local machine:**
- OS, CPU count, RAM, disk space
- Python env, CUDA/MPS availability
- GPU name + VRAM
- PyTorch/Ultralytics/MLflow availability
- Model weight presence (Stage 1/2/3)
- Dataset presence
- MLflow database presence

**Remote server:**
- Configured? Reachable? GPU? Datasets? Registry?

**Example output:**
```text
Host Profile
  Machine:       Local Desktop
  OS:            Windows 11
  GPU:           NVIDIA RTX 4090 (24 GB VRAM)
  CUDA:          Available
  Disk:          800 GB free
  Local models:  Stage 1 ✓ | Stage 2 ✓ | Stage 3 ✓
  Remote:        Not configured
  Recommended:   Local inference + Local training
```

### 10.5 Execution Modes

```yaml
runtime:
  mode: auto          # auto | local | remote
local:
  inference_device: auto   # auto | cuda | cpu | mps
  training_device: auto
remote:
  enabled: false
  base_url: ""
  api_key: ""
  timeout_seconds: 10
```

**Three deployment styles:**

| Style | Use Case |
|-------|----------|
| **Fully Local** | Single machine, simple install, small team |
| **Fully Remote** | Centralized GPU server, multiple operators |
| **Hybrid** | Local inference (fast UX) + remote training (heavy GPU) |

### 10.6 Technology Choices

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, TanStack Router, Tailwind CSS v4, shadcn/ui |
| Backend | FastAPI, Pydantic, Python 3.10 |
| ML | Ultralytics YOLO, SAHI, Shapely, OpenCV |
| Tracking | MLflow |
| Database | SQLite (local) / PostgreSQL (company) |
| Desktop wrapper | Tauri (Phase 13) |
| Build tool | Bun (frontend) |

### 10.7 Automatic Improvement Loop

```text
Operator inspects car
  → Model detects defects
  → Operator confirms / rejects / reclassifies
  → System stores feedback
  → Hard examples enter review queue
  → Engineer approves dataset update
  → Dataset audit runs
  → Training job runs
  → Evaluation runs
  → Candidate compared with champion
  → Human approves promotion
  → Model deployed
  → System monitors performance
  → Repeat
```

> Training and evaluation can be automatic. **Deployment requires human approval.**

### 10.8 Version Milestones

| Version | Scope | Status |
|---------|-------|--------|
| v0.1 | Combined UI shell, host detection, inspection dashboard | ✅ Complete |
| v0.2 | Stage 1 rescue, unclassified anomaly, tire/non-car suppression | ✅ Complete |
| v0.3 | Operator review/feedback, review queue, hard-example export | ✅ Complete |
| v0.4 | Engineer training module, experiment comparison, dataset management | ✅ Complete |
| v0.5 | Model registry, promotion gates, human-approved deployment | ✅ Complete |
| Final | Tauri desktop packaging, installer | 🔜 Phase 13 |

---

## 11. Training Infrastructure

### 11.1 Unified Training Flow

```text
┌─────────────────────────────────────────────────┐
│  LaunchTrainingDialog (UI)                      │
│  Select stage, dataset, overrides, base model   │
└──────────┬──────────────────────────────────────┘
           │  POST /api/training/jobs
           ▼
┌─────────────────────────────────────────────────┐
│  training_worker.py                             │
│  1. Load base config                            │
│  2. Merge UI overrides                          │
│  3. Inject metadata                             │
│  4. Save snapshot YAML                          │
│  5. Launch subprocess                           │
└──────────┬──────────────────────────────────────┘
           │  python src/{stage}/train/train.py --config snapshot.yaml
           ▼
┌─────────────────────────────────────────────────┐
│  Stage-Specific Trainer                         │
│  Reads merged config                            │
│  Applies focal loss / differential LR           │
│  Calls model.train(...)                         │
└──────────┬──────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────┐
│  MLflow + Log Streaming + Candidate Collector   │
│  Metrics → MLflow                               │
│  Logs → UI (3s polling)                         │
│  On completion → auto-register candidate        │
└─────────────────────────────────────────────────┘
```

### 11.2 Stage-Specific Training Details

#### Stage 1 — Binary SOD

| Parameter | Value |
|-----------|-------|
| Trainer script | `src/stage1/train/train_sod.py` |
| Task | Semantic segmentation (`task: semantic`) |
| Loss | FocalCrossEntropyLoss (γ=2.0) |
| Dataset | `sod_tiled` (PNG masks, not YOLO polygons) |
| Key config | `pipeline.loss_type: focal`, `pipeline.task: semantic` |
| Input format | Tiled grayscale masks (0=clean, 1=damage) |
| Base model | `yolo26n-sem.pt` |

#### Stage 2 — 7-Class Defect

| Parameter | Value |
|-----------|-------|
| Trainer script | `src/stage2/train/train.py` |
| Task | Instance segmentation |
| Loss | ScaledFocalBCEWithLogitsLoss (γ=2.0, α=0.50) |
| imgsz | 1024 (locked) |
| freeze | 23 (backbone frozen, head trained) |
| Base model | `model1_remapped_7class_init.pt` |
| multi_scale | false (prevent OOM) |
| mosaic | 0.0 (stability) |
| Key principle | Resume-and-Adapt transfer |
| Optional | Differential LR (backbone 10× slower) |

#### Stage 3 — 21-Class Panel

| Parameter | Value |
|-----------|-------|
| Trainer script | `src/stage3/train/train.py` |
| Task | Instance segmentation |
| Loss | Standard BCE (no focal patch) |
| imgsz | 640 |
| freeze | 0 (train everything) |
| Optimizer | AdamW |
| Base model | `yolo26m-seg.pt` |
| differential_lr | false |
| mosaic | 0.0 |

### 11.3 Config Snapshot Mechanism

Every training job saves a frozen config at:
```text
backend/data/configs/training/{job_id}.yaml
```

Contains: base config + UI overrides + injected metadata.

**Benefits:**
- Reproducibility (exact config for any historical run)
- Auditability (logged to MLflow as artifact)
- Debugging (inspect failed runs)

### 11.4 Mac MPS Safety Guard

Auto-limits epochs to 1 on Apple Silicon unless explicitly overridden. Prevents accidental 100-epoch training on MacBook.

### 11.5 Candidate Collector (Phase 12 Addition)

After a training job completes successfully (`returncode == 0`):
1. Locates `best.pt` (Ultralytics `runs/` convention **plus MLflow `artifacts/` discovery**)
2. Parses last row of `results.csv` into gate metric keys
3. Auto-registers a `candidate` in the model registry

### 11.6 Known Issue

```python
TRAINER_SCRIPTS = {
    StageType.STAGE1: "src/stage1/train/train.py",  # ← generic trainer
    ...
}
```

But Stage 1's actual SOD trainer is `src/stage1/train/train_sod.py` (uses FocalCrossEntropyLoss). This mapping may need correction.

---

## 12. Phase 12 Session Report

### 12.1 Model Registry & Deployment — ✅ DELIVERED

Closed the MLOps loop with a human-approved promotion/deployment system.

#### Backend (New/Modified Files)

| File | Purpose |
|------|---------|
| `backend/schemas/model_registry.py` | Pydantic models: `ModelVersion`, `GateResult`, `RegisterRequest`, `PromotionResponse`, `DeploymentResponse`, `RollbackResponse`, `GatePreviewResponse` |
| `backend/services/model_registry_db.py` | SQLite persistence (`backend/data/model_registry.db`) |
| `backend/services/evaluation_gates.py` | Stage-specific gates (detailed below) |
| `backend/services/model_registry_service.py` | Orchestration: register → promote (gates) → deploy (symlink) → rollback |
| `backend/api/model_registry.py` | REST endpoints under `/api/model-registry` |
| `backend/main.py` | Router wired |

#### Evaluation Gates (Stage-Specific)

| Stage | Gate Criteria |
|-------|--------------|
| Stage 1 | `min_recall ≥ 0.90` |
| Stage 2 | `mAP50 ≥ champion − 0.005`, rare-class recall regression ≤ 0.05, clean leakage audit |
| Stage 3 | `mAP50 ≥ champion − 0.005`, rare-class recall regression ≤ 0.05, clean leakage audit |

#### Frontend (New Files)

| File/Component | Purpose |
|---------------|---------|
| `src/lib/inspection/modelRegistrySchema.ts` | TypeScript types for registry |
| `src/components/Models/ModelsDashboard.tsx` | Main composition |
| `src/components/Models/ModelListTable.tsx` | Table with status badges |
| `src/components/Models/ModelDetailPanel.tsx` | Metrics, config, eval report |
| `src/components/Models/PromoteDialog.tsx` | Compare candidate vs champion |
| `src/components/Models/DeployDialog.tsx` | Deployment confirmation |
| `src/components/Models/RollbackDialog.tsx` | Rollback confirmation |
| `src/components/Models/modelUtils.ts` | Helper functions |
| `src/components/Models/index.ts` | Barrel exports |
| `src/routes/models.tsx` | Route composition |
| `__root.tsx` | Added "Models" nav tab |

#### Layout Fixes Applied
- `table-fixed` on registry table
- `min-w-0` on cells
- `truncate` on long text
- `shortDatasetName` utility for display

---

### 12.2 Training Integration — ✅ DELIVERED

| File | Purpose |
|------|---------|
| `backend/services/candidate_collector.py` | After job completes: locate `best.pt`, parse `results.csv`, auto-register candidate |
| `backend/services/training_worker.py` | Hook added on `returncode == 0` (failure-isolated with try/except) |

**Candidate collection logic:**
1. After training completes, search Ultralytics `runs/` convention for `best.pt`
2. Also search MLflow `artifacts/` directory (discovered weights land in `mlruns/`, not `runs/`)
3. Parse last row of `results.csv` → extract gate metric keys (mAP50, mAP50-95, precision, recall)
4. Auto-register as `candidate` status in model registry

---

### 12.3 End-to-End Testing & The Champion Crisis — ✅ RESOLVED

**What happened, in chronological order:**

1. **Smoke test (Stage 3, 1 epoch)** launched from UI → completed → revealed weights land in `mlruns/`, not `runs/` → collector patched to search both locations.

2. Manually registered smoke candidate → **promoted with threshold 0.0** (no champion existed yet — gate design behaves correctly for first seeding) → deployed (symlink created).

3. **Real champion seeding failed**: manifest path `mlruns/Stage 3/2347b4e3…/best.pt` missing. Investigation proved a **previous cleanup session had moved it to `archive/pre_standardization/mlruns_legacy/Stage 3/`** (violating the cleanup plan's own "never archive champions" rule). Nothing in this session deleted it.

4. **Restored** via `cp -R` from archive → verified 87-epoch champion (`mAP50(M) 0.878`) → registered, promoted, deployed. Stage 2 champion (`stage1_head_warmup_7cls_extended`) also seeded + deployed.

5. **Inference still showed empty panels** → root cause: `ModelManager` caches by `stage/filename`; the running server had cached the 1-epoch smoke model under `stage3/deployed.pt`, and repointing the symlink didn't invalidate it. **Fix: backend restart** → panels restored (Hood, etc.), S1 clipping and panel assignment working again.

6. **`GET /api/experiments` 500** (`Invalid experiment ID: 'Stage 3'`): the restored `mlruns/Stage 3/` dir (space in name, no `meta.yaml`) broke MLflow's `search_experiments()`. **Fix: `rm -rf "mlruns/Stage 3"`** → experiments API healthy.

---

### 12.4 Registry State After Phase 12

| Stage | Status | Model | Details |
|-------|--------|-------|---------|
| Stage 1 | Champion (pre-existing) | `sod_tiled` Focal Loss | Not yet in registry DB |
| Stage 2 | Champion (deployed) | `stage1_head_warmup_7cls_extended` | Symlinked |
| Stage 3 | Champion (promoted + deployed) | `panel_segmenter_baseline` | 87-epoch, mAP50(M) 0.878 |
| Smoke entries | Purged | — | Cleaned from registry |

---

## 13. Workspace Cleanup Status

### 13.1 Option B Cleanup — Mostly Complete

| Item | Status | Details |
|------|--------|---------|
| Backend `.gitignore` | ✅ Done | Runtime data dirs + `backend/models/*/deployed.pt` ignored (healed after zsh paste mangling via Python script) |
| Frontend dead code | ✅ Done | `CreateDatasetDialog.tsx` and `ImportDatasetDialog.tsx` removed (grep-verified zero consumers) |
| `demoPayload.ts`/`mockPipeline.ts`/prettier renames | ✅ Done | Already done by prior session |
| Legacy `backend/config.py` refactor | ✅ Done | `tau_pixel`/`tau_anomaly` → `core/config.py` Settings; `model_manager.py` → absolute paths via `settings.workspace_root`; `stage1.py` repointed; inference re-verified |
| `review.tsx` monolith → components | 🟡 Delivered | `src/components/Review/` (6 files: utils, SubmitForm, EditForm, HistoryList, Dashboard, barrel + thin route wrapper) — code delivered, tsc/commit not yet confirmed |

### 13.2 Review Component Extraction (Delivered, Pending Commit)

```text
src/components/Review/
├── reviewUtils.ts        — shared helpers
├── ReviewSubmitForm.tsx  — confirm/reject/reclassify form
├── ReviewEditForm.tsx    — inline edit
├── ReviewHistoryList.tsx — history table
├── ReviewDashboard.tsx   — composition
└── index.ts              — barrel exports
```

Route: `src/routes/review.tsx` (thin wrapper, imports from barrel)

---

## 14. Full Project Status Report

### 14.1 Phase Completion Matrix

| Phase | Description | Status | Version |
|-------|-------------|--------|---------|
| Phase 0 | Planning & Confirmation | ✅ Complete | — |
| Phase 1 | Champion Verification | ✅ Complete | — |
| Phase 2 | Workspace Inventory | ✅ Complete | — |
| Phase 3 | Safe Workspace Cleanup | ✅ Complete | — |
| Phase 4 | Environment & Tooling Fixes | ✅ Complete | — |
| Phase 5 | Backend Foundation | ✅ Complete | v0.1 |
| Phase 6 | Combined UI Shell | ✅ Complete | v0.1 |
| Phase 7 | Full Inspection Pipeline (S1–S4) | ✅ Complete | v0.2 |
| Phase 8 | Review & Data Flywheel | ✅ Complete | v0.3 |
| Phase 9 | Dataset Management | ✅ Complete | v0.4 |
| Phase 10 | Training Module | ✅ Complete | v0.4 |
| Phase 11 | Experiment Comparison | ✅ Complete | v0.4 |
| Phase 12 | Model Registry & Deployment | ✅ Complete | v0.5 |
| Phase 13 | Desktop Packaging (Tauri) | 🔜 Next | Final |

### 14.2 Champion Models (PROTECTED)

| Stage | Model | Dataset | Key Config | Champion Path |
|-------|-------|---------|-----------|--------------|
| Stage 1 | YOLO26m-sem, Focal Loss | `sod_tiled` (16K images) | 640px, γ=2.0 | `mlruns/1/f3b8f26d.../weights/best.pt` |
| Stage 2 | YOLO26m-seg, Model 5 Head Warmup Extended | `yolo_seg_clean_2200_7cls` (2,019 images) | 1024px, freeze=23 | `runs/segment/stage1_head_warmup_7cls_extended/.../best.pt` |
| Stage 3 | YOLO26m-seg, 21-class panels | `car_damages_panel` (998 images) | 640px, AdamW | `archive/pre_standardization/mlruns_legacy/Stage 3/2347b4e3.../artifacts/weights/best.pt` |

### 14.3 What Works Right Now

```text
✅ Upload car image → Run 4-stage inspection → See defects + panels
✅ Stage 1: Binary SOD pre-screen (Focal Loss, 640px)
✅ Stage 2: 7-class defect segmentation (SAHI, 1024px)
✅ Stage 3: 21-class panel segmentation (640px)
✅ Stage 4: IoD fusion (assign defects to panels, compute DSI)
✅ Stage 1 rescue (unclassified anomaly display)
✅ Tire + non-car suppression
✅ Mask bleed fix (bounding box for car-context check)
✅ Car-context clipping for S1 canvas view
✅ Live system metrics (CPU/RAM/MPS on MacBook)
✅ Host detection (GPU, models, capabilities, recommendations)
✅ Dynamic model discovery from /api/models
✅ Review database (SQLite, full CRUD)
✅ Review Queue UI (confirm/reject/reclassify)
✅ Inline flywheel actions on Inspection dashboard
✅ localStorage state persistence
✅ Export Report button (JSON factory report)
✅ Dataset management (import, detect, re-split, tile, browse, audit)
✅ Training module (launch, monitor, stop, config snapshot)
✅ Experiment comparison (MLflow discovery, run comparison)
✅ Model Registry (register, evaluate, promote, deploy, rollback)
✅ Candidate auto-collection after training
✅ Tab navigation (Inspection / Host / Review / Datasets / Training / Models / Settings)
✅ Full data flywheel (Inference → Review → Dataset → Training → Experiments → Registry/Deploy)
```

### 14.4 What's Missing

```text
❌ Remote server integration
❌ Desktop packaging (Tauri) (Phase 13)
❌ Continuous improvement automation (auto-retrain proposals)
❌ Portability fixes (YAML/SAHI standardization)
❌ git push (52+ commits unpushed)
```

---

## 15. Git Commit History

### 15.1 car_defect_detection Repo

| Phase | Commit Message |
|-------|---------------|
| 0 | `docs: add master plan and environment matrix` |
| 1 | `docs: add champion manifest and verification` |
| 3 | `chore: create archive structure and inventory` |
| 3 | `chore: archive unused yolo_import` |
| 3 | `chore: archive duplicate (1) notebooks` |
| 3 | `chore: archive superseded stage2 configs` |
| 3 | `chore: archive exploratory Diagnost notebooks` |
| 4 | `chore: untrack .env and gitignore .pytest_cache` |
| 4 | `fix: remove hardcoded secrets and paths from docker-compose` |
| 4 | `fix: add missing shapely and sahi dependencies` |
| 4 | `docs: populate README with project overview` |
| 4 | `fix: correct pytest path in CI and remove empty dir` |
| 5 | `feat(backend): add phase5 api skeleton with host detection` |
| 5 | `fix(backend): add system metrics, devices, and models endpoints` |
| 5 | `feat(backend): port config, image utils, model manager, schemas` |
| 5 | `feat(backend): port stage1/stage2 inference, orchestrator, /api/inspect` |
| 5 | `fix(backend): add MPS detection to host profile` |
| 5 | `fix(backend): add /api prefix to host router` |
| 7 | `feat(backend): add stage3 panel segmentation service` |
| 7 | `feat(backend): wire stage3 panel segmentation and stage4 IoD fusion` |
| 7 | `fix(backend): map pydantic field aliases in stage4 IoD assignment` |
| 8 | `feat(backend): add review database and /api/reviews endpoints` |
| 9 | `feat(backend): add dataset management (registry, images, builder, import)` |
| 9 | `feat(backend): add dataset prep (import ZIP, detect, re-split, tile)` |
| 10 | `feat(backend): add training module (worker, db, api, config snapshot)` |
| 11 | `feat(backend): add experiment comparison (MLflow discovery)` |
| 12 | `feat(backend): add model registry (db, gates, service, api)` |
| 12 | `feat(backend): add candidate collector (auto-register after training)` |
| 12 | `fix(backend): restore Stage 3 champion from archive` |
| 12 | `fix(backend): seed Stage 2 champion in registry` |
| 12 | `chore: update .gitignore for runtime data and deployed symlinks` |
| 12 | `refactor(backend): migrate legacy config.py to core/config.py` |

### 15.2 Application React Repo

| Phase | Commit Message |
|-------|---------------|
| 5 | `fix: point API client to port 8010` |
| 5 | `fix: align SystemMetricsPanel with flat /api/system/metrics schema` |
| 6 | `feat(ui): add tab navigation shell with host, review, settings routes` |
| 6 | `feat(ui): add host profile dashboard with hardware and model status` |
| 7 | `feat(ui): expand PanelId and PANEL_LABELS to match 21-class stage3 model` |
| 8 | `feat(ui): add review queue with confirm/reject/reclassify` |
| 8 | `feat(ui): add inline flywheel actions on inspection dashboard` |
| 8 | `feat(ui): add localStorage state persistence` |
| 8 | `feat(ui): add export report button` |
| 9 | `feat(ui): add dataset management (list, detail, gallery, audit, import)` |
| 9 | `feat(ui): add dataset prep (import dialog, split panel, resplit, tile)` |
| 10 | `feat(ui): add training module (launch dialog, job list, detail, logs)` |
| 11 | `feat(ui): add experiment comparison (list, run table, dashboard)` |
| 12 | `feat(ui): add model registry (dashboard, list, detail, promote/deploy/rollback)` |
| 12 | `feat(ui): add Models nav tab` |
| 12 | `fix(ui): layout overflow in registry table` |
| 12 | `refactor(ui): extract review.tsx into components/Review/` |

---

## 16. Critical Outstanding Issues & Debt

### 16.1 ⚠️ CRITICAL: Dangling Stage 3 Symlink

**`rm -rf "mlruns/Stage 3"` left the Stage 3 `deployed.pt` symlink DANGLING.** Inference works *only* because the model is still in the live server's memory cache. **On next restart, Stage 3 loading will fail.**

**Remediation commands (run before restarting):**

```bash
cd "/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection"

# Compare checksums — panel_champion.pt may already be the champion copy
md5 backend/models/stage3/panel_champion.pt \
    "archive/pre_standardization/mlruns_legacy/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt"

# Repoint symlink to the stable archive copy + fix registry path
ln -sfn "$(pwd)/archive/pre_standardization/mlruns_legacy/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt" \
    backend/models/stage3/deployed.pt

sqlite3 backend/data/model_registry.db \
    "UPDATE models SET weights_path='archive/pre_standardization/mlruns_legacy/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt' WHERE model_name='panel_segmenter_baseline';"
```

### 16.2 Other Known Debt

| Issue | Severity | Details |
|-------|----------|---------|
| Stage 2 registry says "deployed" but no symlink | Medium | Works via `defect_champion.pt` fallback |
| ModelManager caches by filename, not mtime/hash | Medium | Repointing symlink requires server restart |
| 52+ commits unpushed | Low | Both repos need `git push` |
| Portability: absolute paths in Stage 1/2/3 YAMLs | Low | MacBook/server paths hardcoded |
| Portability: SAHI `model_type` mismatch | Low | Needs standardization |
| `TRAINER_SCRIPTS` maps Stage 1 to wrong script | Low | Should point to `train_sod.py` |
| Review extraction not committed | Low | Code delivered, tsc/commit pending |

---

## 17. Next Steps & Roadmap

### 17.1 Immediate (This Session)

| # | Task | Priority |
|---|------|----------|
| 1 | **Fix the dangling Stage 3 symlink** (commands in §16.1) | 🔴 Critical |
| 2 | Restart backend + re-verify inspection | 🔴 Critical |
| 3 | Commit Review extraction + confirm `backend/config.py` deletion commit | 🟡 High |
| 4 | Portability fixes (YAML/SAHI standardization) | 🟡 High |
| 5 | Export Report button improvements | 🟡 High |
| 6 | `localStorage` persistence verification | 🟡 High |
| 7 | `git push` both repos | 🟡 High |

### 17.2 Phase 13: Desktop Packaging (Tauri)

| Task | Details |
|------|---------|
| Install Tauri CLI | `bun add @tauri-apps/cli` |
| Create Tauri config | `tauri.conf.json` |
| Bundle FastAPI backend | Include Python runtime |
| Create installer | macOS `.dmg`, Windows `.exe` |
| Test offline mode | Ensure no external dependencies |

### 17.3 ML Improvement Roadmap (Parallel to App)

| Step | Action |
|------|--------|
| 1 | **Leakage audit** between all datasets (mandatory) |
| 2 | Build leakage-free combined binary dataset |
| 3 | Retrain Stage 1 v2 (high-recall anomaly screener) |
| 4 | Implement inference-time rescue improvements |
| 5 | Human-reviewed hard-example mining |
| 6 | Retrain Stage 2 Model 6 with enriched data |
| 7 | Defer guided tiling (revisit if latency is a problem) |

### 17.4 Session Verdict

> Phase 12 shipped end-to-end, champions recovered from archive, cleanup ~90% done — one symlink fix stands between us and a clean restart.

---

*End of consolidated document.*
