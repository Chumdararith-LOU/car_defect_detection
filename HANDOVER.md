# Handover Notes

> Last updated: 2026-09-11
> Branch: cleanup/workspace-refactor
> Status: Production model deployed; evaluation harness complete; repository cleaned for handover.

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

## Evaluation Pipeline (Stage 2)

The Stage 2 evaluation harness provides comprehensive model assessment:

### Usage

```bash
# Full evaluation with all metrics
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml

# Specific mode
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml --mode clean_fpr

# Single model evaluation
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml --model path/to/weights.pt
```

### Metrics Computed

| Category | Metrics | Module |
|---|---|---|
| Accuracy | Per-class P/R/F1/AP50 | `metrics/classwise.py` |
| Size Analysis | Small/Medium/Large AP & Recall | `metrics/size_bucketed.py` |
| Production FPR | False positives on clean images | `metrics/clean_fpr.py` |
| Latency | Preprocess/Inference/NMS timing | `perf/latency.py` |
| Memory | Peak VRAM/RAM | `perf/memory.py` |

### Key Design Decisions

1. **Size-bucketed metrics** (Commandment #1): Aggregate mAP hides small-object failures. We report AP separately for small (<32²), medium (32²-96²), and large (>96²) objects.

2. **Clean FPR as production metric**: A model that hallucinates on clean cars erodes operator trust. We measure FPR on 150 defect-free images.

3. **NMS with IOS metric**: Thin boxes (scratches) have low IoU even for duplicates. IOS (Intersection over Smaller) correctly merges them.

4. **SAHI tiling at inference**: Patch size MUST match training resolution (1024×1024). Mismatched resolution causes silent performance degradation.

### Evaluation Configs

| Config | Purpose |
|---|---|
| `configs/eval/stage2_benchmark.yaml` | Multi-model comparison |
| `configs/eval/clean_images.yaml` | FPR-focused testing |
| `configs/eval/smoke_test.yaml` | End-to-end verification |

## Evaluation Pipeline (Stage 3)

Stage 3 (Panel Segmentation) evaluation is under development. The planned approach:

1. **Panel-level metrics**: IoU between predicted and ground-truth panel masks
2. **Defect-to-panel assignment accuracy**: Percentage of defects correctly assigned to panels
3. **Integration test**: Full pipeline (Stage 2 → Stage 3 → Stage 4) accuracy

## Updated File Index

| Path | What it is |
|---|---|
| `configs/train/stage2/Stage2-training.yaml` | Main production training config |
| `configs/train/stage2/objectness_branch.yaml` | Objectness branch model config |
| `configs/eval/stage2_benchmark.yaml` | Evaluation benchmark config |
| `src/train/train.py` | Training entry point |
| `src/stage2/eval/evaluate.py` | Evaluation entry point |
| `src/stage2/eval/sahi_eval.py` | SAHI inference wrapper |
| `src/stage2/eval/metrics/classwise.py` | Per-class metrics |
| `src/stage2/eval/metrics/size_bucketed.py` | Size-bucketed metrics |
| `src/stage2/eval/metrics/clean_fpr.py` | Clean FPR metrics |
| `src/stage2/eval/perf/latency.py` | Latency profiling |
| `src/stage2/eval/perf/memory.py` | Memory profiling |
| `src/stage2/eval/report.py` | Report generation |
| `src/models/losses.py` | Custom loss functions |
| `src/models/segment_head_with_obj.py` | Objectness head |
| `vendor/ultralytics/MODIFICATIONS.md` | Fork documentation |
| `data/processed/yolo_seg_clean/` | Unified 7-class dataset |
| `data/processed/clean_cars/` | Clean-car pool |
| `archive/experiment_configs/` | Archived superseded configs |
| `archive/experiment_scripts/` | Archived dead scripts |

## Lessons Learned (Evaluation)

1. **Aggregate metrics lie for rare events** — Always check size-bucketed recall, not just mAP.

2. **Clean FPR is the production killer** — A model with 90% recall but 40% FPR will be rejected by operators.

3. **SAHI patch size must match training resolution** — Mismatched resolution looks like under-training but is actually an inference config bug.

4. **IOS beats IoU for thin boxes** — Scratches have low IoU even for duplicates. Use IOS for NMS.

5. **Latency budget is 500ms** — 48 patches × ~8ms + 50ms NMS. Exceeding this breaks the production constraint.

## Inference Pipeline — Objectness Head Registration

Stage 2 inference uses SAHI via `src/stage2/inference/sahi_inference.py`.

Models trained with the objectness branch (e.g., `objectness_branch_new`,
`seesaw_surgical_objectness-26`) use the custom `Segment26WithObjectness` head.
To load these models for inference, the head class must be registered into
Ultralytics before deserialization.

`sahi_inference.py` does this automatically at import time: it registers
`Segment26WithObjectness` into `ultralytics.nn.modules.head` and
`ultralytics.nn.tasks`, mirroring the registration in `src/stage2/train/train.py`.

**Why this matters:** Without this registration, loading an objectness-trained
model would fail or silently drop the objectness branch. This registration
preserves the champion model's objectness branch (which reduced clean-image FPR
from 40.94% to 35.43%) during inference.
