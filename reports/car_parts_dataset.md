# Car Parts Dataset — Analysis Report

**Location analyzed:** `data/raw/archive/Car parts dataset/File1`
**Date:** 2026-08-27
**Format:** Supervisely export (`meta.json` + per-image JSON annotations + rasterized masks)

Despite its name, this is a **damage-type dataset (8 defect classes)** — Stage 2 material, not panel segmentation.

## 1. Structure

```
Car parts dataset/
├── meta.json                 # 8 class definitions (Supervisely project meta)
└── File1/
    ├── img/                  # 814 images (731 PNG, 83 JPEG)
    ├── ann/                  # 814 per-image JSON annotation files
    ├── masks_machine/        # 814 clean color-indexed masks (image-sized)
    └── masks_human/          # 814 rendered visualizations (NOT usable masks)
```

**Pairing integrity: perfect.** Every image has exactly one annotation file and one mask in each mask directory; no orphans in either direction, no byte-level duplicate images (MD5 check).

## 2. Classes & Volume

**814 images, 9,084 polygon annotations** (100% polygon geometry). Every image has ≥1 object.

| Class | Instances | Images | → 7-class taxonomy |
|---|---:|---:|---|
| Scratch | 3,242 | 517 | `scratch` |
| Dent | 1,664 | 629 | `dent` |
| Broken part | 1,500 | 664 | `disjoint_part` |
| Paint chip | 1,356 | 279 | `corrosion` (judgment call) |
| Missing part | 632 | 434 | `disjoint_part` |
| Flaking | 337 | 108 | `corrosion` |
| Corrosion | 277 | 109 | `corrosion` |
| Cracked | 76 | 67 | `crack` |

Objects per image: min 1, median 9, mean 11.2, max 136.

**Taxonomy notes:**
- This dataset is the strongest available source for the two known weak classes: **disjoint_part** (2,132 instances from Broken/Missing part) and **corrosion-family** surface damage (up to 1,970 instances if Paint chip + Flaking are folded into corrosion).
- Paint chip / Flaking are paint-film degradation, not rust; mapping them to `corrosion` is a decision that should be confirmed before merge. Alternative: drop them.
- No coverage for `glass_shatter` or `broken_lamp`.
- Labeled Jan–Apr 2023 by two annotators (GhazalehHITL 7,762, MojtabaHITL 1,322 objects).

## 3. Image Characteristics

- Width 487–1,122 px, height 280–690 px; most common size 574×429.
- No native splits; filenames `Car damages NNN` run 101–1352 with 438 gaps in numbering.
- Modest resolution — below/similar to the locked 1024×1024 training tile size, so no downscaling needed.

## 4. Masks

**`masks_machine/` — usable.** Exact image dimensions, black background + exactly 8 flat colors, one per class. **Caution: the mask colors do NOT match `meta.json` colors** (meta colors are the labeling-tool UI palette). Empirically verified color→class mapping (polygon rasterization overlaid on masks, 400 images):

| Mask color | Class | Confidence |
|---|---|---:|
| `#6666FF` | Scratch | 97% |
| `#33FF66` | Broken part | 97%* |
| `#FF33FF` | Dent | 85% |
| `#FF9933` | Paint chip | 96% |
| `#FF3333` | Missing part | 92% |
| `#99CCFF` | Corrosion | 98% |
| `#33FFFF` | Flaking | 96% |
| `#FFFF33` | Cracked | 100% |

\* per class→color direction; the lower color→class figure for Broken part/Dent is caused by overlapping polygons, not mapping ambiguity. Each class maps to exactly one color.

Pixel share is tiny (largest class = 4.76% of pixels) — defects are small relative to the frame.

**`masks_human/` — NOT usable for training.** These are 2× image width (e.g. 1275×440 for a 637×440 image) side-by-side rendered visualizations with ~129k colors. Visualization/QC artifacts only.

## 5. Label Quality

- 4 zero-area polygons and 286 polygons < 10 px² (~3% of all instances) — drop during conversion.
- Median polygon area is only **363 px²** (≈19×19 px). These are exactly the tiny-instance regime that destroyed corrosion signal last round — native-resolution training + SAHI are mandatory to benefit from them.
- 4 polygons have interior holes (valid COCO-compatible if handled).
- Polygon point counts: 3–308, median 9 — thin scratch/crack polygons present; keep mask-level NMS requirement in mind.

## 6. Recommendations for Stage 2 Integration

1. **Convert Supervisely JSON → unified COCO** using `classTitle` (ignore `classId`); remap per the table in §2.
2. Use polygons from `ann/`, not the masks; use `masks_machine` only for validation. Discard `masks_human`.
3. Drop zero-area and <10 px² polygons during conversion.
4. Confirm the Paint chip / Flaking → `corrosion` mapping decision before merge.
5. Split assignment: no native splits exist — route through the standard MD5 dedup + split-assignment path (default to train; verify no hash overlap with CarDD/Car defect 2200 test splits to avoid leakage).
6. This dataset directly targets the corrosion/disjoint_part weakness — prioritize including it in the retraining mix.
