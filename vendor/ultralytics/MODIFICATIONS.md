# Ultralytics Modifications for Car Defect Detection

Base version: 8.4.90
Fork date: 2026-09-06
Dataset: yolo_seg_clean (7 classes, alphabetical order)

## Modification Log

### 2026-09-06: Seesaw Loss (`SeesawBCE`)

- Added `SeesawBCE` class in `ultralytics/utils/loss.py`: seesaw-reweighted multi-label
  BCE with mitigation factor (`p`, protects tail classes from head-class negative
  gradients) and compensation factor (`q`, punishes confident false positives,
  clamped at 5.0). Returns element-wise loss to stay compatible with the
  `target_scores_sum` normalization in the detection losses.
- `v8DetectionLoss.__init__` reads `seesaw_p`/`seesaw_q` from `model.args`
  (dict or namespace). When both are set, the classification `self.bce` becomes
  `SeesawBCE`. Note: in 8.4.90 the classification BCE lives in `v8DetectionLoss`,
  not `BboxLoss`; `v8SegmentationLoss` inherits it.
- Added `seesaw_p: null` / `seesaw_q: null` to `ultralytics/cfg/default.yaml`
  and registered both in `CFG_FLOAT_KEYS` (`ultralytics/cfg/__init__.py`) so
  `seesaw_p=X seesaw_q=Y` overrides are accepted by the cfg parser.
