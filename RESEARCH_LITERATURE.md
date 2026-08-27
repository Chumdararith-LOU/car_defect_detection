# Research Literature — Stage 2 Upgrade Candidates

Every entry below is picked because it targets a *specific, named* problem
from the Week 7 report or STAGE2_RETRAIN_BRIEF.md — this is not a general
"small object detection" reading list. Each entry has a complexity tag so
the plan agent can sequence cheap wins before expensive rewrites:

- `[config]` — a flag/parameter change in the existing training setup.
- `[recipe]` — changes how training is run (data mix, schedule, sampling),
  no source patching.
- `[loss/assignment]` — requires patching the label-assignment or loss code
  inside Ultralytics' source (not exposed as a config flag).
- `[architecture]` — requires adding/modifying model layers in Ultralytics'
  source (new head, new fusion path).
- `[new pipeline]` — a second model or process alongside Stage 2, not a
  patch to it.

---

## A. Tiny-object localization (attacks the corrosion/disjoint_part root cause directly)

The raw-logit audit in Week 7 found tiny corrosion instances (8-27px) with
near-zero global-inference probability. That's a resolution problem SAHI
already treats at inference — but IoU-based training itself is *also*
known to break down at this scale, independent of resolution. This section
is the highest-leverage cluster for that specific failure.

- **A Comprehensive Literature Review on YOLO-Based Small Object Detection**
  (ScienceDirect, 2026) — https://www.sciencedirect.com/org/science/article/pii/S1546221826001943
  A recent survey organizing the entire small-object-YOLO literature into
  four families: attention/feature enhancement, detection-head redesign,
  loss/assignment engineering, and adaptive fusion. **Read this first** —
  it's the map for everything else in this section. `[reference]`

- **A Normalized Gaussian Wasserstein Distance for Tiny Object Detection**
  (Wang, Xu, Yang & Yu, 2021) — https://arxiv.org/abs/2110.13389, follow-up
  benchmark: https://arxiv.org/abs/2206.13996 (AI-TOD-v2)
  Models each box as a 2D Gaussian and replaces IoU with Wasserstein
  distance (NWD) in label assignment, NMS, *and* the regression loss. The
  core finding: IoU is extremely sensitive to small pixel-level location
  shifts precisely when the object is tiny, which can starve tiny-object
  training signal even when the object is visible in the image — a
  training-time analog of the resize-destroys-signal problem you already
  diagnosed at inference time. Directly relevant to corrosion (8-27px).
  `[loss/assignment]` — official code exists but targets mmdetection/Faster
  R-CNN; porting the NWD formula into Ultralytics' TaskAlignedAssigner and
  bbox loss is a real patch, not a flag.

- **RFLA: Gaussian Receptive Field based Label Assignment for Tiny Object
  Detection** (Xu et al., ECCV 2022) — companion method to NWD from the
  same group, assigns labels using receptive-field-aware Gaussian overlap
  instead of IoU thresholds. Same complexity tag and same target problem;
  worth reading alongside NWD rather than instead of it.

