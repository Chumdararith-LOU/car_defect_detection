
## 1. Design Philosophy (from your professor's Commandments)

Your evaluation entry point must encode these hard-won lessons, or it will repeat the exact bugs your professor documented:

| Commandment | How the Eval Harness Enforces It |
|---|---|
| **#1 Aggregate Metrics Lie** | Report **size-bucketed** (small/medium/large) recall + per-class metrics, never just a single mAP |
| **#2 Bypass the API for Truth** | Add a `--raw-logits` mode that inspects pre-threshold probabilities |
| **#3 Match Activation to Loss** | Auto-detect BCE→Sigmoid vs CE→Softmax from the training config, warn on mismatch |
| **#7 Focal Loss ≠ Missing Features** | Separate "signal weak" (low conf) from "signal absent" (≈0 conf) in diagnostics |
| **#10 Hypothesis→Diagnose→Fix** | Every eval run writes a structured diagnostic report, not just numbers |

---

## 2. The 4 Evaluation Modes You Asked For

Design **one entry point** with a `--mode` flag, so the intern learns one command:

```bash
python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml
```

| Mode | What it measures | Answers the question |
|---|---|---|
| `benchmark` | mAP50/50-95 (box+mask), per-class, size-bucketed | "Which model is most accurate?" |
| `clean_fpr` | False positives on defect-free images | "Will this model hallucinate on clean cars?" |
| `latency` | preprocess / inference / NMS / SAHI wall-clock + FPS | "Is it fast enough for production?" |
| `memory` | Peak GPU/RAM, per-patch VRAM | "Will it fit on the target hardware?" |
| `full` *(default)* | Runs all four, writes a combined report | "Give me the complete picture" |

---

## 3. Proposed File Structure

Keep it **modular** so each concern is isolated (critical for the 27B opencode context window — one file = one micro-task):

```
src/stage2/eval/
├── __init__.py
├── evaluate.py              # ← THE single entry point (thin orchestrator, <120 lines)
├── metrics/
│   ├── __init__.py
│   ├── size_bucketed.py     # Commandment #1: small/medium/large AP + recall
│   ├── clean_fpr.py         # false-positive-rate on clean images
│   └── classwise.py         # per-class P/R/mAP tables
├── perf/
│   ├── __init__.py
│   ├── latency.py           # timing: preprocess/infer/NMS/SAHI
│   └── memory.py            # peak VRAM/RAM (handles CUDA + MPS + CPU)
├── sahi_eval.py             # SAHI tiling wrapper reused for all modes
└── report.py                # writes Markdown + JSON + MLflow logging

configs/eval/
├── stage2_benchmark.yaml    # main config (models, data, thresholds)
└── clean_images.yaml        # clean-image set definition for FPR
```

**Why this split matters for opencode:** each module is small and self-contained, so you can hand opencode *one file at a time* without blowing its context.

---

## 4. Config Schema (`configs/eval/stage2_benchmark.yaml`)

```yaml
mode: full                      # benchmark | clean_fpr | latency | memory | full
project_name: car_defect_eval
run_name: model_comparison_v1

# ── Models to compare (the benchmark core) ──
models:
  - name: objectness_branch
    weights: runs/segment/seesaw_surgical_objectness-26/weights/best.pt
  - name: seesaw_surgical_early
    weights: runs/segment/seesaw_surgical_early/weights/best.pt
  - name: baseline_bce
    weights: runs/segment/stage1_head_warmup_7cls_extended/weights/best.pt

# ── Datasets ──
data:
  test: data/processed/yolo_seg_clean/data.yaml
  clean_images: data/processed/clean_cars/images/clean_eval/   # for FPR mode
  clean_count: 150

# ── SAHI (must match training resolution — Module 8 Native Resolution Rule) ──
sahi:
  enabled: true
  slice_size: 1024
  overlap_ratio: 0.15
  postprocess_match_metric: IOS        # Commandment: IOS not IoU for thin scratches
  postprocess_match_threshold: 0.50

# ── Inference ──
inference:
  conf_threshold: 0.25
  imgsz: 1024
  device: auto                          # cuda > mps > cpu
  amp: false                            # avoid NaN on MPS (your earlier finding)

# ── Output ──
output:
  report_dir: reports/eval/
  log_to_mlflow: true
  save_json: true
```

