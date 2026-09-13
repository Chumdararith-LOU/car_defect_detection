# MASTER CONTEXT DOCUMENT — Car Defect Detection Project
Last Updated: 2026-07-11
Purpose: Restore full context for any AI session working on this project.

═══════════════════════════════════════════════════════
SECTION 1: PROJECT IDENTITY
═══════════════════════════════════════════════════════

Project: Automated Car Body Defect Detection
Author: Intern student (Chumdararith-LOU)
Institution: ITC (Institute of Technology of Cambodia)
Supervisor: [Advisor Name]
Branch: cleanup/workspace-refactor
Remote: https://github.com/Chumdararith-LOU/car_defect_detection.git

Repository Path (Project):
/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection

Repository Path (Testing — to be deleted after consolidation):
/Users/macbook/Documents/ITC8/Internship/AI Farm/Testing/car_defect_detection

═══════════════════════════════════════════════════════
SECTION 2: PROJECT GOAL
═══════════════════════════════════════════════════════

Primary Goal: Prepare this repository for handover to a successor (intern).
The successor should be able to:
  1. git clone the repository
  2. Follow the README
  3. Run training and evaluation without reverse-engineering anything

Secondary Goals:
  - Clean, standardized directory structure
  - One canonical entry point for training each stage
  - One canonical entry point for evaluation each stage
  - Well-documented vendored Ultralytics modifications
  - Comprehensive HANDOVER.md with experiment history

═══════════════════════════════════════════════════════
SECTION 3: ARCHITECTURE OVERVIEW (4-Stage Pipeline)
═══════════════════════════════════════════════════════

Stage 1: Pre-Screener (SOD)
  - Binary saliency detector
  - Routes clean cars to PASS
  - Model: YOLO-based binary classifier
  - Loss: Focal Loss (gamma=1.5, alpha=0.50)

Stage 2: Defect Segmentation (THIS IS THE FOCUS)
  - Multi-class instance segmentation (7 defect types)
  - Model: YOLO-seg (Ultralytics 8.4.90, vendored fork)
  - Custom modifications: Objectness branch, SeesawBCE loss
  - Inference: SAHI (1024x1024 slices, 15% overlap, Mask-IoS NMS)

Stage 3: Panel Mapping
  - Assigns defects to specific car panels
  - Model: Panel segmentation (YOLO-seg based)

Stage 4: Fusion & Severity
  - Computes IoD (Intersection-over-Defect)
  - Computes DSI (Damage Severity Index)
  - Rule-based geometric fusion

═══════════════════════════════════════════════════════
SECTION 4: DEFECT TAXONOMY (7 Classes)
═══════════════════════════════════════════════════════

ID 0: broken_lamp    (502 train instances, TAIL)
ID 1: corrosion      (13,961 train instances, HEAD)
ID 2: crack          (761 train instances, TAIL)
ID 3: dent           (3,440 train instances, MID)
ID 4: disjoint_part  (1,838 train instances, MID)
ID 5: glass_shatter  (440 train instances, TAIL)
ID 6: scratch        (6,384 train instances, MID)

Class ordering: ALPHABETICAL (this is the corrected order)
Previous BUG: Old CarDD ordering (0:dent, 1:scratch, 2:crack, ...)
caused class-index misalignment in Model 4 and Model 5.

═══════════════════════════════════════════════════════
SECTION 5: KEY EXPERIMENTAL FINDINGS (CRITICAL)
═══════════════════════════════════════════════════════

FINDING 1: Seesaw Loss was REJECTED
  - Plain BCE control beat all 9 Seesaw configs by >2x on 20% subset
  - Best Seesaw (p=0.6, q=1.5): 0.211 mAP50 vs BCE control: 0.449 mAP50
  - Reason: Dataset is 7 classes (not 1203 like LVIS); the 31:1 imbalance
    does not benefit from Seesaw's mitigation/compensation factors
  - Decision: Use plain BCE as default loss

FINDING 2: Corrosion is the HEAD class (not rare)
  - 13,961 instances (most in dataset)
  - NOT a long-tail/rare-class problem
  - The real problem is TEXTURE/FEATURE LEARNING
  - Corrosion is a texture defect requiring early-layer adaptation

