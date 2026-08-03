Here is your **Model 3 training blueprint**. The short answer to your question: **Use multi-scale. Do NOT tile.** Your images are ~979×705 — they are already the right size for 1024px training. Tiling is for 4K images; multi-scale is for teaching scale invariance.

---

## The "Perfect Model" Strategy

### Tier 1: Fix Everything That Killed Model 2

These are non-negotiable. If you skip any of these, you will repeat the 48.4% failure.

| # | Fix | Model 2 (Wrong) | Model 3 (Correct) | Why |
|:---:|:---|:---|:---|:---|
| 1 | **Training resolution** | 640px forced resize | **1024px letterbox** | Defects are no longer sub-pixel |
| 2 | **Preprocessing** | `resize(640,640)` — aspect ratio destroyed | **Keep originals, let YOLO letterbox** | Wheels stay round, masks align |
| 3 | **Mosaic** | **0.0 (DISABLED)** | **1.0** | Multi-image collage forces scale/position diversity |
| 4 | **Multi-scale** | `True` (couldn't save 640px) | **True** | ±50% jitter (512–1536px) builds scale robustness |
| 5 | **Scale aug** | 0.2 | **0.5** | Objects seen at 50%–150% of native size |
| 6 | **Degrees** | 15° | **30°** | More angular diversity for car orientations |
| 7 | **Erasing** | 0.2 | **0.4** | Forces model to use context, not local texture |
| 8 | **Validation data** | Mixed legacy + clean (5,436 images) | **Clean 2200 only, stratified split** | Metrics reflect true performance |

### The Locked Config (Model 3)

```yaml
task: segment
model: yolo26m-seg.pt          # COCO pretrained — start fresh
imgsz: 1024
batch: 8                        # RTX 3090 24GB safe limit
epochs: 150
patience: 15
freeze: 15                      # Unfreeze at epoch 16
lr0: 0.01
lrf: 0.01                      # Cosine to 0.0001
optimizer: auto

# Loss
loss_type: focal
fl_gamma: 2.0                  # Bump to 2.5 if scratch mAP >70% while corrosion <40%

# CRITICAL: Let YOLO handle letterboxing. Do NOT pre-resize your images.
# Your dataset YAML should point to the ORIGINAL images.

augmentations:
  hsv_h: 0.03
  hsv_s: 0.4
  hsv_v: 0.5
  degrees: 30.0
  scale: 0.5
  perspective: 0.0005
  fliplr: 0.5
  mosaic: 1.0                  # RE-ENABLED
  mixup: 0.0                   # Keep off — protects thin masks
  erasing: 0.4                 # RE-ENABLED
  close_mosaic: 10             # Disable last 10 epochs for stability

multi_scale: true              # Varies input 512–1536 every 10 batches
amp: true                      # RTX 3090 CUDA — safe to use
device: 0
workers: 8
```

---

## Multi-Scale vs. Tiling: Choose One or Both?

**Choose multi-scale only. Do not tile.**

| | Multi-Scale Training | Training-Time Tiling |
|:---|:---|:---|
| **What it does** | YOLO randomly resizes input ±50% each batch | You slice large images into overlapping patches offline |
| **Your images (~979×705)** | Perfect fit. Images are already near 1024px. | Useless. You'd get 1 patch per image = no benefit. |
| **Defect size effect** | Teaches model to find defects at different scales | Only needed if defects are tiny relative to 4K+ images |
| **Risk** | None | High — split leakage, boundary artifacts, overfitting to repeated context |
| **Verdict** | ✅ **Use this** | ❌ **Skip for Model 3** |

**Why tiling is wrong for you:** Your previous "tiling" script produced exactly 1 patch per parent (memory #28). Real tiling from ~1MP images would still yield ~1 patch per image at 1024px. It adds zero value and introduces seam artifacts. Multi-scale training achieves the same goal (scale diversity) safely and automatically.

**Exception:** If you later acquire **4000×3000 factory images** (from your Phase 3 SAHI experiments), THEN you tile at training time. But your 2200 CVAT images are standard resolution — just train them native at 1024px.

---

## Tier 2: Push From "Good" to "Perfect" (62% → 75%+)

### A. Use Your 200 New Images Strategically
Your class distribution is severely imbalanced. If your 200 new images target weak/rare classes, you get disproportionate return:

| Class | Old Count | Target for 200 new | Priority |
|:---|:---:|:---:|:---:|
| scratch | 47% | Keep flat | Low — already saturated |
| dent | 17% | Keep flat | Low |
| **corrosion** | 4% | **+50 images** | 🔴 Critical |
| **crack** | 9% | **+50 images** | 🔴 Critical |
| **deform** | 5% | **+40 images** | 🟡 High |
| **disjoint_part** | 7% | **+40 images** | 🟡 High |
| broken_lamp | 10% | +20 images | Medium |
| glass_shatter | 4% | +20 images | Medium |

**Goal:** Get corrosion and crack each to ~300+ instances. This fixes the "model never learned what corrosion looks like" problem.

### B. Clean Negatives Check
Model 2 had only 9% clean negatives. With 2200 images, ensure you have **≥10% clean negatives** (220 images). If not, add more no-defect car panels. This prevents hallucination.

### C. Focal Loss Gamma Tuning
Start with `fl_gamma: 2.0`. After epoch 50, check per-class mAP50:
- If **scratch >70%** and **corrosion <40%** → increase to **2.5**
- If **dent/scratch confusion >15%** → your bimodality hypothesis is confirmed; consider splitting scratch post-training

### D. Pretraining Strategy (Optional)
With 2200 images, you have enough to train from COCO directly. **Do NOT pretrain on the dirty 33k** — the 7→8 class mismatch and conflicting labels will poison your backbone. COCO weights already know edges, textures, and object boundaries. Let the clean data teach defect specifics.

---

## Tier 3: Advanced Marginal Gains

Only if you have time after Tier 1 & 2:

1. **Copy-Paste Augmentation for Rare Classes**
   - Offline script: copy corrosion/crack instances onto clean panel backgrounds
   - 2–3× your rare class counts without new annotation
   - Use your 400 clean negative images as paste targets

2. **Exponential Moving Average (EMA)**
   - YOLO enables this by default. Verify `ema: true` in your training. It smooths weights and often adds +1–2% mAP.

3. **Hyperparameter Evolution**
   - If Model 3 hits 65% but stalls, run Ultralytics `tune` for 100 iterations on learning rate and augmentation mix. Not worth it until you have a solid baseline.

---

## Validation Protocol (Critical)

Your Model 2 metrics were contaminated by legacy eval data. For Model 3:

```bash
# 1. Stratified split BEFORE training
train: 1760 images (80%)
val:   220 images (10%)   # MUST be clean-annotated
test:  220 images (10%)   # Held out, touch only at final report

# 2. Verify zero legacy leakage
grep -r "missing_component" labels/   # Must return nothing
grep -r "broken_component" labels/      # Must return nothing (now broken_lamp)

# 3. Evaluate with LOCKED inference config
conf: 0.15
iou: 0.50
imgsz: 1024
device: mps  # or cuda if testing on RTX
```

**Do not evaluate Model 3 on the old 5,436 mixed dataset.** That set exists only for failure-mode analysis. Your production metrics come from the clean 220 test images.

---

## Expected Timeline & Milestones

| Epoch | What to Watch | Abort If |
|:---:|:---|:---|
| 1–15 | Frozen backbone; box loss should drop steadily | Loss NaN → check AMP |
| 16 | LR cliff 10×; val mAP should NOT drop >20% | Catastrophic forgetting → restart |
| 17–50 | Unfrozen backbone; all classes should rise | One class collapses to 0% → label error |
| 51–100 | Plateau hunting; watch val seg loss | Val seg loss rises >10% from min → overfitting |
| 101–150 | Fine convergence; patience=15 will catch peak | — |

**Projected outcome:** 62–72% Box mAP50 on clean test set, with glass_shatter/broken_lamp >90%, scratch/crack/dent >60%, corrosion >45%.

---

## Bottom Line

**To make Model 3 perfect:**
1. **Train at 1024px** with letterboxing (not resize)
2. **Enable mosaic + multi-scale + full augmentations** (the Model 2 config was anemic)
3. **Do not tile** — your images are already the right size
4. **Evaluate only on clean data** — legacy labels lie about your true performance
5. **Use the 200 new images to feed rare classes** (corrosion, crack, deform)

The model architecture is fine. The data is fine. The labels are now fine. Just give the model enough resolution to see what you annotated.
