#!/usr/bin/env python3
"""
Port of Phase 3 notebook Cells 13-14: Threshold sweep for rare classes.
Runs on Mac MPS/CPU, uses the local SAHI engine, validates the balanced preset.
"""

from pathlib import Path

import cv2
import numpy as np
import importlib.util

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
VAL_DIR = REPO_ROOT / "data" / "processed" / "yolo_seg_clean_2200_7cls" / "val"
VAL_IMAGES = VAL_DIR / "images"
VAL_LABELS = VAL_DIR / "labels"
MODEL_PATH = (
    REPO_ROOT
    / "runs"
    / "segment"
    / "model5_resume_adapt_7cls"
    / "stage2_differential_finetune_7cls"
    / "weights"
    / "best.pt"
)
SAHI_MODULE = REPO_ROOT / "src" / "stage2" / "inference" / "sahi_inference.py"
CONFIG_PATH = REPO_ROOT / "configs" / "inference" / "sahi_production.yaml"

# Load SAHI module dynamically
spec = importlib.util.spec_from_file_location("sahi_inference", SAHI_MODULE)
si = importlib.util.module_from_spec(spec)
spec.loader.exec_module(si)

# Load config and set to calib preset (low thresholds for sweep)
cfg = si.load_config(str(CONFIG_PATH))
cfg["preset"] = "calib"

# Initialize engine
print(f"Loading model from {MODEL_PATH}...")
engine = si.SahiInference(str(MODEL_PATH), cfg)

# Target classes
TARGET_CLASSES = {5: "corrosion", 6: "disjoint_part"}


def mask_ios(a_mask, a_area, b_mask, b_area):
    """Intersection over Smaller area for masks."""
    inter = int(np.logical_and(a_mask, b_mask).sum())
    smaller = min(a_area, b_area)
    return inter / smaller if smaller > 0 else 0.0


def collect_gt_and_preds():
    """Run SAHI on all val images, collect GT masks and predictions."""
    calib_data = []
    label_files = sorted(VAL_LABELS.glob("*.txt"))
    print(f"Scanning {len(label_files)} validation images...")

    for idx, label_file in enumerate(label_files):
        img_name = label_file.stem
        img_path = None
        for ext in [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]:
            p = VAL_IMAGES / (img_name + ext)
            if p.exists():
                img_path = p
                break
        if not img_path:
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            continue
        H0, W0 = img.shape[:2]

        # Parse GT masks for rare classes
        gt_masks = []
        with open(label_file) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 7 and int(parts[0]) in TARGET_CLASSES:
                    coords = list(map(float, parts[1:]))
                    pts = np.array(
                        [
                            [int(coords[i] * W0), int(coords[i + 1] * H0)]
                            for i in range(0, len(coords) - 1, 2)
                        ],
                        np.int32,
                    )
                    m = np.zeros((H0, W0), np.uint8)
                    cv2.fillPoly(m, [pts], 1)
                    gt_masks.append(
                        {
                            "cls": int(parts[0]),
                            "mask": m.astype(bool),
                            "area": int(m.sum()),
                        }
                    )

        # Run SAHI with calib preset (low thresholds)
        preds = [p for p in engine.predict(str(img_path)) if p["cls"] in TARGET_CLASSES]
        calib_data.append({"img": img_name, "gt": gt_masks, "pred": preds})

        if (idx + 1) % 20 == 0:
            print(f"  Processed {idx + 1}/{len(label_files)}...")

    return calib_data


def eval_thresh(calib_data, cls_id, thresh):
    """Compute P/R/F1 at a given threshold using mask-IOS matching."""
    tp = fp = fn = 0
    for c in calib_data:
        gts = [g for g in c["gt"] if g["cls"] == cls_id]
        preds = [p for p in c["pred"] if p["cls"] == cls_id and p["score"] >= thresh]
        used = [False] * len(gts)
        for p in preds:
            best_i, best_v = -1, 0.0
            for j, g in enumerate(gts):
                if used[j]:
                    continue
                v = mask_ios(p["mask"], p["area"], g["mask"], g["area"])
                if v > best_v:
                    best_i, best_v = j, v
            if best_i >= 0 and best_v >= 0.5:
                used[best_i] = True
                tp += 1
            else:
                fp += 1
        fn += sum(1 for u in used if not u)

    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return prec, rec, f1, tp, fp, fn


def main():
    print("=" * 70)
    print("THRESHOLD SWEEP EVALUATION (Phase 3, Cells 13-14)")
    print("=" * 70)
    print(f"Validation set: {VAL_IMAGES}")
    print(f"Model: {MODEL_PATH}")
    print("SAHI preset: calib (low thresholds for sweep)")
    print()

    calib_data = collect_gt_and_preds()

    n_p5 = sum(len([p for p in c["pred"] if p["cls"] == 5]) for c in calib_data)
    n_p6 = sum(len([p for p in c["pred"] if p["cls"] == 6]) for c in calib_data)
    print(f"\nPredictions collected: corrosion={n_p5}, disjoint_part={n_p6}")
    print()

    for cls_id, name in [(5, "corrosion"), (6, "disjoint_part")]:
        print(f"\n{'='*10} {name} {'='*10}")
        print(
            f"{'thresh':>6} | {'precision':>9} | {'recall':>6} | {'F1':>6} | {'TP':>3} {'FP':>3} {'FN':>3}"
        )
        print("-" * 60)
        for t in np.arange(0.05, 0.501, 0.05):
            prec, rec, f1, tp, fp, fn = eval_thresh(
                calib_data, cls_id, round(float(t), 2)
            )
            marker = ""
            if name == "corrosion" and abs(t - 0.15) < 0.001:
                marker = " ← balanced preset"
            elif name == "disjoint_part" and abs(t - 0.15) < 0.001:
                marker = " ← balanced preset"
            print(
                f"  {t:.2f}  | {prec:>9.3f} | {rec:>6.3f} | {f1:>6.3f} | {tp:>3} {fp:>3} {fn:>3}{marker}"
            )


if __name__ == "__main__":
    main()
