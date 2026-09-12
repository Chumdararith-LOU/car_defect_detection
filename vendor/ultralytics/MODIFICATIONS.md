# Ultralytics Fork Modifications

> ⚠️ **CRITICAL WARNING**: This is a MODIFIED fork of Ultralytics.
> Do NOT run `pip install ultralytics` — it will overwrite these modifications.
> Always use: `pip install -e vendor/ultralytics` (editable install)

## Base Version

- **Ultralytics Version**: 8.4.90
- **Fork Date**: 2026-09-11
- **Fork Reason**: Custom loss functions and objectness branch integration
- **Repository**: https://github.com/Chumdararith-LOU/car_defect_detection

## Modified Files

### 1. `ultralytics/utils/loss.py`

**What was modified:**
- Added `SeesawBCE` class (line ~89) for long-tailed instance segmentation
- Modified `v8SegmentationLoss.__init__` to inject custom loss functions based on `model.args["loss_type"]`
- Modified `v8SegmentationLoss.__call__` to compute objectness loss when `model.args["use_objectness"]` is True
- Modified `E2ELoss.__call__` for end-to-end objectness loss computation

**Why:**
The standard Ultralytics loss pipeline only supports BCE for classification.
Our car defect detection pipeline requires:
1. **Seesaw Loss** for handling class imbalance (7 defect classes with 31:1 ratio)
2. **Scaled Focal Loss** for hard example mining
3. **Objectness branch** for two-tier gating (reduces false positives on clean cars)

**How it works:**
```python
# In v8SegmentationLoss.__init__:
loss_type = model.args.get("loss_type", "bce")
if loss_type == "seesaw":
    self.bce = SeesawBCE(p=model.args["seesaw_p"], q=model.args["seesaw_q"])
elif loss_type == "focal":
    self.bce = ScaledFocalBCEWithLogitsLoss(...)
else:
    self.bce = nn.BCEWithLogitsLoss(reduction="none")  # standard

# In v8SegmentationLoss.__call__:
if model.args.get("use_objectness", False):
    obj_loss = compute_objectness_loss(preds, batch)
    loss += obj_loss * model.args["obj_loss_weight"]
```

**Parameters injected via `model.args`:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `loss_type` | str | "bce" | Loss function: "bce", "focal", "seesaw" |
| `fl_gamma` | float | 1.5 | Focal loss gamma |
| `fl_alpha` | float | 0.50 | Focal loss alpha |
| `fl_scale` | float | 1.0 | Focal loss scale |
| `seesaw_p` | float | 0.8 | Seesaw mitigation exponent |
| `seesaw_q` | float | 2.0 | Seesaw compensation exponent |
| `use_objectness` | bool | False | Enable objectness branch |
| `obj_loss_weight` | float | 1.0 | Objectness loss weight |

### 2. `ultralytics/nn/modules/head.py`

**What was modified:**
- Added `Segment26WithObjectness` class (imported from `src/models/segment_head_with_obj.py`)
- This class extends the standard `Segment26` head with an additional objectness prediction branch

**Why:**
The objectness branch provides a separate "is there any defect here?" prediction
that is independent of the class prediction. This enables two-tier gating:
```
final_score = P(class) × P(objectness)
```
This dramatically reduces false positives on clean cars (FPR dropped from 40.94% to 35.43%).

**Architecture:**
```
Standard Segment26 Head:
├── cv2: Box regression (4 × reg_max channels per FPN level)
├── cv3: Class prediction (nc channels per FPN level)
├── cv4: Mask coefficients (nm channels per FPN level)
└── proto: Prototype masks (32 channels)

Segment26WithObjectness (ADDED):
├── cv2: Box regression (unchanged)
├── cv3: Class prediction (unchanged)
├── cv4: Mask coefficients (unchanged)
├── proto: Prototype masks (unchanged)
└── obj: Objectness prediction (1 channel per FPN level) ← NEW
```

### 3. `ultralytics/nn/tasks.py`

**What was modified:**
- Registered `Segment26WithObjectness` in the model task registry
- This allows YOLO to recognize and load models with the objectness head

**Why:**
Without this registration, YOLO would fail to load models saved with
the objectness head, throwing a `KeyError` or `AttributeError`.

## Loss Function Decision Matrix

| Config Setting | Loss Used | When to Use |
|---|---|---|
| `loss_type: bce` | Standard BCE | Baseline, balanced datasets |
| `loss_type: focal` | ScaledFocalBCEWithLogitsLoss | Hard examples dominate |
| `loss_type: seesaw` | SeesawBCE | Long-tailed class distribution |

**IMPORTANT**: Seesaw Loss was REJECTED after experimental evaluation.
Plain BCE outperformed all Seesaw configurations by >2× on the 20% subset.
Keep SeesawBCE for reference only. Default to `loss_type: bce`.

## Objectness Branch Usage

To enable the objectness branch in training:
```yaml
# In your training config YAML:
use_objectness: true
obj_loss_weight: 1.0
model_preset: yolo26m-seg.pt  # Will be replaced with Segment26WithObjectness
```

The training script (`src/train/train.py`) automatically:
1. Replaces the standard head with `Segment26WithObjectness`
2. Copies weights from the original head (cv2, cv3, cv4, proto)
3. Injects objectness loss into the training loop via `model.args`

## Verification

To verify the fork is correctly installed:
```python
from ultralytics.utils.loss import SeesawBCE
print("✅ SeesawBCE available")

from ultralytics.nn.modules.head import Segment26WithObjectness
print("✅ Segment26WithObjectness available")
```

To verify loss injection works:
```python
from ultralytics import YOLO
model = YOLO("yolo26m-seg.pt")
model.args["loss_type"] = "seesaw"
model.args["seesaw_p"] = 0.8
model.args["seesaw_q"] = 2.0
# Train and check for "[🔥] SEESAW LOSS INJECTED" in logs
```

## Upgrading Ultralytics

If you need to upgrade the base Ultralytics version:

1. **DO NOT** simply `pip install ultralytics==X.Y.Z`
2. Create a new branch: `git checkout -b upgrade-ultralytics`
3. Download the new version source
4. Manually re-apply the modifications listed above
5. Run the evaluation smoke test to verify nothing broke
6. Update this document with the new version number

## Files Modified Summary

| File | Lines Changed | Purpose |
|---|---|---|
| `ultralytics/utils/loss.py` | ~150 added | SeesawBCE + loss injection |
| `ultralytics/nn/modules/head.py` | ~5 added | Import Segment26WithObjectness |
| `ultralytics/nn/tasks.py` | ~3 added | Register objectness head |

## Related Project Files

| File | Relationship |
|---|---|
| `src/models/losses.py` | Defines ScaledFocalBCEWithLogitsLoss (imported by fork) |
| `src/models/segment_head_with_obj.py` | Defines Segment26WithObjectness (imported by fork) |
| `src/train/train.py` | Injects loss params into model.args |
| `configs/train/stage2/*.yaml` | Training configs with loss_type settings |

## References

- Seesaw Loss paper: https://arxiv.org/abs/2008.10032
- eval.md Module 20: The 10 Commandments of Industrial ML
- HANDOVER.md: Experiment history and design decisions
