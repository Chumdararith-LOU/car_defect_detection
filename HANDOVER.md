# Handover Notes

> Last updated: 2026-07-11
> Branch: cleanup/workspace-refactor
> Status: Production model deployed; repository cleaned for handover.

## Key Results Summary

| Metric | Baseline (Model 5) | Final (objectness_branch) | Change |
|---|---|---|---|
| SAHI Mask mAP50 | 63.65% | 66.91% | +3.26 |
| Corrosion mAP50 | 6.70% | 69.29% | +62.59 (10.3x) |
| Clean-Image FPR | 40.94% | 35.43% | -5.51 |
| Detection Rate | 70.32% | 90.72% | +20.40 |

## Experiment History

| # | Experiment | Result | Key Lesson |
|---|---|---|---|
| 1 | Hard-Negative Injection | ❌ FAILED | Empty-label gradients overwhelm rare-class positives without protective loss |
| 2 | Seesaw Loss Baseline | ✅ Partial | Reduced FPR but BCE control later outperformed it |
| 3 | Copy-Paste Augmentation | ⚠️ REGRESSED | Frozen backbone can't adapt to pasted contexts |
| 4 | Seesaw + Surgical Early | ✅ Champion | Synergistic: Seesaw=gradient signal, Surgical=capacity |
| 5 | NWD Integration | ❌ FAILED | Engineering bugs (shape/format mismatch), not method failure |
| 6 | Objectness Branch | ✅ Production | Two-tier gating (obj × class) suppresses FPs |
| 7 | Seesaw p/q Sweep (9 cells) | ❌ REJECTED | Plain BCE control beat every Seesaw cell by >2x |

## Critical Design Decisions

1. Corrosion is the HEAD class (13,961 instances), not a rare class.
   The initial hypothesis (tiny + rare) was wrong. The real problem was
   feature/texture learning, addressed by surgical fine-tuning of early layers.

2. Plain BCE outperforms Seesaw Loss on this dataset.
   The 7-class, 31:1 imbalance regime does not benefit from Seesaw's
   mitigation/compensation factors. They destabilize gradients on the
   frozen-backbone subset.

3. Surgical fine-tuning of early layers (0-4) is essential for corrosion.
   Corrosion is a texture defect. Early layers detect edges/textures;
   deep layers detect semantics. Unfreezing early layers gives the model
   capacity to learn rust patterns while preserving car-geometry features.

4. SAHI inference is mandatory for high-resolution images.
   Training at 1024x1024 and inferring on 1024x1024 slices with 15%
   overlap recovers small defects that full-image inference misses.

5. Objectness branch + two-tier gating is the production FPR solution.
   final_score = P(class) × P(objectness). Detections are kept only if
   both exceed their thresholds.

## Known Limitations

- Clean-image FPR floor: ~22% of clean images emit high-confidence
  hallucinations (reflections, shadows, water spots). Requires hard-negative
  mining + retraining or a PaDiM anomaly gate.
- Head-class regression: surgical fine-tuning slightly hurt broken_lamp
  (-14.42 mAP50) and crack (-15.12). Mitigated by multi-model routing.
- Disjoint_part val noise: only 33 val instances → per-class metrics unstable.

## Recommended Next Steps

1. Hard-negative Round 2: inject 3-5% clean images with Seesaw protection
   (or plain BCE + early stopping on corrosion recall).
2. Proper NWD integration: custom BboxLoss class, not monkey-patching.
3. P2 detection head: stride-4 features for corrosion (currently sub-pixel at P3+).
4. SAHI training integration: train on slices, not just infer on them.
5. Panel segmentation: Stage 3 is still under development.

## File Index (for quick reference)

| Path | What it is |
|---|---|
| configs/train/stage2/Stage2-training.yaml | Main production training config |
| configs/train/stage2/objectness_branch.yaml | Objectness branch model config |
| vendor/ultralytics/ | Forked Ultralytics 8.4.90 with custom modifications |
| data/processed/yolo_seg_clean/ | Unified 7-class dataset (YOLO format) |
| data/processed/clean_cars/ | Clean-car pool (train + eval) |
| archive/experiment_configs/ | Archived superseded experiment configs |
| archive/experiment_scripts/ | Archived dead experiment scripts |