FINDING 3: Surgical Fine-Tuning (early_texture) is CRITICAL
  - Unfreezing layers 0-4 + head gives capacity to learn corrosion textures
  - Based on Lee et al. "Surgical Fine-Tuning" paper:
    Input-level shifts (textures) → tune FIRST layers
  - This drove the 10.3x corrosion improvement

FINDING 4: Objectness Branch provides FPR suppression
  - Two-tier gating: final_score = P(class) × P(objectness)
  - Reduces clean-image false positives
  - Must be wired via source modification (not monkey-patch)

FINDING 5: Hard-Negative Injection previously FAILED
  - Without Seesaw protection, clean images overwhelmed corrosion signal
  - "Shy Model" effect: model learned "when uncertain, predict nothing"
  - Can be retried CAREFULLY with monitoring (3-5% clean images)

FINDING 6: Monkey-patching Ultralytics is FRAGILE
  - Caused E2ELoss silent failure (objectness branch never trained)
  - Solution: Source modification of vendored Ultralytics
  - vendor/ultralytics is now the canonical source

═══════════════════════════════════════════════════════
SECTION 6: BEST RESULTS ACHIEVED
═══════════════════════════════════════════════════════

Baseline (Model 5):
  SAHI Mask mAP50: 63.65%
  Corrosion mAP50: 6.70%
  Clean-Image FPR: 40.94%
  Detection Rate: 70.32%

Champion (objectness_branch_new):
  SAHI Mask mAP50: 66.91%
  Corrosion mAP50: 69.29% (10.3x improvement)
  Clean-Image FPR: 35.43%
  Detection Rate: 90.72%

Per-Class mAP50 (objectness_branch_new):
  dent: 79.15%
  scratch: 42.89%
  crack: 43.84%
  glass_shatter: 47.66%
  broken_lamp: 34.42%
  corrosion: 96.99%
  disjoint_part: 32.42%

═══════════════════════════════════════════════════════
SECTION 7: VENDORED ULTRALYTICS MODIFICATIONS
═══════════════════════════════════════════════════════

Location: vendor/ultralytics/
Base Version: Ultralytics 8.4.90
Install: pip install -e vendor/ultralytics (editable mode)

Modified Files:
1. ultralytics/utils/loss.py
   - Added SeesawBCE class (kept for reference, NOT production default)
   - Loss injection logic in v8SegmentationLoss.__init__
   - Objectness loss wiring in v8SegmentationLoss.__call__
   - Objectness loss wiring in E2ELoss.__call__
   - loss_type parameter: "focal" | "seesaw" | "bce" (default: bce)

2. ultralytics/nn/modules/head.py
   - Added Segment26WithObjectness class
   - 1x1 conv branches per FPN level for objectness prediction
   - Bias initialization: -2.0 (sigmoid(-2) ≈ 0.12, favors background)

CRITICAL WARNING:
  Do NOT run `pip install ultralytics` — it will overwrite the fork.
  Always use the editable install from vendor/ultralytics.

═══════════════════════════════════════════════════════
SECTION 8: TRAINING CONFIGURATION
═══════════════════════════════════════════════════════

Production Config: configs/train/stage2/Stage2-training.yaml
Objectness Config: configs/train/stage2/objectness_branch.yaml
Baseline Config: configs/train/stage2/model5_stage1_head_warmup_7cls_extended.yaml

Key Hyperparameters:
  - loss_type: bce (NOT seesaw — rejected)
  - surgical_mode: early_texture (layers 0-4 + head unfrozen)
  - optimizer: AdamW
  - lr0: 0.001
  - lrf: 0.01
  - epochs: 100 (early stopping, patience=20)
  - imgsz: 1024
  - batch: 8
  - amp: true (CUDA), false (MPS)

SAHI Inference:
  - slice_size: 1024x1024
  - overlap_ratio: 0.15
  - NMS: Mask-IoS, threshold 0.50
  - device: mps (MacBook) or cuda (server)

═══════════════════════════════════════════════════════
SECTION 9: RESEARCH PAPERS IN KNOWLEDGE BASE
═══════════════════════════════════════════════════════

