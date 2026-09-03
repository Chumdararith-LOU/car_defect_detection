# Phase 4 — Safety Preset Calibration Report

Phase 4F end-to-end calibration of the `safety` preset on the MacBook M5
(MPS device) against the held-out calibration set: 593 defect images +
150 clean images (743 total), the same set used for the Phase 4D sweep.

## 1. Locked operating point

The `safety` preset is locked to the **per_class routing** configuration
committed in `6a29727`:

- **Routing**: `objectness_branch_new` + `baseline_m5`, `merge: per_class`.
  `corrosion`, `disjoint_part`, and `glass_shatter` are designated to
  `objectness_branch_new` only; `broken_lamp`, `crack`, `dent`, and
  `scratch` are undesignated, so both models contribute (union for recall).
- **Class rules**: `conf 0.25` for classes 0–4, `conf 0.10` for classes
  5–6 (corrosion, disjoint_part), with `min_area` preserved per class.
- **Two-tier gating** (objectness_branch_new only): `obj_threshold 0.20`,
  `cls_threshold 0.25`.

Measured live (full 743-image set, MPS):

- **FPR**: 54.0% (81/150 clean triggered)
- **Recall**: 92.9% (551/593 defect triggered)

## 2. Measured live operating points

| Configuration | Live FPR | Live Recall |
|---|---|---|
| Union merge (baseline) | 59.3% | 94.4% |
| per_class routing (locked) | 54.0% | 92.9% |
| Composite thresholds | 28.0% | 88.9% |
| Option-2 (aggressive recall recovery) | 35.3% | 89.4% |

## 3. Target gap

- **FPR**: +9pp over the 45% target (54.0% measured vs 45% target).
- **Recall**: −0.1pp below the 93% target (92.9% measured vs 93% target),
  within measurement noise.

No measured configuration hits both targets simultaneously. The
FPR/recall trade is structural, not a tuning artifact — every point that
pulls FPR under 45% costs enough recall to fall below 93%.

## 4. Why threshold tuning stopped

Offline replay over-predicts live recall by ~5.4pp because it cannot model
the live two-tier gating and cross-slice mask-IOS NMS. The offline sweep
predicted 94.8% recall for the Option-2 point, but live measurement
delivered 89.4%. Further threshold tuning cannot bridge this offline/live
gap. This is a known limitation of the current calibration tooling
(`scripts/sweep_routed_thresholds.py` replays raw detections without
simulating gating or NMS).

## 5. FPR floor & path to closing it

33 of 150 clean images (22%) emit detections at >= 0.60 confidence. No
confidence threshold can remove these — they are high-confidence
hallucinations. The fix requires hard-negative mining plus more clean
training data, which is currently blocked (no retraining server available).

## 6. Recall fallback

If a hard >= 93% recall floor is mandated, use **union routing** (the
Phase 4F baseline), which achieves 94.4% recall at 59.3% FPR.
