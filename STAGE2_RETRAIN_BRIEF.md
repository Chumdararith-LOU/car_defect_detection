# Stage 2 Retrain Brief — "best possible" round

Read this alongside AGENTS.md (which holds the non-negotiable constraints).
This file is input to the **plan agent** — it should turn this into a
concrete, file-level PLAN.md, not start implementing yet.

## 1. Goal

Produce the best achievable Stage 2 (multi-class instance segmentation)
model, where "best" means: beats or thoughtfully trades off against Model 5
(65.0% test Mask mAP50) on the locked 7-class held-out test set, closes the
corrosion/disjoint_part gap, and — new this round — does not hallucinate
defects on clean, undamaged cars.

Out of scope: Stage 1 (SOD pre-screener) and Stage 3 (panel mapping). Do not
touch them.

## 2. What to try, in priority order

Each of these is a candidate improvement over the Model 5 recipe. Cost and
expected value are rough guides for sequencing, not commitments — the plan
agent should size them against the actual repo/compute before ordering.
**RESEARCH_LITERATURE.md has the published papers backing each item below**
— read it alongside this brief; items are cross-referenced by section
letter (A-G).

1. **Hard-negative injection (highest priority, addresses a real gap).**
   Add clean/undamaged car images with empty annotation files to the
   training set at a swept ratio (start 10-15% of total images). See §3 for
   sources. This is the only way the model can learn a "no defect" prior —
   right now it has literally never seen one.
2. **Class-balanced sampling for corrosion / disjoint_part** (literature:
   §D Seesaw/Equalization Loss). These remain near-zero despite the
   taxonomy fix and SAHI. Oversample images containing these classes
   during training (not just at eval), or use a weighted sampler keyed on
   instance count per class — or go further and patch the loss itself per
   §D if simple oversampling plateaus.
3. **Gradual/partial backbone unfreeze** (literature: §B Surgical
   Fine-Tuning, LP-FT — approved experiment, not yet tried). Week 7 only
   tested two extremes: fully frozen (freeze:23, winner) vs. fully
   unfrozen with differential LR (freeze:0, worse). Try unfreezing only
   the last 1-2 backbone stages, or unfreezing progressively after the
   head has converged (e.g. head-only for N epochs, then unfreeze last
   stage for a further M epochs at a low LR). Compare against the frozen
   baseline on the same metrics.
4. **Train on native-resolution tiles directly, not just full 1024px
   frames** (literature: §E, the original SAHI paper's own fine-tuning
   stage). Inference already uses SAHI slicing; training currently does
   not. Feeding the model SAHI-style 1024px crops (with defect-containing
   crops oversampled) during training may improve tiny-defect learning
   directly rather than relying on inference-time tiling to compensate for a
   training/inference resolution mismatch in what the network has actually
   learned to attend to.
5. **Copy-paste augmentation for corrosion** (literature: §C Simple
   Copy-Paste, CrashCar101). Paste segmented corrosion instances from
   source images onto clean-car crops to synthetically multiply rare-class
   examples, or evaluate CrashCar101's synthetic dataset directly. No
   longer optional-only — CrashCar101 in particular is a real candidate
   for permanently closing the rare-class data gap rather than working
   around it every round.
6. **Tiny-object loss/assignment surgery** (literature: §A NWD, RFLA).
   IoU-based label assignment and loss are known to destabilize on objects
   in the corrosion size range independent of resolution — this is a
   training-time analog of the resize problem already solved at inference.
   Requires patching Ultralytics' assigner/loss code directly. Higher
   engineering cost; sequence after 1-5 since it's the most invasive
   change on this list short of item 8.
7. **Clean-image anomaly-detection gate** (literature: §F PatchCore,
   PaDiM, CutPaste). Instead of only adding hard negatives to Stage 2's
   own training set, train a second, lightweight model purely on clean-car
   images to flag "doesn't look like a normal car surface" as an
   independent signal. Complements item 1 rather than replacing it — the
   two catch different failure modes.
8. **Optional/stretch: P2 detection head or larger backbone.** A P2 head
   (literature: §A) adds a 4th detection scale tapping earlier, higher-
   resolution backbone features — real architecture surgery, budget
   accordingly, and re-check the SAHI latency budget afterward (current
   594ms/image on the target M5 hardware). Only worth it if 1-7 plateau
   below target.

