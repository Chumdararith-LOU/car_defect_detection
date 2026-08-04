# Model 5 (Revised): Resume-and-Adapt, Not Pretrain-from-Scratch

## What changed vs. the original proposal

Original plan: COCO weights → pretrain on Dirty 33k (Phase A, 50 epochs) → fine-tune on
CVAT clean 2,200 (Phase B, 100 epochs).

Revised plan: **Model 1's epoch-101 checkpoint** (8,000 professor-curated images, 51.6%
box mAP50 — your best result so far) → remap head 7→8 classes → fine-tune on CVAT clean
2,200 in two stages, with differential learning rates and a `close_mosaic` schedule.

The Dirty 33k pretraining step is dropped from the critical path. It was diagnosed as
harmful standalone (43.9%, worse than Model 1) because of conflicting class definitions,
bad bbox→polygon conversions, and duplicates. Re-exposing a from-scratch backbone to that
same noisy signal in Phase A just reintroduces the problem before clean data ever gets a
chance to fix it. Model 1's checkpoint already did the job Phase A was meant to do — teach
a backbone what car damage looks like — using better data.

This is not a guaranteed win. It's the best-supported hypothesis given what your five
prior runs actually show, not a certainty. Treat the projections below as ranges to test,
not commitments.

---

## Stage 0 (optional, secondary — do not run first)

If you still want the volume/diversity of the 33k set, don't feed it in raw — that
already failed once. Filter it first: dedupe, drop bbox-derived polygons, resolve
conflicting class taxonomies against the CVAT 8-class schema. Then run a short,
low-LR continued-pretrain starting from **Model 1's weights** (not COCO), so noisy
signal can only nudge the backbone, not overwrite it.

Only worth doing if the Stage 1+2 resume baseline (below) undershoots your target and
you suspect it's data-volume-limited rather than mosaic/context-limited. Run the
baseline first — this adds a full extra experiment's worth of compute and confound risk.

---

## Stage 1 — Head remap + head-only warmup

**Goal:** adapt the 7-class head to 8 classes without disturbing the backbone/neck
features Model 1 already learned.

- Load Model 1's **epoch-101 checkpoint** (its documented peak — not the epoch-200
  final weights, which the original report notes had already started overfitting).
- Rebuild the model at `nc=8`, load Model 1's weights with `strict=False` so every
  layer except the shape-mismatched head transfers; the head gets a fresh init.
- Freeze backbone+neck (`freeze: 15`, same convention as your prior runs).
- Train ~15 epochs on CVAT clean 2,200 at 1024px, `mosaic: 1.0, scale: 0.5, degrees: 30`
  (matches Model 3's aug recipe, which — per the Model 3 vs. 4 comparison — net-helped
  over no-mosaic at this dataset size).
- No early stopping here; this is a short fixed warmup, not the main optimization.

See `stage1_head_warmup.py`.

---

## Stage 2 — Full fine-tune, differential LR, mosaic close-out

**Goal:** let the whole network adapt to the clean 8-class taxonomy, but protect the
backbone's damage-texture priors from being overwritten by only 2,200 images, and give
the head a final stretch of training on real (non-mosaicked) panel context so it isn't
evaluated on a distribution it never saw plain.

- Resume from Stage 1's best checkpoint. Unfreeze everything (`freeze: 0`) — a hard
  freeze/unfreeze cliff is replaced by a **10x LR multiplier gap**: backbone/neck at
  `0.1x` the head's learning rate, via custom optimizer param groups (ultralytics
  doesn't expose this natively, so it's implemented as a small trainer subclass).
- `mosaic: 1.0` for the bulk of training, then `close_mosaic: 25` — mosaic turns off
  for the final 25 epochs so the head's last training signal matches real, single-image
  panel context, not stitched crops.
- `patience: 20`, up to 120 epochs, best checkpoint by clean-val mAP kept.

See `stage2_differential_finetune.py`.

**Layer-split caveat:** the backbone/head split point (`SPLIT_LAYER_IDX = 15`) reuses
your existing `freeze: 15` convention. Confirm this index is actually the neck→head
boundary in your specific YOLO26m-seg architecture before running — if it's off, the
differential LR will split at the wrong point and the effect will be muted or backwards.

---

## Checkpoint selection & evaluation protocol

- Track clean-val mAP **every epoch in both stages**, not just at the end — if Stage 2
  starts drifting backbone features away from Model 1's priors, catch it early rather
  than always using the final checkpoint.
- Evaluate **only** on the clean 220-image held-out split. Legacy/dirty data is for
  failure analysis (which classes break, what kinds of images), never for reported mAP.
- Keep a per-class instance-count table alongside every result — corrosion at ~64 train
  instances needs to be read differently than classes with hundreds.

## Variance control

Your test split (220 images, 8 classes, some classes in the tens of instances) is small
enough that a 3–5 point mAP gap between configs may not be distinguishable from run
noise. Before treating any single number as the deciding result:
- Run 2–3 seeds of the Stage 2 fine-tune, or
- k-fold across the 2,200 clean images (fold the 220-image test portion too),
and report a range, not a point estimate. This matters most for the rarest classes.

## Risks to verify before launching

1. **Head remap correctness** — confirm the `strict=False` load actually skips only the
   head layers and not something else (log `missing`/`unexpected` keys and eyeball them).
2. **Layer split index** — see caveat above; wrong index silently breaks the differential
   LR's intent.
3. **Stage 1→2 handoff** — Stage 2 should resume from Stage 1's *best*, not *last*,
   checkpoint if Stage 1 overfits before epoch 15.
4. **API surface** — the scripts below are written against standard Ultralytics YOLO
   conventions (`YOLO()`, `SegmentationTrainer`, `close_mosaic`, `freeze`). If your
   YOLO26m-seg build is a fork or has renamed these, the exact calls will need
   adjusting — the structure (surgery → freeze warmup → differential-LR unfreeze with
   mosaic close-out) is the part that should transfer regardless.