- **P2 high-resolution detection head** — this is a recurring, well-proven
  community modification, not one paper: add a 4th detection head tapping
  the backbone's stride-4 feature map (before it's been downsampled to
  stride-8/P3), so an 8px object still occupies multiple feature cells
  instead of collapsing to sub-pixel. Representative implementations:
  SOD-YOLO (https://www.nature.com/articles/s41598-024-77513-4),
  YOLOv8-Ghost-P2-PIoU2, and a concrete Ultralytics-specific walkthrough on
  the Ultralytics community forum ("Adding a new head to the YOLO11n model
  to detect very small objects" —
  https://community.ultralytics.com/t/adding-a-new-head-to-the-yolo11n-model-to-detect-very-small-objects/876).
  Reported cost: one paper measured ~11% more FLOPs for the added P2 branch
  — worth weighing against your existing 594ms SAHI latency budget.
  `[architecture]` — requires editing the YOLO26-seg yaml/model definition
  and neck fusion code, most direct source-level change on this list.

---

## B. Transfer-learning strategy refinement (extends what Model 5 already proved)

Week 7 found frozen-backbone + extended head warmup (65.0%) beats
differential full fine-tuning (63.3%). These two papers explain *why*, by
name, and point at an untried middle ground.

- **Fine-Tuning can Distort Pretrained Features and Underperform
  Out-of-Distribution** (Kumar, Raghunathan, Jones, Ma & Liang, ICLR 2022)
  — https://arxiv.org/abs/2202.10054
  Shows theoretically and empirically that full fine-tuning can distort a
  good pretrained feature extractor and hurt out-of-distribution accuracy,
  because the head and backbone update simultaneously and the backbone
  compensates for a still-randomly-adapting head. Their fix, **LP-FT**
  (linear-probe the head first, *then* unfreeze for full fine-tuning) beat
  both plain fine-tuning and plain linear probing. This is a formal name
  for close to what you already did (head warmup, then differential FT) —
  the paper suggests the remaining gap might be in *how* the second phase
  is run (a much smaller, decaying LR on top of the LP solution) rather
  than whether to run it at all. `[recipe]`

- **Surgical Fine-Tuning Improves Adaptation to Distribution Shifts** (Lee
  et al., ICLR 2023) — https://arxiv.org/abs/2210.11466
  Directly tests partial/selective layer unfreezing against both full
  fine-tuning and full freezing across seven real distribution-shift
  tasks, and finds a selectively-unfrozen *contiguous subset* of layers
  consistently matches or beats both extremes — which subset is best
  depends on the type of shift. This is the literature backing for
  STAGE2_RETRAIN_BRIEF.md item 3 (gradual/partial unfreeze), which was
  flagged there as "approved but not yet tried." `[recipe]` — implementable
  today via existing `freeze:` parameter swept across different values,
  no source patch required.

---

## C. Rare-class data scarcity (corrosion, disjoint_part)

Two different strategies: augment what little real data exists, or
generate more data synthetically. Worth trying in that order.

- **Simple Copy-Paste is a Strong Data Augmentation Method for Instance
  Segmentation** (Ghiasi et al., CVPR 2021) — https://arxiv.org/abs/2012.07177
  Finds that randomly pasting segmented object instances onto other
  training images — no context-matching needed — produces solid gains for
  data-scarce and rare categories in instance segmentation. This is the
  most direct, cheapest fix for corrosion/disjoint_part: paste existing
  corrosion masks from your labeled set onto clean-car crops (once you have
  the hard-negative pool from STAGE2_RETRAIN_BRIEF.md §3) to multiply rare
  examples without new annotation. `[recipe]` — a data pipeline addition,
  no Ultralytics source changes needed if using the offline-augmentation
  route (as opposed to Ultralytics' built-in online copy-paste augmenter,
  which is simpler to enable but less controllable).

- **CrashCar101: Procedural Generation for Damage Assessment** (Parslov,
  Riise & Papadopoulos, WACV 2024) — https://arxiv.org/abs/2311.06536,
  dataset: 101,050 synthetic images with pixel-accurate part+damage masks,
  generated by procedurally damaging 3D car models and rendering.
  Demonstrated sim2real transfer for damage segmentation, and that mixing
  real + synthetic data beat real-only training for part segmentation.
  This is the most ambitious option on this list: instead of waiting for
  more real corrosion images through the "data flywheel" mentioned in your
  report's blockers section, procedurally *generate* arbitrarily many
  corrosion/disjoint_part examples with perfect masks. Check whether their
  damage taxonomy includes corrosion specifically before committing —
  their public categories may be dent/scratch/crack-focused. `[new
  pipeline]` — either use their released dataset directly (data-level, no
  code change) or adapt their generation pipeline for your own damage
  types (a real engineering project).

---

## D. Class-imbalance loss functions (a training-time complement to C)

Focal loss (already in use) addresses *easy-vs-hard* example imbalance.
These address *category frequency* imbalance specifically, which is a
different axis — worth stacking, not substituting.

- **Seesaw Loss for Long-Tailed Instance Segmentation** (Wang et al., CVPR
  2021) — https://arxiv.org/abs/2008.10032
  Dynamically rebalances the gradient a rare class receives from
  negative/background samples (which otherwise dominate and suppress rare
  classes), while adding a compensation term specifically so this doesn't
  cause more false positives on the rare classes — notable given your new
  clean-image false-positive requirement pulls in the opposite direction
  from naive rebalancing. `[loss/assignment]` — patches the classification
  loss in Ultralytics' segmentation head.

- **Equalization Loss / EQLv2** (Tan et al.) — the predecessor/sibling
  approach: 1st place in the 2019 LVIS long-tail challenge by simply
  zeroing out the gradient contribution of rare-class negatives past a
  frequency threshold. Simpler to implement than Seesaw Loss if you want a
  cheaper first attempt at this idea before committing to the full Seesaw
  formulation. `[loss/assignment]`

---

## E. Mask-level NMS / SAHI postprocessing (validates and extends your Mask-IOS work)

- **Slicing Aided Hyper Inference and Fine-tuning for Small Object
  Detection** (Akyon, Altinuc & Temizel, ICIP 2022) —
  https://arxiv.org/abs/2202.06934 — the original SAHI paper you're already
  using. Worth re-reading one detail: the paper's own pipeline includes a
  **fine-tuning-on-slices** stage, not just sliced inference — direct prior-art
  support for STAGE2_RETRAIN_BRIEF.md item 4 (train on tiles, not just
  infer on them). The SAHI library's postprocessing options (Greedy NMM,
  LSNMS) are also worth comparing against your custom Mask-IOS merge as a
  sanity baseline before assuming a custom implementation is required.
  `[recipe]` for the slice-training part — largely a data pipeline change.

- **SOLOv2: Dynamic and Fast Instance Segmentation** (Wang et al., NeurIPS
  2020) — https://arxiv.org/abs/2003.10152
  Introduces **Matrix NMS**, a mask-level NMS that runs as a single
  parallel matrix operation instead of the sequential greedy loop standard
  NMS uses — addresses exactly the latency cost of mask-level merging
  (their paper notes mask IoU computation is the expensive part of mask
  NMS, which is presumably part of why your SAHI pass costs 594ms vs 213ms
  direct). If Mask-IOS merging is a latency bottleneck at production scale,
  Matrix NMS's parallelized formulation is worth adapting even though your
  chosen merge *metric* (IOS) already differs from theirs (mask IoU).
  `[architecture]` if reimplemented for speed; `[recipe]` if you just want
  the *concept* (mask-level, not bbox-level) validated against your own
  approach with no speed changes.

- Multiple independent papers outside your domain (industrial table-cell
  segmentation, scene-text detection) converge on the same idea you built
  independently: mask-level IoU/overlap for NMS beats bounding-box IoU
  when instances are thin or irregular. This is worth citing in your final
  report as "consistent with published practice," not just an ad hoc fix.

---

## F. Clean-car false-positive suppression as anomaly detection (a second model, not just more negatives)

STAGE2_RETRAIN_BRIEF.md §2.1 treats hard-negative injection as a data
addition to the *segmentation* model. There's a materially different, more
powerful option: a dedicated **anomaly-detection gate** trained *only* on
your new clean-car dataset, that flags "this doesn't look like a normal
car surface" independent of the 7-class segmentation model's own
confidence. This directly targets the requirement that Stage 2 must not
hallucinate on clean cars, using an entirely different failure mode than
"insufficient negative training data."

- **PatchCore: Towards Total Recall in Industrial Anomaly Detection** (Roth
  et al., CVPR 2022) — patch-level feature memory bank built *only* from
  normal/clean images, no defect labels needed at all. Reports up to 99%+
  image-level AUROC on the MVTec AD industrial benchmark, and needs
  comparatively few training images (one comparative study cites strong
  results from ~294 normal images) — realistic given your clean-car pool
  size. `[new pipeline]`
- **PaDiM: Patch Distribution Modeling Framework for Anomaly Detection**
  (Defard et al., 2021) — a lighter-weight alternative to PatchCore, models
  per-patch feature distributions with a pretrained CNN + Gaussian model
  instead of a memory bank. Cheaper to run, slightly behind PatchCore on
  benchmarks. Good first thing to try given lower implementation cost.
  `[new pipeline]`
- **CutPaste: Self-Supervised Learning for Anomaly Detection and
  Localization** (Li et al., CVPR 2021) — synthesizes fake local "defects"
  by cutting a patch from a clean image and pasting it elsewhere on the
  same image, then trains a classifier to spot the seam — a way to bootstrap
  an anomaly detector without needing any real defect images, useful if the
  clean-car pool ends up much bigger than the labeled-defect pool. `[new
  pipeline]`

Recommended framing for the plan: treat F as a stretch goal that runs
*alongside* Stage 2's own segmentation confidence (e.g., only trust a
segmentation-model detection if the anomaly gate also flags the image),
rather than a replacement for hard-negative training in §2.1 — the two
target overlapping but not identical failure modes.

