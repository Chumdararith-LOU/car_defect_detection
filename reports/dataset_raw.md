# Raw Dataset Analysis Report

**Location analyzed:** `data/raw/`
**Date:** 2026-08-26

## 1. Overview

The raw data directory contains **5 top-level sources** (11 distinct datasets) covering car defect detection, damage segmentation, rust/corrosion, cracks, and car-part segmentation. Annotation formats are predominantly **COCO JSON**, with mask-based datasets under `archive/`.

```
data/raw/
├── Car defect 2000 new/     # COCO detection (10 defect classes)
├── Car defect 2200/         # COCO detection (10 defect classes, near-duplicate of above)
├── CarDD_release/           # CarDD benchmark (COCO + Salient Object Detection)
├── Roboflow/                # 6 Roboflow exports (COCO format)
└── archive/                 # 2 mask-based datasets (car damages, car parts)
```

### Summary table

| # | Dataset | Source | Splits (images) | Annotations | Classes | Format |
|---|---------|--------|-----------------|-------------|---------|--------|
| 1 | Car defect 2000 new | custom | 5,436 (single) | 37,439 | 10 defect | COCO |
| 2 | Car defect 2200 | custom | 5,435 (single) | 37,558 | 10 defect | COCO |
| 3 | CarDD_COCO | CarDD benchmark | train 2,816 / val 810 / test 374 | 6,211 / 1,744 / 785 | 6 defect | COCO |
| 4 | CarDD_SOD | CarDD benchmark | TR 2,816 / VAL 810 / TE 374 (img+mask) | binary masks | defect masks | SOD masks + pair lists |
| 5 | Roboflow: Car Defect Detection | Roboflow | train 8,566 / valid 826 / test 422 | 16,814 / 1,669 / 886 | 8 (messy labels) | COCO |
| 6 | Roboflow: Rust Detection | Roboflow | train 9,472 / valid 295 / test 296 | 52,024 / 1,125 / 1,187 | 11 corrosion | COCO |
| 7 | Roboflow: car defect.v1i | Roboflow | train 4,901 / valid 1,052 / test 1,047 | 30,065 / 6,024 / 6,065 | 6 (numeric labels) | COCO |
| 8 | Roboflow: car-damage-detection.v1i | Roboflow | train 2,816 (no val/test) | 6,211 | 7 damage | COCO |
| 9 | Roboflow: crack_v2.v1i | Roboflow | train 290 / valid 93 / test 31 | 570 / 176 / 71 | 2 crack | COCO |
| 10 | Roboflow: socarC.v1i | Roboflow | train 21,260 / valid 2,470 / test 986 | 65,599 / 7,727 / 3,053 | 5 damage types | COCO |
| 11a | archive: Car damages dataset | CarDD paper | 998 (no splits) | masks + part polygons | 21 car parts | masks (human/machine) + meta.json |
| 11b | archive: Car parts dataset | CarDD paper | 814 (no splits) | masks | 8 damage | masks (human/machine) + meta.json |

**Approximate total images (including overlaps): ~71,500**

---

## 2. Dataset Details

### 2.1 Car defect 2000 new / Car defect 2200

