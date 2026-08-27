# AGENTS.md — Automated Car Defect Detection Pipeline

This file is auto-loaded into context by opencode on every session in this repo.
Do not repeat the content below in chat prompts — it is already known.

## Project scope for this workstream

We are retraining **Stage 2 only** (the multi-class instance segmentation core
engine). Stage 1 (binary SOD pre-screener) and Stage 3 (panel/component
segmentation) are explicitly out of scope — do not touch their code, configs,
or weights unless asked.

Definition of done for "best possible Stage 2 model" this round:
1. Beats the current champion (Model 5: 65.0% test Mask mAP50, 49.4% mAP50-95,
   66.6% precision, 63.5% recall) on the held-out 7-class test split, **or**
   the plan documents why a candidate that doesn't beat it on mAP is still the
   right pick (e.g. materially better recall on corrosion/disjoint_part or a
   materially lower clean-image false-positive rate).
2. Reports a **clean-image false-positive rate** — this metric does not exist
   yet in prior reports and must be added (see Evaluation Protocol below).
3. Reports per-class and size-bucketed (tiny / small / medium) Mask mAP, not
   just the aggregate number — aggregate mAP hid the corrosion/disjoint_part
   failure last round.

## Locked decisions — do not relitigate without new evidence

These were established through real experiments in Week 5-7 and cost real
compute to learn. Re-testing a rejected approach is fine if the brief calls
for it explicitly; silently drifting back to it is not.

- **Training and SAHI inference resolution must match, and both must be
  native/high-resolution (1024×1024 tiles).** 640px training destroyed thin
  defects (Model 2: 46.3% mAP50 vs Model 1's 50.1% at 1024px, despite cleaner
  labels). Never propose downsampling below the model's proven working
  resolution to save training time — flag the tradeoff instead and ask.
- **Default transfer strategy is frozen-backbone + extended head-only warmup**,
  resuming from the Model 1 backbone. Full/differential fine-tuning
  (freeze:0, backbone_lr_mult:0.1) underperformed this on our ~2,200-image
  dataset (63.3% vs 65.0% test mAP50) — the backbone is already well-adapted
  and the dataset is too small to safely update it further. A **gradual/
  partial unfreeze** (unfreezing only the last N backbone blocks, or
  unfreezing progressively over epochs) has NOT been tried yet and is an
  approved experiment this round — full simultaneous unfreeze of all layers
  is not.
- **Mask-level NMS (Mask-IOS: intersection over the smaller mask's area), not
  bounding-box NMS**, for merging overlapping SAHI patch predictions.
  Bbox NMS damages thin scratch/crack masks. This is a locked postprocessing
  requirement, not a training-time concern, but any retrained model must
  still be validated against it before being called production-ready.
- **7-class unified taxonomy is final**: `dent` (merged with the old
  `deform`), `scratch`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion`,
  `disjoint_part`. Do not reintroduce a `deform` class. Any new source
  dataset must be mapped onto exactly these 7 labels before it enters
  training — see the data-source manifest in STAGE2_RETRAIN_BRIEF.md.
- **corrosion and disjoint_part are the known weak classes.** Diagnostic
  work (raw-logit audit) showed the signal exists but is destroyed by global
  resizing on tiny instances (5 corrosion instances at 8-27px were recovered
  at native resolution: P≈0.04 globally vs P>0.25 in a native crop). This is
  a training-data/training-recipe problem to close this round, not just an
  inference-time SAHI problem — SAHI already covers the inference side.

## Data source manifest

Full raw-dataset audit lives in `data/raw/DATASET_AUDIT.md` (paste the
existing audit there if it isn't in the repo yet — ask the user rather than
re-deriving it from scratch). Known facts from that audit an agent must
respect:

- `Roboflow/car-damage-detection.v1i.coco` is a **duplicate** of
  `CarDD_release/CarDD_COCO/train2017` — never include both.
- `Car defect 2000 new/` and `Car defect 2200/` are near-duplicate exports of
  the same 10-class dataset — dedupe at the image-hash level before using
  both; do not simply concatenate.
- `archive/Car damages dataset` = **21 car PANEL classes** (Stage 3 material,
  not Stage 2).
- `archive/Car parts dataset` = **8 DAMAGE type classes** despite its name —
  this one is Stage 2 material. Don't mix these two up when writing loaders.
- Several Roboflow exports have unusable raw category names (`0`, `1`,
  `object`, hash-suffixed labels like `car-G2ce`) — resolve via each export's
  `README.dataset.txt` before mapping to the 7-class schema, never guess.

## New this round: clean/undamaged hard-negative data

We have **zero clean-car images** in the training set today. The model has
never been shown a defect-free car and has no way to learn what "no defect"
looks like — this is a likely source of false positives on clean vehicles.
Candidate sources are listed in STAGE2_RETRAIN_BRIEF.md §3. Treat the
negative:positive image ratio as a swept hyperparameter (start ~10-15% of
the training set as pure-negative images with empty label files), not a
fixed constant — report how the clean-image false-positive rate moves as
this ratio changes.

## Conventions

- Report metrics in the same table format as `Report_Week_7.docx`: Mask
  mAP50 / mAP50-95 / Precision / Recall, with Val and Test columns and the
  run config (resolution, freeze layer, epochs, lr0, loss) alongside.
- Every training run gets a short run-log entry (config changed, metric
  deltas, one-line verdict) — this is what previous weekly reports were
  built from; keep producing it in the same shape so it drops straight into
  next week's report.
- Before running anything expensive (a full training run), stop and confirm
  the config with the user if it deviates from the locked decisions above.
