import shutil
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "processed" / "yolo_seg"
DST = ROOT / "data" / "processed" / "yolo_seg_clean"
SPLITS = ["train", "val", "test"]
MIN_DIM = 0.001


def clean_line(parts):
    try:
        coords = [float(v) for v in parts[1:]]
    except ValueError:
        return None
    if len(coords) < 6:
        return None
    xs = coords[0::2]
    ys = coords[1::2]
    if max(xs) - min(xs) <= MIN_DIM or max(ys) - min(ys) <= MIN_DIM:
        return None
    return True


def main():
    names = yaml.safe_load((SRC / "data.yaml").read_text())["names"]
    removed_by_class = defaultdict(int)
    original_total = clean_total = 0

    for split in SPLITS:
        out_dir = DST / "labels" / split
        out_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted((SRC / "labels" / split).glob("*.txt")):
            kept = []
            for line in path.read_text().splitlines():
                parts = line.split()
                if not parts:
                    continue
                original_total += 1
                if clean_line(parts):
                    kept.append(line)
                    clean_total += 1
                else:
                    cid = int(parts[0]) if parts[0].isdigit() else -1
                    removed_by_class[cid] += 1
            (out_dir / path.name).write_text("\n".join(kept) + ("\n" if kept else ""))

    # symlink images (3.4G — no need to duplicate); copy data.yaml unchanged
    # (relative paths still resolve: YOLO derives label paths from image paths)
    img_dir = DST / "images"
    img_dir.mkdir(exist_ok=True)
    for split in SPLITS:
        link = img_dir / split
        if not link.exists():
            link.symlink_to(SRC / "images" / split)
    shutil.copy(SRC / "data.yaml", DST / "data.yaml")

    print(f"Removed {original_total - clean_total} malformed boxes. "
          f"Original total: {original_total}. Cleaned total: {clean_total}.")
    print("\nRemoved per class:")
    for cid in sorted(removed_by_class):
        label = names.get(cid, f"unknown({cid})")
        print(f"  {label}: {removed_by_class[cid]}")


if __name__ == "__main__":
    main()
