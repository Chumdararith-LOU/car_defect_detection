#!/usr/bin/env python3
"""Report the largest / most unusual images (by pixel count and aspect ratio) in
a set of paths, without touching the GPU or importing torch/ultralytics at all.

Usage:
    python inspect_image_sizes.py --noncar-list <path/to/list.txt> --project-root .
    python inspect_image_sizes.py /path/to/some/dir
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", help="explicit image files or directories to scan")
    ap.add_argument("--noncar-list", default=None,
                     help="same --noncar-list txt file you pass to eval_car_only.py")
    ap.add_argument("--project-root", default=".",
                     help="repo root; used to resolve --noncar-list entries the same way eval_car_only.py does")
    ap.add_argument("--top", type=int, default=15, help="how many largest images to print")
    args = ap.parse_args()

    root = Path(args.project_root)
    files = []
    for p in args.paths:
        p = Path(p)
        if p.is_dir():
            files.extend(sorted(q for q in p.iterdir() if q.suffix.lower() in IMG_EXTS))
        else:
            files.append(p)
    if args.noncar_list:
        names = [l.strip() for l in Path(args.noncar_list).read_text().splitlines() if l.strip()]
        noncar_dir = root / "data/processed/yolo_seg/images/test"
        files.extend(noncar_dir / n for n in names)

    rows = []
    for f in files:
        if not f.exists():
            print(f"[missing] {f}", file=sys.stderr)
            continue
        try:
            with Image.open(f) as im:
                w, h = im.size
                mode = im.mode
        except Exception as e:
            print(f"[unreadable] {f}: {e}", file=sys.stderr)
            continue
        aspect = max(w, h) / max(1, min(w, h))
        rows.append((w * h, w, h, aspect, mode, str(f)))

    if not rows:
        print("No readable images found.")
        return

    rows.sort(reverse=True)
    print(f"Scanned {len(rows)} images.\n")
    print(f"{'megapixels':>10} {'w':>6} {'h':>6} {'aspect':>7} {'mode':>6}  path")
    for mp, w, h, aspect, mode, f in rows[: args.top]:
        print(f"{mp/1e6:10.2f} {w:6} {h:6} {aspect:7.2f} {mode:>6}  {f}")

    weird = [r for r in rows if r[3] > 4.0 or r[4] not in ("RGB", "L")]
    if weird:
        print("\nFlagged (aspect ratio > 4:1, or non-RGB/L mode):")
        for mp, w, h, aspect, mode, f in weird:
            print(f"  {w}x{h} aspect={aspect:.1f} mode={mode}  {f}")


if __name__ == "__main__":
    main()
