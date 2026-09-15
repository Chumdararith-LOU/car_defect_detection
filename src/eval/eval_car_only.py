#!/usr/bin/env python3
"""Evaluate a trained segmentation model on the car-only test subset and compute
the clean-image false-positive rate.

  - per-class Mask mAP50 / P / R / F1 on the car-only test split
  - clean-image FPR: fraction of clean-car eval images with >=1 corrosion
    detection at each threshold (single conf=0.001 pass, post-hoc thresholding)
  - secondary: corrosion detection rate on non-car test images
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
for _p in (str(_PROJECT_ROOT), _VENDOR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ultralytics import YOLO  # noqa: E402

CORROSION = 1
IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def max_corrosion_conf(result) -> float:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return 0.0
    cls = boxes.cls.cpu().numpy()
    conf = boxes.conf.cpu().numpy()
    corr = conf[cls == CORROSION]
    return float(corr.max()) if len(corr) else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--car-test-data", required=True, help="data.yaml of the car-only test set")
    ap.add_argument("--clean-dir", required=True)
    ap.add_argument("--noncar-list", default=None)
    ap.add_argument("--imgsz", type=int, default=1024)
    ap.add_argument("--fpr-thresholds", default="0.15,0.25")
    ap.add_argument("--baseline", default="")
    ap.add_argument("--out", default="reports/clean_retrain_augmented_eval.md")
    args = ap.parse_args()

    model = YOLO(str(_PROJECT_ROOT / args.weights))
    thresholds = [float(t) for t in args.fpr_thresholds.split(",")]

    # --- 1. car-only test val (per-class Mask metrics) ---
    car_data = _PROJECT_ROOT / args.car_test_data
    ds = yaml.safe_load(car_data.read_text())
    names = ds["names"]
    results = model.val(data=str(car_data), imgsz=args.imgsz, conf=0.001, batch=8, device=0, verbose=False)
    seg = results.seg
    rows = []
    for i, c in enumerate(seg.ap_class_index):
        p, r = float(seg.p[i]), float(seg.r[i])
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        rows.append((names[c], float(seg.ap50[i]), p, r, f1))
    rows.sort(key=lambda x: x[0])

    # val's validator state pins ~20GB in the CUDA caching allocator; the predict
    # passes run on CPU (291 images, a few minutes) to avoid the OOM entirely
    del results
    import gc
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # --- 2. clean-image FPR ---
    clean_dir = _PROJECT_ROOT / args.clean_dir
    clean_imgs = sorted(p.name for p in clean_dir.iterdir() if p.suffix.lower() in IMG_EXTS)
    preds = model.predict(source=str(clean_dir), conf=0.001, imgsz=args.imgsz, batch=1, device="cpu", verbose=False)
    clean_max = [max_corrosion_conf(r) for r in preds]
    fpr = {t: float(np.mean([m >= t for m in clean_max])) for t in thresholds}

    # --- 3. secondary: non-car test images ---
    noncar_rate = None
    if args.noncar_list:
        noncar_names = [l.strip() for l in (_PROJECT_ROOT / args.noncar_list).read_text().splitlines() if l.strip()]
        noncar_dir = _PROJECT_ROOT / "data/processed/yolo_seg/images/test"
        srcs = [str(noncar_dir / n) for n in noncar_names if (noncar_dir / n).exists()]
        preds = model.predict(source=srcs, conf=0.001, imgsz=args.imgsz, batch=1, device="cpu", verbose=False)
        noncar_max = [max_corrosion_conf(r) for r in preds]
        noncar_rate = {t: float(np.mean([m >= t for m in noncar_max])) for t in thresholds}

    # --- report ---
    lines = [
        "# clean_retrain_augmented — evaluation",
        "",
        f"Weights: `{args.weights}`",
        "",
        "## Car-only test subset (Mask metrics)",
        "",
        f"Aggregate: mAP50={seg.map50:.4f}  mAP50-95={seg.map:.4f}  P={seg.mp:.4f}  R={seg.mr:.4f}",
        "",
        "| class | mAP50 | P | R | F1 |",
        "|---|---|---|---|---|",
    ]
    for name, ap50, p, r, f1 in rows:
        lines.append(f"| {name} | {ap50:.4f} | {p:.4f} | {r:.4f} | {f1:.4f} |")
    lines += [
        "",
        "## Clean-image false-positive rate (corrosion)",
        "",
        f"Clean eval images: {len(clean_imgs)}",
        "",
        "| threshold | FPR |",
        "|---|---|",
    ]
    for t in thresholds:
        lines.append(f"| {t} | {fpr[t]:.4f} |")
    if noncar_rate is not None:
        lines += ["", "## Non-car test images (secondary)", "", "| threshold | detection rate |", "|---|---|"]
        for t in thresholds:
            lines.append(f"| {t} | {noncar_rate[t]:.4f} |")
    if args.baseline:
        lines += ["", f"Baseline: {args.baseline} Mask mAP50", ""]
    out = _PROJECT_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")

    print(f"[eval] report written to {out}")
    print(f"[eval] car-only Mask mAP50={seg.map50:.4f}  mAP50-95={seg.map:.4f}")
    for name, ap50, p, r, f1 in rows:
        print(f"[eval]   {name:15s} mAP50={ap50:.4f} P={p:.4f} R={r:.4f} F1={f1:.4f}")
    for t in thresholds:
        print(f"[eval] clean FPR @ {t}: {fpr[t]:.4f}")
        if noncar_rate is not None:
            print(f"[eval] non-car detection rate @ {t}: {noncar_rate[t]:.4f}")


if __name__ == "__main__":
    main()