---

## G. Whole-architecture alternatives and CarDD-specific state of the art

Since part of your training data *is* CarDD, work published directly
against the CarDD benchmark is the most externally-validated comparison
point available.

- **CarDD: A New Dataset for Vision-based Car Damage Detection** (Wang et
  al., IEEE T-ITS 2023) — the dataset's own paper. Their best model, DCN+,
  reached 57.0 mask AP on CarDD's own split (Mask R-CNN: 49.4, plain DCN:
  52.5) — useful as an external sanity check on what's achievable on
  CarDD-family data before your other datasets and taxonomy changes are
  mixed in. Also explicitly flags that Salient Object Detection methods
  (i.e., what your own Stage 1 already does) showed particular strength on
  irregular damage shapes, and suggests combining SOD-style and
  category-aware segmentation — which is architecturally close to your
  3-stage pipeline design already.
- **C-DiffDet+: Fusing Global Scene Context with Generative Denoising for
  High-Fidelity Car Damage Detection** (2025) —
  https://arxiv.org/abs/2509.00578 — current published state of the art on
  CarDD detection (64.8 box AP), built on a diffusion-based detector
  (DiffusionDet) with an added global-scene-context fusion module. This is
  the most complex item on this whole list — diffusion-based detection is
  architecturally unrelated to YOLO — but it's flagged here because you
  explicitly said complexity isn't a constraint, and it represents a real
  ceiling estimate for what CarDD-family data supports. `[new pipeline]`,
  large undertaking, would essentially mean running a second, unrelated
  architecture as a comparison point rather than modifying YOLO26-seg.

---

## Suggested reading/trial order

Given the "as complex as needed" mandate, here's a rough value-for-effort
ordering — not a mandate, the plan agent should re-rank against actual
repo/compute constraints:

1. **Surgical fine-tuning sweep (B)** — free, uses the `freeze:` parameter
   you already have, directly extends the Week 7 finding.
2. **Copy-paste augmentation for corrosion/disjoint_part (C)** — cheap,
   data-only, no source patch.
3. **Hard-negative injection + PaDiM anomaly gate (F)** — uses the new
   clean-car data two different ways; PaDiM is the cheaper anomaly-model
   option to prototype first.
4. **NWD loss/assignment (A)** — the most evidence-backed fix specifically
   for tiny corrosion instances, but requires patching Ultralytics'
   assigner/loss — budget real engineering time.
5. **P2 detection head (A)** — architecture surgery, budget real
   engineering time and re-check the SAHI latency budget afterward.
6. **Seesaw/Equalization loss (D)** — stack on top of whichever of the
   above is already in place, since it's a loss-level change independent
   of them.
7. **C-DiffDet+ / diffusion detector comparison (G)** — treat as a research
   spike / ceiling estimate, not a production commitment, given the
   architecture distance from your current YOLO26-seg pipeline.
