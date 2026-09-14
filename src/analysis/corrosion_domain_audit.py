#!/usr/bin/env python3
"""
Corrosion Domain Audit — quantify out-of-domain corrosion images.

Scans train/val/test for images with corrosion annotations (class_id=1),
extracts per-image metadata, and classifies each as car / non-car /
ambiguous using filename, size, and count heuristics. No model needed.

Run on server:
  conda activate car_defect
  python src/analysis/corrosion_domain_audit.py

Outputs:
  reports/corrosion_domain_audit.md
  reports/corrosion_car_images.txt
  reports/corrosion_noncar_images.txt
  reports/corrosion_ambiguous_images.txt
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

SPLITS = ["train", "val", "test"]
CORROSION = 1
DATA_ROOT = "data/processed/yolo_seg"
OUTPUT_DIR = "reports"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

# Strong out-of-domain signals (web articles, screenshots, industrial subjects)
NONCAR_KEYWORDS = [
    "captura-de-tela", "screenshot", "encyclopedia", "encyclopdia", "wikipedia", "wiki",
    "blog", "article", "case-study", "vuetrade", "how-can-rust", "how-rust", "how-to",
    "how-indsturial", "how-industrial", "rust-removal", "rustremoval", "removal",
    "prevention", "prevenirla", "galvanic", "galvanica", "electrochemical",
    "pitting", "bolt", "fastener", "screw", "tornillos", "pipe", "pipeline",
    "industrial", "steel", "metal", "concrete", "concreto", "bridge", "ship",
    "tank", "valve", "weld", "flange", "gasket", "rebar", "re-bar", "anchor", "gears",
    "acid", "acids", "oxid", "oxida", "ximo", "material-corrosion", "steel-panel",
]
# Generic names that carry no domain information -> uncertain
GENERIC_NAME_RE = re.compile(r"^(img|image|images)[-_]?\d*$|^[a-z]{1,2}\d{1,3}$")
# Roboflow export suffix, e.g. "_jpg.rf.abc123" / "_png_jpg.rf.abc123"
ROBOFLOW_SUFFIX_RE = re.compile(r"_(?:jpg|jpeg|png|bmp)(?:_jpg)?\.rf\.[0-9a-f]+$")

CLOSEUP_AREA_PCT = 30.0
MAX_INSTANCES = 10


def corrosion_label_files(split):
    """Yield (image_name, [corrosion lines]) for images with >=1 corrosion annotation."""
    img_dir = Path(DATA_ROOT) / "images" / split
    lbl_dir = Path(DATA_ROOT) / "labels" / split
    if not img_dir.is_dir():
        print(f"  [!] {img_dir} not found, skipping split {split}")
        return
    for img_path in sorted(img_dir.iterdir()):
        if not (img_path.is_file() and img_path.suffix.lower() in IMAGE_EXTS):
            continue
        label_path = lbl_dir / (img_path.stem + ".txt")
        if not label_path.exists():
            continue
        lines = []
        with open(label_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5 and parts[0] == str(CORROSION):
                    lines.append(parts)
        if lines:
            yield img_path.name, lines


def parse_instances(lines):
    """Corrosion label lines (normalized coords) -> list of bbox area % of image."""
    areas = []
    for parts in lines:
        coords = [float(x) for x in parts[1:]]
        if len(coords) % 2 == 1:
            coords = coords[:-1]
        if len(coords) < 4:
            continue
        if len(coords) == 4:  # detection format: cx cy w h
            cx, cy, w, h = coords
            x1, y1, x2, y2 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        else:  # segmentation format: polygon vertices
            xs, ys = coords[0::2], coords[1::2]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
        areas.append(100.0 * max(0.0, (x2 - x1) * (y2 - y1)))
    return areas


def rust_band_fraction(img_bgr):
    """Fraction of pixels in the rust brown/orange HSV band (weak texture signal)."""
    small = cv2.resize(img_bgr, (64, 64), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    mask = (h >= 5) & (h <= 25) & (s >= 40) & (v >= 40) & (v <= 220)
    return float(mask.mean())


def classify(name, n_instances, areas):
    """Return (label, reasons). label in {car, non-car, ambiguous}."""
    stem = name.lower()
    reasons = []
    kw_hits = [k for k in NONCAR_KEYWORDS if k in stem]
    if kw_hits:
        reasons.extend(f"filename:{k}" for k in kw_hits)
    closeup = bool(areas) and all(a > CLOSEUP_AREA_PCT for a in areas)
    if closeup:
        reasons.append(f"close-up: all {n_instances} instance(s) > {CLOSEUP_AREA_PCT:.0f}% of image")
    if n_instances > MAX_INSTANCES:
        reasons.append(f"> {MAX_INSTANCES} corrosion instances ({n_instances})")
    base = ROBOFLOW_SUFFIX_RE.sub("", stem)
    if GENERIC_NAME_RE.match(base) and not kw_hits:
        reasons.append("generic/unverifiable filename")

    if kw_hits:
        label = "non-car"
    elif reasons:
        label = "ambiguous"  # geometry/generic-name flags alone are weak (car close-ups exist)
    else:
        label = "car"
    return label, reasons


def main():
    print("=" * 80)
    print("CORROSION DOMAIN AUDIT")
    print("=" * 80)

    records = []
    for split in SPLITS:
        print(f"[*] Scanning {split}...")
        n = 0
        for name, lines in corrosion_label_files(split):
            img = cv2.imread(os.path.join(DATA_ROOT, "images", split, name))
            if img is None:
                print(f"  [!] unreadable image {name}, skipping")
                continue
            h, w = img.shape[:2]
            areas = parse_instances(lines)
            label, reasons = classify(name, len(areas), areas)
            records.append({
                "split": split, "name": name, "n_instances": len(areas),
                "mean_area_pct": float(np.mean(areas)) if areas else 0.0,
                "aspect_ratio": w / h if h else 1.0,
                "rust_frac": rust_band_fraction(img),
                "label": label, "reasons": reasons,
            })
            n += 1
        print(f"    {n} corrosion images")

    total = len(records)
    by_label = {l: [r for r in records if r["label"] == l] for l in ("car", "non-car", "ambiguous")}
    print(f"[*] Classified: car={len(by_label['car'])} non-car={len(by_label['non-car'])} "
          f"ambiguous={len(by_label['ambiguous'])}")

    # Report
    L = []
    L.append("# Corrosion Domain Audit\n")
    L.append(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append(f"- **Scope:** corrosion-annotated images (class_id=1) in train/val/test of `{DATA_ROOT}`")
    L.append("- **Classification rule:** filename keyword hit -> non-car; size/count/generic-name "
             "flags only -> ambiguous (close-ups of car panels are legitimate); no flags -> car.")
    L.append("- **Color metadata:** rust_frac = pixel fraction in rust brown/orange HSV band "
             "(H 5-25, S>=40, V 40-220) on a 64x64 downscale.\n")

    L.append("## Totals\n")
    L.append("| Split | Corrosion images |")
    L.append("|---|---|")
    for split in SPLITS:
        L.append(f"| {split} | {sum(1 for r in records if r['split'] == split)} |")
    L.append(f"| **total** | **{total}** |\n")

    L.append("## Car vs Non-car Split\n")
    L.append("| Class | Count | % of total |")
    L.append("|---|---|---|")
    for label in ("car", "non-car", "ambiguous"):
        n = len(by_label[label])
        L.append(f"| {label} | {n} | {100.0 * n / total:.1f}% |" if total else f"| {label} | 0 | 0% |")
    L.append("")
    L.append("| Split | car | non-car | ambiguous |")
    L.append("|---|---|---|---|")
    for split in SPLITS:
        row = [sum(1 for r in records if r["split"] == split and r["label"] == l)
               for l in ("car", "non-car", "ambiguous")]
        L.append(f"| {split} | {row[0]} | {row[1]} | {row[2]} |")
    L.append("")

    L.append("## Top 50 Most Likely Non-car\n")
    L.append("| # | Split | Filename | Reasons |")
    L.append("|---|---|---|---|")
    top = sorted(by_label["non-car"],
                 key=lambda r: (-len([x for x in r["reasons"] if x.startswith("filename:")]),
                                -r["rust_frac"]))[:50]
    for i, r in enumerate(top, 1):
        L.append(f"| {i} | {r['split']} | `{r['name']}` | {'; '.join(r['reasons'])} |")
    L.append("")

    L.append("## Corrosion Instances by Class\n")
    L.append("| Class | Total instances | Mean per image |")
    L.append("|---|---|---|")
    for label in ("car", "non-car", "ambiguous"):
        rs = by_label[label]
        tot = sum(r["n_instances"] for r in rs)
        mean = tot / len(rs) if rs else 0.0
        L.append(f"| {label} | {tot} | {mean:.2f} |")
    L.append("")

    L.append("## Mean Corrosion Bbox Area by Class (% of image)\n")
    L.append("| Class | Mean area % | Mean rust_frac |")
    L.append("|---|---|---|")
    for label in ("car", "non-car", "ambiguous"):
        rs = by_label[label]
        ma = float(np.mean([r["mean_area_pct"] for r in rs])) if rs else 0.0
        mr = float(np.mean([r["rust_frac"] for r in rs])) if rs else 0.0
        L.append(f"| {label} | {ma:.3f} | {mr:.3f} |")
    L.append("")

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    (Path(OUTPUT_DIR) / "corrosion_domain_audit.md").write_text("\n".join(L))

    for label, fname in (("car", "corrosion_car_images.txt"),
                         ("non-car", "corrosion_noncar_images.txt"),
                         ("ambiguous", "corrosion_ambiguous_images.txt")):
        with open(Path(OUTPUT_DIR) / fname, "w") as f:
            for r in sorted(by_label[label], key=lambda r: (r["split"], r["name"])):
                f.write(f"{r['split']}/{r['name']}\n")

    print(f"Found {len(by_label['car'])} car images, {len(by_label['non-car'])} non-car images, "
          f"{len(by_label['ambiguous'])} ambiguous out of {total} total corrosion images")
    print(f"Report: {OUTPUT_DIR}/corrosion_domain_audit.md")


if __name__ == "__main__":
    main()
