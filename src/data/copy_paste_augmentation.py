#!/usr/bin/env python3
"""
Targeted Copy-Paste augmentation for weak classes.

Extracts instances (mask + pixels) of broken_lamp / glass_shatter / crack /
scratch from yolo_seg_clean train images and pastes them at random positions
on random train images, adding enough instances to bring each target class to
at least 50% of the median class count. The original dataset is never
modified.

Run on server:
  conda activate car_defect
  python src/data/copy_paste_augmentation.py

Outputs:
  data/processed/yolo_seg_clean_augmented/
    images/train/  originals as relative symlinks + cp_*.jpg composites
    labels/train/  copies of original labels + labels for composites
    images/val|test, labels/val|test  relative symlinks to yolo_seg_clean
    data.yaml      path: . with relative train/val/test
  reports/copy_paste_augmentation_report.md
"""

import os
import random
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

SRC = Path("data/processed/yolo_seg_clean")
DST = Path("data/processed/yolo_seg_clean_augmented")
REPORT = Path("reports/copy_paste_augmentation_report.md")
CLASS_NAMES = {
    0: "broken_lamp", 1: "corrosion", 2: "crack", 3: "dent",
    4: "disjoint_part", 5: "glass_shatter", 6: "scratch",
}
CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}
TARGET_CLASSES = ["broken_lamp", "glass_shatter", "crack", "scratch"]
MEDIAN_FRACTION = 0.5
SEED = 42
MIN_INSTANCE_AREA_PX = 16
MAX_TARGET_TRIES = 10
MAX_POS_TRIES = 10
OCCLUSION_LIMIT = 0.9
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def list_images(d):
    return sorted(p.name for p in Path(d).iterdir()
                  if p.is_file() and p.suffix.lower() in IMAGE_EXTS)


def read_lines(path):
    if not path.exists():
        return []
    with open(path) as f:
        return [l.rstrip("\n") for l in f if l.strip()]


def parse_line(line):
    """YOLO seg line -> (class_id, [(x, y), ...]) or None."""
    parts = line.split()
    if len(parts) < 7:
        return None
    coords = [float(x) for x in parts[1:]]
    if len(coords) % 2:
        coords = coords[:-1]
    if len(coords) < 6:
        return None
    return int(parts[0]), list(zip(coords[0::2], coords[1::2]))


