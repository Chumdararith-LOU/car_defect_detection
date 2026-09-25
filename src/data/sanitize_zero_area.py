#!/usr/bin/env python3
"""Strip degenerate GT instances from a YOLO-seg dataset.

An instance line is dropped ONLY when it is truly degenerate:
  - malformed line (not a valid YOLO-seg polygon)
  - bbox width == 0 AND bbox height == 0
  - fewer than --min-points distinct vertices with zero extent
    (all points identical)

Low-vertex polygons with nonzero extent (e.g. 2-point line segments) are
valid thin scratch/corrosion masks and are KEPT.

Label files that become empty are kept (the image remains a background sample).
Idempotent: a second pass drops nothing.

Usage:
    python src/data/sanitize_zero_area.py --root data/processed/yolo_seg_hn999 --dry-run --report reports/zero_area_report_hn999.json
    python src/data/sanitize_zero_area.py --root data/processed/yolo_seg_hn999 --inplace --report reports/zero_area_report_hn999.json
"""

import argparse
import json
from pathlib import Path


def is_degenerate(parts, min_points=3):
    """parts: whitespace-split YOLO-seg line (cls cx cy w h + mask points)."""
    if len(parts) < 7 or (len(parts) - 5) % 2 != 0:
        return True  # malformed -> treat as droppable garbage
    w, h = float(parts[3]), float(parts[4])
    if w == 0.0 and h == 0.0:
        return True
    pts = [float(v) for v in parts[5:]]
    xs, ys = pts[0::2], pts[1::2]
    if len(set(zip(xs, ys))) < min_points:
        # keep only if the segment has nonzero extent
        return not (max(xs) - min(xs) > 0.0 or max(ys) - min(ys) > 0.0)
    return False


def process_split(label_dir, inplace, min_points=3):
    stats = {"scanned": 0, "dropped": 0, "kept": 0, "files_emptied": 0}
    for lbl in sorted(label_dir.glob("*.txt")):
        lines = lbl.read_text().splitlines()
        kept_lines = []
        for line in lines:
            if not line.strip():
                continue
            stats["scanned"] += 1
            if is_degenerate(line.split(), min_points):
                stats["dropped"] += 1
            else:
                kept_lines.append(line)
                stats["kept"] += 1
        n_orig = sum(1 for l in lines if l.strip())
        if inplace and len(kept_lines) != n_orig:
            lbl.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""))
        if n_orig and not kept_lines:
            stats["files_emptied"] += 1
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="YOLO-seg dataset dir (images/ + labels/)")
    parser.add_argument("--inplace", action="store_true", help="rewrite label files (default: dry run)")
    parser.add_argument("--dry-run", action="store_true", help="write report only, no changes")
    parser.add_argument("--report", type=Path, required=True, help="output JSON report path")
    parser.add_argument("--min-points", type=int, default=3,
                        help="polygons with fewer distinct vertices are kept only if they have nonzero extent")
    args = parser.parse_args()

    if args.inplace and args.dry_run:
        raise SystemExit("--inplace and --dry-run are mutually exclusive")

    labels_root = args.root / "labels"
    if not labels_root.is_dir():
        raise SystemExit(f"labels dir not found: {labels_root}")

    report = {}
    for split_dir in sorted(p for p in labels_root.iterdir() if p.is_dir()):
        report[split_dir.name] = process_split(split_dir, inplace=args.inplace, min_points=args.min_points)
        print(f"{split_dir.name}: {report[split_dir.name]}")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    mode = "INPLACE" if args.inplace else "DRY-RUN"
    print(f"[{mode}] report written to {args.report}")


if __name__ == "__main__":
    main()
