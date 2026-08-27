# YOLO-seg Dataset Audit Report — Baseline Readiness

**Audited:** `data/processed/yolo_seg/` + source COCO JSONs `data/processed/annotations/`
**Date:** 2026-08-27
**Purpose:** Pre-training certification for the Stage 2 baseline run (YOLO-seg, 7-class)

---


The dataset is **structurally sound and ready for the baseline training run**. Zero syntax errors, zero orphan files, zero empty labels, full image↔label pairing, and the one count anomaly found (test +3 lines) was root-caused and is benign. Class imbalance is severe but is a known, documented property of this data mix — not a corruption.

---

## 1. Structural & File Integrity

| Split | Images | Labels | Orphan images | Orphan labels | Non-image files | Empty labels |
|---|---:|---:|---:|---:|---:|---:|
| train | 12,464 | 12,464 | 0 | 0 | 0 | 0 |
| val   | 998    | 998    | 0 | 0 | 0 | 0 |
| test  | 577    | 577    | 0 | 0 | 0 | 0 |

- Every image has exactly one `.txt` with the identical stem. ✅
- **0 empty label files** in all splits — consistent with clean-negative injection being skipped for this baseline. ✅
- `data.yaml` matches the 7-class taxonomy and split layout. Note: it uses the relative path `../data/processed/yolo_seg`, so training must be launched from `src/` (or the yaml path must be made absolute).

## 2. Label Format & Syntax

All **14,039 label files / 94,368 label lines** parsed programmatically:

| Check | Result |
|---|---|
| Line format `[class] x1 y1 ... xn yn` | 0 violations |
| class_id integer in [0, 6] | 0 violations |
| Coordinates float in [0.0, 1.0] | 0 violations |
| ≥3 polygon points (≥6 coords) | 0 violations |
| Odd coordinate counts | 0 violations |
| Blank lines | 0 |

**Total syntax errors: 0.** ✅

## 3. Class Distribution

| Class (YOLO id) | Train | Val | Test | Train % |
|---|---:|---:|---:|---:|
| corrosion (1) | 51,521 | 1,054 | 1,145 | **57.8%** |
| scratch (6) | 20,078 | 738 | 677 | 22.5% |
| dent (3) | 7,994 | 510 | 255 | 9.0% |
| broken_lamp (0) | 6,422 | 141 | 75 | 7.2% |
| disjoint_part (4) | 1,703 | **32** | 96 | 1.9% |
| crack (2) | 981 | 177 | 86 | 1.1% |
| glass_shatter (5) | 477 | 135 | 71 | 0.5% |
| **Total** | **89,176** | **2,787** | **2,402*** | |

\* COCO test.json has 2,402 annotations; YOLO labels contain 2,405 lines. See §6 — explained, not an error.

- **disjoint_part val patch verified:** 32 instances in val (>0). ✅ Still thin — expect noisy per-class val mAP for it.
- **corrosion dominates at 57.8%** of train instances (108:1 vs glass_shatter). Long-tail classes: `glass_shatter` (477), `crack` (981), `disjoint_part` (1,703).
- Split proportions are broadly consistent across train/val/test for all classes (no split-skew red flags).

## 4. Geometric Sanity (BBox-Fallback vs Real Polygons)

Rectangles = exactly 4 axis-aligned corner points (bbox-fallback signature).

| Class | Train rect | Train irreg | Rect % | Val rect % | Test rect % |
|---|---:|---:|---:|---:|---:|
| corrosion | 31,044 | 20,477 | **60.3%** | 64.8% | 59.7% |
| scratch | 104 | 19,974 | 0.5% | 0% | 0.1% |
| dent | 28 | 7,966 | 0.4% | 0% | 0% |
| glass_shatter | 16 | 461 | 3.4% | 7.4% | 2.8% |
| broken_lamp | 0 | 6,422 | 0% | 0% | 0% |
| crack | 0 | 981 | 0% | 0% | 0% |
| disjoint_part | 0 | 1,703 | 0% | 0% | 0% |

- Matches expectation: **corrosion is the bbox-fallback class** (Roboflow rust exports are detection-only). ~60% of all corrosion instances are synthetic rectangles.
- Thin-defect classes (`scratch`, `crack`) are ~100% real polygons — no accidental bbox degradation there. ✅
- Known ceiling: rectangle masks cap corrosion mask-mAP potential; irregular-mask corrosion comes from CarDD + Supervisely sources.

## 5. Visual Sanity Check

13 annotated renders saved to `reports/dataset_audit_visuals/`:
- 5 random train + 5 random val samples
- 3 Supervisely ("Car parts dataset") images + 1 more picked randomly (`supervisely_Car damages 606`)

Polygon fills, outlines, bboxes, and class labels drawn per class color. Supervisely renders confirm masks align with actual damage regions — the empirically-derived color→class mapping from the integration report holds.

## 6. Anomalies & Root Causes

| # | Finding | Severity | Resolution |
|---|---|---|---|
| 1 | Test: YOLO 2,405 lines vs COCO 2,402 anns (+3, all scratch) | Warning | Root-caused to a single image `cardd_test_000152.jpg`: one `iscrowd=1` scratch annotation stored as a **multi-region RLE** was decomposed into 4 separate polygons during conversion. 4 − 1 = +3. Correct behavior, no data lost. |
| 2 | corrosion 57.8% of train | Warning | Known data-mix property. Per-class mAP reporting is mandatory (locked requirement) so this cannot hide weak-class regression. |
| 3 | ~60% of corrosion masks are bbox rectangles | Warning | Expected (bbox-fallback policy). Flag in the run log; consider mask refinement later. |
| 4 | disjoint_part val = 32 | Warning | Patch achieved its goal (>0) but per-class val mAP for it will be high-variance. Cross-check with test (96). |
| 5 | Filenames with spaces (`supervisely_Car damages NNN`) | Info | YOLO handles these fine; audit tooling needed explicit extension lookup. No action needed. |
| 6 | 0 clean-negative images | Info | Deliberate for this baseline; clean-image FP rate metric still required at evaluation time. |

No critical errors found.

## 7. Summary Table

| Metric | Value |
|---|---|
| Train / Val / Test images | 12,464 / 998 / 577 |
| Train / Val / Test instances | 89,176 / 2,787 / 2,402 |
| Label syntax errors | 0 |
| Orphan files | 0 |
| Empty labels | 0 |
| disjoint_part in val | 32 ✅ |
| Dominant class | corrosion 57.8% |
| Long tail | glass_shatter 0.5%, crack 1.1% |
| Visual spot-checks | 13 renders, all consistent |