def bbox_of(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def count_instances(labels_dir):
    counts = defaultdict(int)
    for lf in Path(labels_dir).glob("*.txt"):
        for line in read_lines(lf):
            parsed = parse_line(line)
            if parsed:
                counts[parsed[0]] += 1
    return dict(counts)


def build_pool(labels_dir, class_id):
    """image_stem -> [polygons] for a class (degenerate instances skipped)."""
    pool = defaultdict(list)
    for lf in Path(labels_dir).glob("*.txt"):
        for line in read_lines(lf):
            parsed = parse_line(line)
            if not parsed or parsed[0] != class_id:
                continue
            poly = parsed[1]
            x1, y1, x2, y2 = bbox_of(poly)
            if (x2 - x1) * (y2 - y1) <= 0:
                continue
            pool[lf.stem].append(poly)
    return pool


def rasterize(poly_norm, w, h):
    pts = np.array([(x * w, y * h) for x, y in poly_norm], dtype=np.int32)
    m = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def coverage(paste_bbox, gt_bbox):
    """Fraction of gt_bbox covered by paste_bbox."""
    x1, y1 = max(paste_bbox[0], gt_bbox[0]), max(paste_bbox[1], gt_bbox[1])
    x2, y2 = min(paste_bbox[2], gt_bbox[2]), min(paste_bbox[3], gt_bbox[3])
    if x1 >= x2 or y1 >= y2:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    gt_area = (gt_bbox[2] - gt_bbox[0]) * (gt_bbox[3] - gt_bbox[1])
    return inter / gt_area if gt_area > 0 else 0.0


def main():
    random.seed(SEED)
    np.random.seed(SEED)
    print("=" * 80)
    print("COPY-PASTE AUGMENTATION")
    print("=" * 80)

    src_img_dir = SRC / "images" / "train"
    src_lbl_dir = SRC / "labels" / "train"
    if not src_img_dir.is_dir():
        sys.exit(f"ERROR: {src_img_dir} not found — run rebuild_train_split.py first")
    if DST.exists():
        sys.exit(f"ERROR: {DST} already exists — remove it first if you want to rebuild")

    # 1. Class distribution
    before = count_instances(src_lbl_dir)
    print("[*] Instance distribution (before):")
    below_median = []
    median = float(np.median([before.get(c, 0) for c in CLASS_NAMES]))
    for cid in sorted(CLASS_NAMES):
        n = before.get(cid, 0)
        flag = "  <-- below median" if n < median else ""
        if n < median:
            below_median.append(CLASS_NAMES[cid])
        print(f"    {CLASS_NAMES[cid]:<15} {n}{flag}")
    target_count = int(np.ceil(MEDIAN_FRACTION * median))
    need = {c: max(0, target_count - before.get(CLASS_IDS[c], 0)) for c in TARGET_CLASSES}
    print(f"[*] Median class count: {median:.0f} | augmentation target: >= {target_count} per class")
    for c in TARGET_CLASSES:
        print(f"    {c:<15} need +{need[c]}")

    all_images = list_images(src_img_dir)
    if not all_images:
        sys.exit("ERROR: no train images found")
    stem_to_name = {Path(n).stem: n for n in all_images}

    # 2. Dataset skeleton: originals symlinked (images) + copied (labels)
    dst_img_dir = DST / "images" / "train"
    dst_lbl_dir = DST / "labels" / "train"
    dst_img_dir.mkdir(parents=True)
    dst_lbl_dir.mkdir(parents=True)
    print(f"[*] Linking {len(all_images)} original images...")
    for name in all_images:
        os.symlink(os.path.relpath(src_img_dir / name, dst_img_dir), dst_img_dir / name)
        src_lbl = src_lbl_dir / (Path(name).stem + ".txt")
        if src_lbl.exists():
            shutil.copyfile(src_lbl, dst_lbl_dir / (Path(name).stem + ".txt"))

    # 3. Copy-paste
    placed = {c: 0 for c in TARGET_CLASSES}
    failures = 0
    samples = {c: [] for c in TARGET_CLASSES}
    counter = {c: 0 for c in TARGET_CLASSES}

    def place_instance(class_name, cid, src_name, poly):
        """Paste one instance onto a random target. Returns new image name or None."""
        src_img = cv2.imread(str(src_img_dir / stem_to_name[src_name]))
        if src_img is None:
            return None
        sh, sw = src_img.shape[:2]
        mask = rasterize(poly, sw, sh)
        if mask.sum() < MIN_INSTANCE_AREA_PX:
            return None
        ys, xs = np.where(mask)
        y1, y2, x1, x2 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
        crop, mask_crop = src_img[y1:y2, x1:x2], mask[y1:y2, x1:x2]
        ih, iw = crop.shape[:2]
        for _ in range(MAX_TARGET_TRIES):
            tgt_name = random.choice(all_images)
            tgt_img = cv2.imread(str(src_img_dir / tgt_name))
            if tgt_img is None:
                continue
            H, W = tgt_img.shape[:2]
            if iw > W or ih > H:
                continue
            tgt_lines = read_lines(src_lbl_dir / (Path(tgt_name).stem + ".txt"))
            tgt_bboxes = []
            for line in tgt_lines:
                parsed = parse_line(line)
                if parsed:
                    bx1, by1, bx2, by2 = bbox_of(parsed[1])
                    tgt_bboxes.append((bx1 * W, by1 * H, bx2 * W, by2 * H))
            for _ in range(MAX_POS_TRIES):
                dx = random.randint(0, W - iw)
                dy = random.randint(0, H - ih)
                paste = (dx, dy, dx + iw, dy + ih)
                if any(coverage(paste, gb) > OCCLUSION_LIMIT for gb in tgt_bboxes):
                    continue  # would fully occlude an existing instance
                out = tgt_img.copy()
                out[dy:dy + ih, dx:dx + iw][mask_crop] = crop[mask_crop]
                # polygon in crop-local pixels, then translated to target-normalized
                new_poly = [(((px * sw - x1) + dx) / W, ((py * sh - y1) + dy) / H)
                            for px, py in poly]
                line = str(cid) + " " + " ".join(f"{x:.6f} {y:.6f}" for x, y in new_poly)
                counter[class_name] += 1
                out_name = f"cp_{class_name}_{counter[class_name]:05d}.jpg"
                cv2.imwrite(str(dst_img_dir / out_name), out, [cv2.IMWRITE_JPEG_QUALITY, 95])
                with open(dst_lbl_dir / (out_name[:-4] + ".txt"), "w") as f:
                    f.write("\n".join(tgt_lines + [line]) + "\n")
                return out_name
        return None

    for class_name in TARGET_CLASSES:
        if need[class_name] == 0:
            continue
        cid = CLASS_IDS[class_name]
        pool = build_pool(src_lbl_dir, cid)
        pool_images = [s for s in pool if s in stem_to_name]
        if not pool_images:
            sys.exit(f"ERROR: no source instances found for {class_name}")
        n_inst = sum(len(v) for v in pool.values())
        print(f"[*] {class_name}: {n_inst} source instances in {len(pool_images)} images, "
              f"placing {need[class_name]}...")
        attempts = 0
        while placed[class_name] < need[class_name] and attempts < need[class_name] * 5:
            attempts += 1
            src_name = random.choice(pool_images)
            poly = random.choice(pool[src_name])
            out_name = place_instance(class_name, cid, src_name, poly)
            if out_name:
                placed[class_name] += 1
                if len(samples[class_name]) < 5:
                    samples[class_name].append(str(dst_img_dir / out_name))
            else:
                failures += 1
        if placed[class_name] < need[class_name]:
            print(f"  [!] {class_name}: placed {placed[class_name]}/{need[class_name]} "
                  f"after {attempts} attempts")

    # 4. val/test + data.yaml
    for split in ("val", "test"):
        (DST / "images" / split).symlink_to(os.path.relpath(SRC / "images" / split, DST / "images"))
        (DST / "labels" / split).symlink_to(os.path.relpath(SRC / "labels" / split, DST / "labels"))
    yaml_out = ["path: ." if l.startswith("path:") else l
                for l in (SRC / "data.yaml").read_text().splitlines()]
    (DST / "data.yaml").write_text("\n".join(yaml_out) + "\n")

    # 5. Validation
    after = count_instances(dst_lbl_dir)
    bad = sum(1 for lf in dst_lbl_dir.glob("*.txt")
              if not any((dst_img_dir / (lf.stem + ext)).exists() for ext in IMAGE_EXTS))
    if bad:
        sys.exit(f"ERROR: {bad} label(s) reference missing images — aborting")
    zero = [CLASS_NAMES[c] for c in CLASS_NAMES if after.get(c, 0) == 0]
    if zero:
        sys.exit(f"ERROR: classes with 0 instances after augmentation: {zero}")

    total_placed = sum(placed.values())
    print("\n" + "=" * 80)
    print("AUGMENTATION REPORT")
    print("=" * 80)
    print(f"Total images: before={len(all_images)}  after={len(all_images) + total_placed} "
          f"(+{total_placed} composites, {failures} failed placements)")
    print("Instances per class (before -> after):")
    for cid in sorted(CLASS_NAMES):
        b, a = before.get(cid, 0), after.get(cid, 0)
        mark = f"  (+{a - b} augmented)" if a > b else ""
        print(f"  {CLASS_NAMES[cid]:<15} {b:>6} -> {a:>6}{mark}")

    # 6. Report file
    L = []
    L.append("# Copy-Paste Augmentation Report\n")
    L.append(f"- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L.append(f"- **Source:** `{SRC}/` | **Output:** `{DST}/`")
    L.append(f"- **Config:** seed={SEED}, target = {MEDIAN_FRACTION:.0%} of median class count "
             f"({target_count}), min instance area {MIN_INSTANCE_AREA_PX}px, "
             f"occlusion limit {OCCLUSION_LIMIT:.0%}")
    L.append(f"- **Total images:** {len(all_images)} -> {len(all_images) + total_placed} "
             f"(+{total_placed} composites, {failures} failed placements)\n")
    L.append("## Instance Distribution (before -> after)\n")
    L.append("| Class | Before | After | Δ |")
    L.append("|---|---|---|---|")
    for cid in sorted(CLASS_NAMES):
        b, a = before.get(cid, 0), after.get(cid, 0)
        L.append(f"| {CLASS_NAMES[cid]} | {b} | {a} | {a - b} |")
    L.append("\nNote: Δ for non-target classes comes from target images' existing annotations "
             "being carried into composites; actual pasted-instance counts are in the table below.")
    L.append("")
    L.append("## Augmented Images per Target Class\n")
    L.append("| Class | Placed | Sample paths |")
    L.append("|---|---|---|")
    for c in TARGET_CLASSES:
        s = "<br>".join(f"`{p}`" for p in samples[c]) or "—"
        L.append(f"| {c} | {placed[c]} | {s} |")
    L.append("")
    L.append("Validation: [OK] all labels reference existing images, [OK] no class has 0 instances.")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L))
    print(f"\nReport: {REPORT}")
    print("COPY-PASTE AUGMENTATION COMPLETE")


if __name__ == "__main__":
    main()
