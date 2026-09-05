import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "processed" / "yolo_seg_clean"
DST = ROOT / "data" / "processed" / "yolo_seg_subset"
FRACTION = 0.2
SEED = 42

YAML = """path: .
train: images/train
val: images/val
names:
  0: broken_lamp
  1: corrosion
  2: crack
  3: dent
  4: disjoint_part
  5: glass_shatter
  6: scratch
"""


def main():
    label_dir = SRC / "labels" / "train"
    per_image = {}
    for path in sorted(label_dir.glob("*.txt")):
        classes = Counter()
        for line in path.read_text().splitlines():
            if line.split():
                classes[int(line.split()[0])] += 1
        per_image[path] = classes

    # total instances per class across the whole train set
    totals = Counter()
    for classes in per_image.values():
        totals.update(classes)

    # group each image by its rarest class (fewest total instances);
    # images with no labels go into a "background" group keyed by -1
    groups = {}
    for path, classes in per_image.items():
        if classes:
            key = min(classes, key=lambda c: (totals[c], c))
        else:
            key = -1
        groups.setdefault(key, []).append(path)

    rng = random.Random(SEED)
    selected = []
    for paths in groups.values():
        rng.shuffle(paths)
        n = max(1, round(len(paths) * FRACTION))
        selected.extend(paths[:n])

    # clean output
    import shutil
    if DST.exists():
        shutil.rmtree(DST)
    (DST / "labels" / "train").mkdir(parents=True)
    (DST / "images" / "train").mkdir(parents=True)

    subset_counts = Counter()
    for path in selected:
        shutil.copy(path, DST / "labels" / "train" / path.name)
        stem = path.stem
        imgs = list((SRC / "images" / "train").glob(f"{stem}.*"))
        if imgs:
            (DST / "images" / "train" / imgs[0].name).symlink_to(imgs[0])
        subset_counts.update(per_image[path])

    # full val set via directory symlinks
    (DST / "images" / "val").symlink_to(SRC / "images" / "val")
    (DST / "labels" / "val").symlink_to(SRC / "labels" / "val")

    (DST / "data.yaml").write_text(YAML)

    names = ["broken_lamp", "corrosion", "crack", "dent", "disjoint_part",
             "glass_shatter", "scratch"]
    print(f"Selected {len(selected)} / {len(per_image)} train images "
          f"({len(selected)/len(per_image):.1%})")
    print(f"\n| Class | Original | Subset | % |")
    print(f"|---|---:|---:|---:|")
    for cid, name in enumerate(names):
        print(f"| {name} | {totals[cid]} | {subset_counts[cid]} | "
              f"{subset_counts[cid]/totals[cid]*100 if totals[cid] else 0:.1f}% |")


if __name__ == "__main__":
    main()