- **Structure:** `annotations/instances_default.json` + `images/default/`
- **Size:** 5,436 vs 5,435 images; 37,439 vs 37,558 annotations
- **Classes (10, identical taxonomy):** `dent`, `ding`, `deform`, `scratch_hairline`, `scratch_gouge`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion`, `broken_components`
- **Note:** The two datasets are nearly identical in size and taxonomy — they appear to be two versions of the same dataset ("2200" likely a superset/updated export). No train/val/test split.

### 2.2 CarDD_release (CarDD benchmark)

**CarDD_COCO** (detection):
- `train2017`: 2,816 images / 6,211 annotations
- `val2017`: 810 images / 1,744 annotations
- `test2017`: 374 images / 785 annotations
- **Classes (6):** `dent`, `scratch`, `crack`, `glass shatter`, `lamp broken`, `tire flat`
- Extra file: `image_info.xlsx`

**CarDD_SOD** (salient object detection, same image set as COCO):
- `CarDD-TR` / `CarDD-VAL` / `CarDD-TE`, each containing `*-Image`, `*-Mask`, `*-Edge` folders plus `train_pair.lst`
- 2,816 / 810 / 374 image-mask pairs respectively

### 2.3 Roboflow exports (all COCO format, `train/valid/test` + `_annotations.coco.json`)

| Dataset | train (img/ann) | valid (img/ann) | test (img/ann) | Categories |
|---------|-----------------|------------------|----------------|------------|
| Car Defect Detection.coco-segmentation | 8,566 / 16,814 | 826 / 1,669 | 422 / 886 | `car-scratch-dent-dirt`, `1`–`5`, `2 0 0 0 1 1 1 1 0 0 0`, `object` |
| Rust Detection.v1i | 9,472 / 52,024 | 295 / 1,125 | 296 / 1,187 | `rust`, `Rust`, `car`, `copper corrosion`, `corroded-part`, `corrosion`, `iron rust`, `mild-corrosion`, `moderate-corrosion`, `severe-corrosion` |
| car defect.v1i | 4,901 / 30,065 | 1,052 / 6,024 | 1,047 / 6,065 | `car-G2ce`, `0`, `1`, `2`, `3`, `object` |
| car-damage-detection.v1i | 2,816 / 6,211 | — | — | `car_damage`, `crack`, `dent`, `glass shatter`, `lamp broken`, `scratch`, `tire flat` |
| crack_v2.v1i | 290 / 570 | 93 / 176 | 31 / 71 | `crack-4VtJ`, `- crack_v1 - 2024-09-12 5-58am` |
| socarC.v1i | 21,260 / 65,599 | 2,470 / 7,727 | 986 / 3,053 | `objects`, `Breakage`, `Crushed`, `Scratched`, `Separated` |

### 2.4 archive/

Both datasets use `File1/{ann, img, masks_human, masks_machine}` layout with a Roboflow-style `meta.json`:

- **Car damages dataset:** 998 images with matching human and machine masks; meta classes are **21 car parts** (`Quarter-panel`, `Front-wheel`, `Back-window`, `Trunk`, `Front-door`, `Rocker-panel`, `Grille`, `Windshield`, `Front-window`, `Back-door`, `Headlight`, `Back-wheel`, `Back-windshield`, `Hood`, `Fender`, `Tail-light`, `License-plate`, `Front-bumper`, `Back-bumper`, `Mirror`, `Roof`)
- **Car parts dataset:** 814 images with matching human and machine masks; meta classes are **8 damage types** (`Missing part`, `Broken part`, `Scratch`, `Cracked`, `Dent`, `Flaking`, `Paint chip`, `Corrosion`)

---

## 3. Key Findings

### 3.1 Duplicates / overlaps
1. **`Roboflow/car-damage-detection.v1i.coco` is identical to `CarDD_COCO/train2017`** (same 2,816 images, same 6,211 annotations, same categories). One should be dropped.
2. **`Car defect 2000 new` vs `Car defect 2200`** are near-duplicates (5,436 vs 5,435 images, same 10-class taxonomy). Deduplication check recommended; likely only one is needed.
3. **`CarDD_SOD` shares the exact same images as `CarDD_COCO`** (2,816/810/374) — different annotation modality (masks), not new images.

### 3.2 Data quality issues
1. **Messy category names** in several Roboflow exports:
   - Numeric/opaque labels: `0`–`5`, `object` (`car defect.v1i`, `Car Defect Detection`)
   - Hash suffixes: `car-G2ce`, `crack-4VtJ`
   - Garbage label: `2 0 0 0 1 1 1 1 0 0 0`
   - Case/format duplicates: `rust` vs `Rust`; `car_damage` vs individual damage types in the same file
2. **Inconsistent taxonomies** across datasets (e.g., `scratch_hairline`/`scratch_gouge` vs `scratch`; `glass_shatter` vs `glass shatter`; `corrosion` vs `rust` family) — a unified class mapping is required before merging.
3. **Split imbalance:** `Rust Detection` is ~94% train; `car-damage-detection.v1i` has no valid/test split; `crack_v2` is very small (414 images total).

### 3.3 Strengths
- Large combined pool (~71.5k images) covering dents, scratches, cracks, glass breakage, lamps, corrosion/rust, and flat tires.
- CarDD provides a clean, well-structured benchmark with official train/val/test splits and both bbox and mask annotations.
- `Car defect 2000/2200` offer the most granular defect taxonomy (10 fine-grained classes).

---

## 4. Recommendations

1. **Deduplicate:** remove `Roboflow/car-damage-detection.v1i.coco` (CarDD duplicate) and reconcile the two "Car defect" versions.
2. **Define a unified taxonomy**, e.g.: `dent`, `scratch`, `crack`, `glass_shatter`, `broken_lamp`, `corrosion/rust`, `tire_flat`, `deform/ding`, `broken_components` — and map every source dataset onto it.
3. **Clean labels:** resolve numeric/hash categories in Roboflow exports using their `README.dataset.txt` files before any merge.
4. **Create consistent splits** for datasets lacking them (Car defect 2000/2200, archive datasets), ensuring no image-level leakage between train/val/test across merged sources.
5. **Verify domain relevance** of `socarC.v1i` (its classes `Breakage`/`Crushed`/`Scratched`/`Separated` may not be car-specific) before including it.