## 3. Clean/undamaged car data sources to evaluate

None of these have been vetted for this project's license/domain fit yet —
that vetting is part of the plan, not assumed done.

| Source | What it is | Notes / caveats |
|---|---|---|
| CarDD's own "500 undamaged" hard-negative set | The CarDD authors built exactly this — 500 undamaged images used to stress-test false positives, same Flickr/Shutterstock domain and resolution as `CarDD_COCO`, which is already in our training mix. **Best domain match.** | Not confirmed downloadable as a standalone bundle — check `https://cardd-ustc.github.io/` / the CarDD GitHub for a challenge-set release. Requires agreeing to Flickr/Shutterstock license terms, non-commercial use — flag for the user since this is headed toward a factory/production deployment. |
| Kaggle: "Car damage detection" (`anujms/car-damage-detection`) | Binary damaged-vs-whole dataset; the "whole" class is a ready-made clean-car set with decent diversity. | Free, no special license friction noted. Good primary volume source. |
| Kaggle: "Undamaged Vehicle Image Dataset" (`garystafford/undamaged-vehicle-image-dataset`) | Undamaged images of a single late-model BMW 3-series. | Very low diversity — single make/model. Use only as a supplement, not the bulk of negatives, or the model may learn "clean = this one car" instead of "clean = no defect texture." |
| Stanford Cars-196 / CompCars / VMMRdb | Large-scale (16k-150k+ images), high-resolution, multi-angle car photos from dealer listings, auctions, and web crawls. Not labeled for damage, but the overwhelming majority are undamaged (they're marketing/catalog photos). | Best source for volume and viewpoint/lighting diversity. Needs a cheap filter pass (spot-check a sample, or run the current Stage 1 SOD model over it and drop anything it flags) to catch the rare damaged photo that slipped in. Check each dataset's own license before redistribution/production use — academic datasets often restrict commercial use. |

Recommended approach: use CarDD's undamaged set if obtainable (domain match)
+ the anujms whole-car set as the primary negative pool, and pull a filtered
slice of Stanford Cars/CompCars for volume and viewpoint diversity once the
ratio-sweep in §2.1 shows how many negatives are actually useful. Don't
bulk-ingest all of them by default — that's wasted compute and an
unnecessarily large license surface for a first pass.

## 4. Evaluation protocol (new requirements this round)

The existing held-out 202-image 7-class test split stays as-is for the
positive-class Mask mAP50/mAP50-95/precision/recall numbers. Add:

- **Clean-image false-positive rate**: run the model over a held-out slice
  of the clean-car set (not used in training) and report % of images with
  ≥1 predicted defect above the production confidence threshold, plus a
  breakdown by which class is most often hallucinated.
- **Per-class Mask mAP50**, not just aggregate — last round's aggregate
  65.0% hid that corrosion and disjoint_part were near zero.
- **Size-bucketed Mask mAP** (tiny <0.05% of image area / small 0.05-0.2% /
  medium >0.2%) — needed to tell whether an improvement is broad or is just
  moving the strong classes around.
- Re-run the existing Direct-vs-SAHI M5 MacBook benchmark on the new
  champion only if it's actually promoted to production — don't burn time
  re-benchmarking every intermediate experiment.

## 5. Deliverables

1. Unified, deduped 7-class dataset (positives) + a separate hard-negative
   image pool with empty label files, both with a documented source
   manifest (which raw dataset each image came from, license).
2. Data pipeline scripts: taxonomy remap, dedup, negative-ratio injection as
   a configurable parameter.
3. Training run log for every experiment in §2, in the Week-7 report table
   format (config → metrics → one-line verdict).
4. Updated evaluation script implementing §4's new metrics.
5. A short recommendation memo: which config is the new champion, and why —
   written so it can drop directly into next week's report.

## 6. Open questions the plan agent should resolve by scanning the repo

Don't guess these — read the actual codebase and ask if still unclear:

- Exact paths to the existing data pipeline, training config, and the
  Model 1 backbone weights referenced in Week 7.
- Whether `data/raw/DATASET_AUDIT.md` (the raw-dataset audit) already
  exists in-repo or needs to be added.
- What YOLO26-seg config format / CLI the existing runs use, so new runs
  are launched the same way.