---

## 5. The Metrics Each Mode Produces

### `benchmark` mode (Commandment #1 — never trust a single number)
```
Per model, per class (7 classes):
  box:   P, R, mAP50, mAP50-95
  mask:  P, R, mAP50, mAP50-95
Size-bucketed:
  AP_small (<32²), AP_medium (32²–96²), AP_large (>96²)
  Recall_small / Recall_medium / Recall_large   ← catches rare-event failures
```

### `clean_fpr` mode (the production killer)
```
total_clean_images: 150
images_with_fp: 47
FPR (%): 31.3
total_false_positives: 89
avg_fp_confidence: 0.34
fp_by_class:                 ← which class gets hallucinated most?
  broken_lamp: 23
  disjoint_part: 19
  ...
```

### `latency` mode (Module 21 — matches your <500ms budget)
```
per_image_avg:
  preprocess_ms: 12.4
  inference_ms:  284.7
  nms_ms:        48.1
  sahi_total_ms: 412.3       ← summed over patches
  fps: 2.4
patch_count: 48
```

### `memory` mode
```
peak_gpu_mb:  6420          # CUDA: max_memory_allocated / MPS: current_allocated
peak_cpu_mb:  2150
per_patch_mb: 134
backend: mps
```
> ⚠️ Note for opencode: MPS memory tracking uses `torch.mps.current_allocated_memory()` (PyTorch ≥ 2.0); CUDA uses `torch.cuda.max_memory_allocated()`. Wrap in a `try/except` fallback for CPU.

---

## 6. Report Output (what the intern + advisor actually read)

`report.py` writes **three artifacts** per run:
1. `reports/eval/<run_name>/report.md` — human-readable Markdown with comparison tables
2. `reports/eval/<run_name>/results.json` — machine-readable (for future CI/regression checks)
3. **MLflow** — one run per model, metrics + the config YAML as artifact (mirrors your training script)

The Markdown comparison table is the headline deliverable:

```markdown
| Model                  | mAP50(mask) | Corrosion R | Clean FPR | SAHI ms | Peak VRAM |
|------------------------|-------------|-------------|-----------|---------|-----------|
| objectness_branch      | 0.669       | 0.90        | 35.4%     | 412     | 6.4 GB    |
| seesaw_surgical_early  | 0.670       | 0.89        | 37.0%     | 409     | 6.4 GB    |
| baseline_bce           | 0.449       | 0.21        | 29.9%     | 401     | 6.3 GB    |
```

---

## 7. Micro-Task Breakdown for opencode

Because opencode has limited context, build this **one file at a time**, in dependency order. Each is one paste:

| # | Micro-task | Produces |
|---|---|---|
| 1 | Create `configs/eval/stage2_benchmark.yaml` + `clean_images.yaml` | Config schema |
| 2 | `metrics/size_bucketed.py` | Size-bucketed AP/recall |
| 3 | `metrics/classwise.py` | Per-class tables |
| 4 | `metrics/clean_fpr.py` | FPR computation |
| 5 | `perf/latency.py` | Timing instrumentation |
| 6 | `perf/memory.py` | VRAM/RAM tracking (CUDA+MPS+CPU) |
| 7 | `sahi_eval.py` | Reusable SAHI eval wrapper |
| 8 | `report.py` | Markdown + JSON + MLflow writer |
| 9 | `evaluate.py` | Thin orchestrator wiring it all |
| 10 | **Smoke test**: run `--mode full` on `dummy_dataset` | End-to-end verification |

---

## My Recommendation

Start with **Micro-task 1 (configs) → 2 (size_bucketed) → 4 (clean_fpr)**, because those encode your professor's most important lessons (#1 and the FPR production metric). The latency/memory (`perf/`) modules come after, since they're more hardware-specific and need the MPS/CUDA care.

**Would you like me to draft Micro-task 1 + 2 as ready-to-paste opencode prompts?** Or would you prefer to adjust the design first (e.g., different metric priorities, a specific model registry, or whether Stage 3 panel evaluation should share this same harness)?
