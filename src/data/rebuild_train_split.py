#!/usr/bin/env python3
"""
Rebuild the train split with out-of-domain (non-car) corrosion images removed.

Reads reports/corrosion_noncar_images.txt (from corrosion_domain_audit.py) and
writes a NEW dataset dir data/processed/yolo_seg_clean/ — the original
data/processed/yolo_seg/ is never modified.

Rules:
  - non-car image with ONLY corrosion annotations -> image + label removed
  - non-car image with corrosion AND other defects -> only corrosion lines removed
  - everything else (incl. ambiguous images) -> kept untouched
  - val/test -> symlinked as-is (evaluated via the car-only eval lists)

Layout of yolo_seg_clean/:
  images/train/<name>   relative symlink -> ../../yolo_seg/images/train/<name>
  labels/train/<name>   real file (corrosion lines stripped where applicable)
  images/val|test       relative symlinks to the original dirs
  labels/val|test       relative symlinks to the original dirs
  data.yaml             path: . with relative train/val/test

Run on server:
  conda activate car_defect
  python src/data/rebuild_train_split.py
"""

import os
import sys
from pathlib import Path

SRC = Path("data/processed/yolo_seg")
DST = Path("data/processed/yolo_seg_clean")
NONCAR_LIST = Path("reports/corrosion_noncar_images.txt")
CORROSION = "1"
CLASS_NAMES = {
    "0": "broken_lamp", "1": "corrosion", "2": "crack", "3": "dent",
    "4": "disjoint_part", "5": "glass_shatter", "6": "scratch",
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def read_noncar_train_entries():
    if not NONCAR_LIST.exists():
        sys.exit(f"ERROR: {NONCAR_LIST} not found — run src/analysis/corrosion_domain_audit.py first")
    entries = set()
    with open(NONCAR_LIST) as f:
        for line in f:
            line = line.strip()
            if line.startswith("train/"):
                entries.add(line.split("/", 1)[1])
    return entries


def count_instances(lines):
    counts = {}
    for l in lines:
        c = l.split()[0]
        counts[c] = counts.get(c, 0) + 1
    return counts


def main():
    print("=" * 80)
    print("REBUILD TRAIN SPLIT (remove non-car corrosion images)")
    print("=" * 80)

    if not SRC.is_dir():
        sys.exit(f"ERROR: source dataset not found: {SRC}")
    if DST.exists():
        sys.exit(f"ERROR: {DST} already exists — remove it first if you want to rebuild")

    drop = read_noncar_train_entries()
    print(f"[*] Non-car train images to process: {len(drop)}")

    src_train_img = SRC / "images" / "train"
    src_train_lbl = SRC / "labels" / "train"
    dst_train_img = DST / "images" / "train"
    dst_train_lbl = DST / "labels" / "train"
    dst_train_img.mkdir(parents=True)
    dst_train_lbl.mkdir(parents=True)

    before_imgs = 0
    after_imgs = 0
    before_inst, after_inst = {}, {}
    removed_images = 0
    stripped_labels = 0
    missing_in_source = 0

    for img_path in sorted(src_train_img.iterdir()):
        if not (img_path.is_file() and img_path.suffix.lower() in IMAGE_EXTS):
            continue
        before_imgs += 1
        lbl = src_train_lbl / (img_path.stem + ".txt")
        lines = []
        if lbl.exists():
            with open(lbl) as f:
                lines = [l.rstrip("\n") for l in f if l.strip()]
        for c, n in count_instances(lines).items():
            before_inst[c] = before_inst.get(c, 0) + n

        if img_path.name in drop:
            non_corr = [l for l in lines if l.split()[0] != CORROSION]
            if not non_corr:
                removed_images += 1
                continue  # image + label removed entirely
            lines = non_corr
            stripped_labels += 1

        after_imgs += 1
        for c, n in count_instances(lines).items():
            after_inst[c] = after_inst.get(c, 0) + n
        os.symlink(os.path.relpath(img_path, dst_train_img), dst_train_img / img_path.name)
        with open(dst_train_lbl / (img_path.stem + ".txt"), "w") as f:
            f.write("\n".join(lines) + "\n")

    for name in sorted(drop):
        if not (src_train_img / name).exists():
            missing_in_source += 1
            print(f"  [!] non-car list entry not found in source: {name}")

    # val/test: symlink as-is
    for split in ("val", "test"):
        (DST / "images" / split).symlink_to(os.path.relpath(SRC / "images" / split, DST / "images"))
        (DST / "labels" / split).symlink_to(os.path.relpath(SRC / "labels" / split, DST / "labels"))

    # data.yaml: keep the original names block, fix path to relative
    orig_yaml = (SRC / "data.yaml").read_text().splitlines()
    yaml_out = ["path: ." if l.startswith("path:") else l for l in orig_yaml]
    (DST / "data.yaml").write_text("\n".join(yaml_out) + "\n")

    # Validation 1: every label references an existing image
    bad = 0
    for lbl in sorted(dst_train_lbl.glob("*.txt")):
        if not any((dst_train_img / (lbl.stem + ext)).exists() for ext in IMAGE_EXTS):
            bad += 1
            print(f"  [!] label without image: {lbl.name}")
    if bad:
        sys.exit(f"ERROR: {bad} label(s) reference missing images — aborting")

    # Validation 2: non-corrosion class counts unchanged
    all_classes = sorted(set(before_inst) | set(after_inst))
    for c in all_classes:
        if c == CORROSION:
            continue
        b, a = before_inst.get(c, 0), after_inst.get(c, 0)
        if b != a:
            sys.exit(f"ERROR: {CLASS_NAMES.get(c, c)} instances changed {b} -> {a} — aborting")

    # Removal report
    print("\n" + "=" * 80)
    print("REMOVAL REPORT")
    print("=" * 80)
    print(f"Images:              before={before_imgs}  after={after_imgs}  "
          f"(removed={removed_images} fully, label-stripped={stripped_labels})")
    b_corr = before_inst.get(CORROSION, 0)
    a_corr = after_inst.get(CORROSION, 0)
    print(f"Corrosion instances: before={b_corr}  after={a_corr}  removed={b_corr - a_corr}")
    print("Instances per class (before -> after):")
    for c in all_classes:
        b, a = before_inst.get(c, 0), after_inst.get(c, 0)
        mark = "" if (c == CORROSION or b == a) else "  <-- UNEXPECTED CHANGE"
        print(f"  {CLASS_NAMES.get(c, c):<15} {b:>6} -> {a:>6}{mark}")
    print("Validation:")
    print("  [OK] all labels reference existing images")
    print("  [OK] non-corrosion class counts unchanged")
    print(f"\nNew dataset: {DST}/ (original {SRC}/ untouched)")
    print(f"Train with:  data={DST}/data.yaml")


if __name__ == "__main__":
    main()
