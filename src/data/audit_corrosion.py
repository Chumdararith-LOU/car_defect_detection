#!/usr/bin/env python3
"""Corrosion tiny-instance audit.

Compares corrosion mask areas (px^2) across the train splits of
yolo_seg/, yolo_seg_clean/, yolo_seg_clean_augmented/.

Reports percentiles p1/p5/p25/p50/p75/p95/p99 and the count of instances
with area < 500 px^2 (the thesis's "tiny" threshold).

Outputs:
    reports/corrosion_audit.json
    reports/corrosion_hist.png

Prints a one-line verdict:
    SAFE  - tiny corrosion preserved
    RISK  - N tiny instances lost vs yolo_seg, use yolo_seg + rare-class augmentation instead
"""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

TINY_PX2 = 500.0
CORROSION_CLASS = 1  # index in the 7-class taxonomy
DATASETS = ["yolo_seg", "yolo_seg_clean", "yolo_seg_clean_augmented"]
PERCENTILES = [1, 5, 25, 50, 75, 95, 99]


def shoelace_area_px(pts, w, h):
    """Shoelace area in px^2 for normalized polygon points [x1,y1,...]."""
    if len(pts) < 6:
        return 0.0
    xs = np.array(pts[0::2], dtype=np.float64) * w
    ys = np.array(pts[1::2], dtype=np.float64) * h
    return 0.5 * abs(np.dot(xs, np.roll(ys, -1)) - np.dot(ys, np.roll(xs, -1)))


def image_size(path):
    with Image.open(path) as im:
        return im.size  # (w, h)


def audit_dataset(root, split="train"):
    img_dir = root / "images" / split
    lbl_dir = root / "labels" / split
    areas = []
    for lbl in sorted(lbl_dir.glob("*.txt")):
        img = img_dir / (lbl.stem + ".jpg")
        if not img.exists():
            img = img_dir / (lbl.stem + ".png")
        if not img.exists():
            img = img_dir / (lbl.stem + ".jpeg")
        if not img.exists():
            img = img_dir / (lbl.stem + ".JPEG")
        if not img.exists():
            continue
        w, h = image_size(img)
        for line in lbl.read_text().splitlines():
            if not line.strip():
                continue
            p = line.split()
            if len(p) < 7 or (len(p) - 5) % 2 != 0:
                continue
            if int(p[0]) != CORROSION_CLASS:
                continue
            areas.append(shoelace_area_px([float(v) for v in p[5:]], w, h))
    areas = np.array(areas, dtype=np.float64)
    out = {
        "n_instances": int(len(areas)),
        "n_tiny_lt_500px2": int((areas < TINY_PX2).sum()),
        "percentiles_px2": {f"p{q}": float(np.percentile(areas, q)) if len(areas) else None for q in PERCENTILES},
    }
    return out, areas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--report", type=Path, default=Path("reports/corrosion_audit.json"))
    parser.add_argument("--hist", type=Path, default=Path("reports/corrosion_hist.png"))
    args = parser.parse_args()

    report = {}
    all_areas = {}
    for name in DATASETS:
        root = args.data_root / name
        if not (root / "labels" / "train").is_dir():
            print(f"[warn] missing {root}/labels/train, skipped")
            continue
        print(f"[audit] {name} ...", flush=True)
        stats, areas = audit_dataset(root)
        report[name] = stats
        all_areas[name] = areas
        print(f"  n={stats['n_instances']} tiny(<500px2)={stats['n_tiny_lt_500px2']} "
              f"p50={stats['percentiles_px2']['p50']:.1f}px2")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    print(f"[audit] report -> {args.report}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, areas in all_areas.items():
        if len(areas) == 0:
            continue
        tiny = areas[areas < TINY_PX2]
        ax.hist(np.clip(areas, 0, 5000), bins=100, range=(0, 5000),
                alpha=0.5, label=f"{name} (n={len(areas)}, tiny={len(tiny)})")
    ax.set_xscale("log")
    ax.set_xlabel("corrosion mask area (px^2, log scale, clipped at 5000)")
    ax.set_ylabel("instance count")
    ax.set_title("Corrosion mask-area distribution (train splits)")
    ax.axvline(TINY_PX2, color="red", linestyle="--", label="tiny threshold (500 px^2)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.hist, dpi=120)
    print(f"[audit] histogram -> {args.hist}")

    base = report.get("yolo_seg", {}).get("n_tiny_lt_500px2")
    name = "yolo_seg_clean_augmented"
    if name in report and base is not None:
        lost = base - report[name]["n_tiny_lt_500px2"]
        if lost > 0:
            print(f"RISK — {lost} tiny corrosion instances lost vs yolo_seg "
                  f"({report[name]['n_tiny_lt_500px2']} remain in {name}), "
                  f"use yolo_seg + rare-class augmentation instead")
        else:
            print(f"SAFE — tiny corrosion preserved in {name} "
                  f"({report[name]['n_tiny_lt_500px2']} vs {base} in yolo_seg)")


if __name__ == "__main__":
    main()