1. NWD (Normalized Wasserstein Distance) for Tiny Objects — Wang et al. 2021
2. Fine-Tuning can Distort Pretrained Features — Kumar et al. ICLR 2022
3. Corrosion Segmentation (Semi-supervised) — Wang et al. SHM 2025
4. Copy-Paste Augmentation — Ghiasi et al. CVPR 2021
5. SOD-YOLO (Lightweight Small Object Detection) — Xiao et al. 2024
6. CrashCar101 (Procedural Damage Generation) — Parslov et al. WACV 2024
7. SAHI (Slicing Aided Hyper Inference) — Akyon et al. ICIP 2022
8. Seesaw Loss for Long-Tailed Instance Segmentation — Wang et al. CVPR 2021
9. Surgical Fine-Tuning — Lee et al. ICLR 2023
10. Detecting Tiny Objects in Aerial Images (NWD-RKA) — Xu et al. 2022
11. SOLOv2 (Dynamic and Fast Instance Segmentation) — Wang et al. NeurIPS 2020

═══════════════════════════════════════════════════════
SECTION 10: WHAT HAS BEEN DONE (COMPLETED WORK)
═══════════════════════════════════════════════════════

PHASE 0: Git Pre-flight ✅
  - Project directory on cleanup/workspace-refactor branch
  - Working tree clean

PHASE 1: Cleanup & Archiving ✅
  - Safety snapshot committed
  - Dead experiment scripts archived → archive/experiment_scripts/
  - Superseded configs archived → archive/experiment_configs/
  - .gitignore updated
  - README.md rewritten
  - HANDOVER.md created

PHASE 2: Consolidation (Partially Done)
  - SeesawBCE extracted from Testing train.py
  - Loss injection code written into vendor/ultralytics/ultralytics/utils/loss.py
  - Segment26WithObjectness defined in src/models/heads.py
  - Loss functions: ScaledFocalBCEWithLogitsLoss in src/models/losses.py
  - Testing directory NOT YET deleted (waiting for verification)

PHASE 3: Source Modification (Mostly Done)
  - v8SegmentationLoss.__init__ modified for loss injection
  - v8SegmentationLoss.__call__ modified for objectness loss
  - E2ELoss.__call__ modified for objectness loss
  - Printing statements added for verification

═══════════════════════════════════════════════════════
SECTION 11: WHAT REMAINS TO BE DONE
═══════════════════════════════════════════════════════

TODO 1: Verify Source Modifications Work
  - Run a quick 1-epoch training to confirm loss injection prints
  - Verify objectness loss appears in training logs
  - Confirm no NaN or divergence

TODO 2: Standardize Training Entry Points
  - Create src/stage2/train.py (single entry point)
  - Create src/stage3/train.py (single entry point)
  - Config-driven (all hyperparams in YAML)
  - No hardcoded paths

TODO 3: Standardize Evaluation Entry Points
  - Create src/stage2/evaluate.py
  - Create src/stage3/evaluate.py
  - Should output: per-class mAP50/mAP50-95, FPR, detection rate
  - Save results to report file

TODO 4: Configuration Cleanup
  - Rename configs for clarity
  - Ensure all paths are relative or from .env
  - Remove any hardcoded absolute paths
  - Create .env.example

TODO 5: Document Vendored Fork
  - Create vendor/ultralytics/MODIFICATIONS.md
  - Document every modified file, what changed, and why
  - Include verification steps

TODO 6: Final Documentation
  - Update README with standardized commands
  - Update HANDOVER.md with final experiment results
  - Add docs/architecture.md
  - Add docs/training_guide.md

TODO 7: Clone-and-Run Verification
  - Create scripts/verify_setup.py
  - Test that a fresh clone can train and evaluate
  - Fix any path issues discovered

TODO 8: Delete Testing Directory
  - After ALL verification passes
  - Remove /Users/macbook/Documents/ITC8/Internship/AI Farm/Testing/car_defect_detection

═══════════════════════════════════════════════════════
SECTION 12: IMPORTANT LESSONS & WARNINGS
═══════════════════════════════════════════════════════

WARNING 1: Do NOT monkey-patch Ultralytics
  - Use source modifications in vendor/ultralytics
  - Monkey-patching caused E2ELoss silent failure

WARNING 2: Do NOT use Seesaw Loss as default
  - BCE control outperformed Seesaw by 2x
  - Seesaw kept only for reference/experimentation

WARNING 3: Hard-Negative Injection requires CARE
  - Can cause "shy model" (corrosion recall drops)
  - Use only 3-5% clean images
  - Monitor corrosion recall closely

WARNING 4: Class ordering is ALPHABETICAL
  - 0:broken_lamp, 1:corrosion, 2:crack, 3:dent,
    4:disjoint_part, 5:glass_shatter, 6:scratch
  - Old CarDD ordering (0:dent) is WRONG and DEPRECATED

WARNING 5: MPS (MacBook) does NOT support amp=True
  - amp causes NaN divergence on MPS
  - Use amp=false on MacBook, amp=true on CUDA server

LESSON 1: Corrosion needs SURGICAL FINE-TUNING
  - Unfreeze early layers (0-4) + head
  - This gives capacity to learn texture features

LESSON 2: The 705-line train.py was a "god script"
  - It mixed training, evaluation, patching, and configuration
  - Must be decomposed into modular entry points

LESSON 3: SAHI is MANDATORY for high-resolution inference
  - Training at 1024x1024, inferring on full images loses small defects
  - SAHI slices recover what full-image inference misses

═══════════════════════════════════════════════════════
SECTION 13: FILE STRUCTURE (CURRENT STATE)
═══════════════════════════════════════════════════════

car_defect_detection/
├── README.md                    # Rewritten (done)
├── HANDOVER.md                  # Created (done)
├── .gitignore                   # Updated (done)
├── .env.example                 # TODO: Create
├── requirements.txt
├── requirements-dev.txt
├── configs/
│   ├── data/stage2/
│   ├── train/stage1/stage1-sod.yaml
│   ├── train/stage2/
│   │   ├── Stage2-training.yaml       # Production config
│   │   ├── objectness_branch.yaml     # Objectness model config
│   │   └── model5_stage1_head_warmup_7cls_extended.yaml
│   ├── train/stage3/
│   └── inference/sahi_production.yaml
├── src/
│   ├── models/
│   │   ├── heads.py             # Segment26WithObjectness
│   │   └── losses.py            # ScaledFocalBCEWithLogitsLoss
│   ├── training/
│   │   ├── callbacks.py         # Freeze/unfreeze logic
│   │   └── patches.py           # DEPRECATED (keep minimal)
│   ├── stage1/
│   │   ├── data/
│   │   ├── deploy/
│   │   ├── diagnostics/
│   │   ├── eval/
│   │   ├── inference/
│   │   ├── tests/
│   │   ├── train/
│   │   └── utils/
│   ├── stage2/
│   │   ├── Resume-and-Adapt/
│   │   ├── annotation/
│   │   ├── data/
│   │   ├── eval/
│   │   ├── inference/sahi_inference.py
│   │   ├── models/
│   │   └── train/train.py       # TODO: Refactor
│   ├── stage3/
│   │   ├── data/
│   │   ├── eval/
│   │   └── train/train.py       # TODO: Refactor
│   ├── stage4/
│   │   ├── batch_mapping_test.py
│   │   └── spatial_context_mapper.py
│   ├── train/train.py           # 705-line god script (TODO: Remove)
│   └── training/
│       ├── callbacks.py
│       └── patches.py
├── vendor/
│   └── ultralytics/             # Forked 8.4.90 (MODIFIED)
│       └── MODIFICATIONS.md     # TODO: Create
├── backend/                     # FastAPI on port 8010
├── frontend/                    # Bun frontend
├── docs/                        # TODO: Populate
├── scripts/
│   └── setup_models.py
├── archive/
│   ├── experiment_scripts/
│   └── experiment_configs/
├── data/
│   └── processed/
│       ├── yolo_seg_clean/
│       └── clean_cars/
└── runs/                        # Training outputs (gitignored)

═══════════════════════════════════════════════════════
SECTION 14: IMMEDIATE NEXT STEPS
═══════════════════════════════════════════════════════

1. Verify source modifications with a 1-epoch training run
2. Create standardized train.py and evaluate.py for Stage 2
3. Create standardized train.py and evaluate.py for Stage 3
4. Clean up and rename configs
5. Create vendor/ultralytics/MODIFICATIONS.md
6. Create scripts/verify_setup.py
7. Update final documentation
8. Run clone-and-run test
9. Delete Testing directory

═══════════════════════════════════════════════════════
END OF MASTER CONTEXT DOCUMENT
═══════════════════════════════════════════════════════
