#!/usr/bin/env python3
"""Unify raw car-defect COCO datasets into the locked 7-class taxonomy,
deduplicate images by MD5 (keeping the copy with the most annotations),
and emit train/val/test COCO JSONs plus a unified image directory."""

import argparse
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from tqdm import tqdm

UNIFIED_CLASSES = [
    "broken_lamp",
    "corrosion",
    "crack",
    "dent",
    "disjoint_part",
    "glass_shatter",
    "scratch",
]

CLASS_MAPPING = {
    "dent": "dent",
    "ding": "dent",
    "deform": "dent",
    "scratch": "scratch",
    "scratch_hairline": "scratch",
    "scratch_gouge": "scratch",
    "crack": "crack",
    "crack-4VtJ": "crack",
    "glass shatter": "glass_shatter",
    "glass_shatter": "glass_shatter",
    "lamp broken": "broken_lamp",
    "broken_lamp": "broken_lamp",
    "corrosion": "corrosion",
    "rust": "corrosion",
    "Rust": "corrosion",
    "copper corrosion": "corrosion",
    "corroded-part": "corrosion",
    "iron rust": "corrosion",
    "mild-corrosion": "corrosion",
    "moderate-corrosion": "corrosion",
    "severe-corrosion": "corrosion",
    "broken_components": "disjoint_part",
    "disjoint_part": "disjoint_part",
}

# 'car' only denotes corroded bodywork inside the Rust Detection export
SOURCE_CLASS_OVERRIDES = {
    "Rust Detection.v1i.coco": {"car": "corrosion"},
}

# documented duplicate of CarDD_release/CarDD_COCO/train2017 (data/raw/DATASET_AUDIT.md)
EXCLUDED_DATASETS = {"car-damage-detection.v1i.coco"}

PREFIX_TO_SPLIT = {"train": "train", "val": "val", "test": "test"}


def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_coco(json_path):
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"    [warn] cannot read {json_path}: {exc}")
        return None
    if not isinstance(data, dict) or "images" not in data or "annotations" not in data:
        print(f"    [warn] not a COCO instances file: {json_path}")
        return None
    return data


def discover_sources(raw_dir):
    sources = []
    cardd = raw_dir / "CarDD_release" / "CarDD_COCO"
    for split, subdir in (
        ("train", "train2017"),
        ("val", "val2017"),
        ("test", "test2017"),
    ):
        ann = cardd / "annotations" / f"instances_{subdir}.json"
        if ann.exists():
            sources.append(
                {
                    "name": "CarDD_COCO",
                    "json": ann,
                    "images_dir": cardd / subdir,
                    "split": split,
                }
            )

    for folder in ("Car defect 2000 new", "Car defect 2200"):
        ann = raw_dir / folder / "annotations" / "instances_default.json"
        if ann.exists():
            sources.append(
                {
                    "name": folder,
                    "json": ann,
                    "images_dir": raw_dir / folder / "images" / "default",
                    "split": None,
                }
            )

    roboflow = raw_dir / "Roboflow"
    if roboflow.is_dir():
        for export in sorted(roboflow.iterdir()):
            if not export.is_dir() or export.name in EXCLUDED_DATASETS:
                continue
            for split, subdir in (
                ("train", "train"),
                ("val", "valid"),
                ("test", "test"),
            ):
                ann = export / subdir / "_annotations.coco.json"
                if ann.exists():
                    sources.append(
                        {
                            "name": export.name,
                            "json": ann,
                            "images_dir": export / subdir,
                            "split": split,
                        }
                    )
    return sources


def split_from_filename(file_name):
    parts = file_name.split("_")
    if len(parts) >= 2 and parts[0] in ("cardd", "rust"):
        return PREFIX_TO_SPLIT.get(parts[1], "train")
    return "train"


def process_source(src):
    stats = Counter()
    data = load_coco(src["json"])
    if data is None:
        return [], stats

    overrides = SOURCE_CLASS_OVERRIDES.get(src["name"], {})
    cat_to_unified = {}
    for cat in data.get("categories", []):
        target = overrides.get(cat["name"], CLASS_MAPPING.get(cat["name"]))
        if target in UNIFIED_CLASSES:
            cat_to_unified[cat["id"]] = UNIFIED_CLASSES.index(target) + 1

    anns_by_image = defaultdict(list)
    for ann in data.get("annotations", []):
        unified_id = cat_to_unified.get(ann.get("category_id"))
        if unified_id is None:
            stats["anns_dropped_unmapped"] += 1
            continue
        anns_by_image[ann.get("image_id")].append(
            {
                "category_id": unified_id,
                "segmentation": ann.get("segmentation", []),
                "area": ann.get("area", 0),
                "bbox": ann.get("bbox", []),
                "iscrowd": ann.get("iscrowd", 0),
            }
        )

    entries = []
    for im in data.get("images", []):
        kept = anns_by_image.get(im.get("id"))
        if not kept:
            stats["images_without_kept_anns"] += 1
            continue
        path = src["images_dir"] / im.get("file_name", "")
        if not path.is_file():
            stats["images_missing_on_disk"] += 1
            continue
        entries.append(
            {
                "source": src["name"],
                "path": path,
                "split": src["split"] or split_from_filename(im.get("file_name", "")),
                "width": im.get("width"),
                "height": im.get("height"),
                "annotations": kept,
            }
        )
    stats["images_kept"] = len(entries)
    return entries, stats


def deduplicate(entries):
    by_hash = {}
    cross_split = 0
    for entry in tqdm(entries, desc="Hashing images", unit="img"):
        digest = md5_file(entry["path"])
        entry["md5"] = digest
        current = by_hash.get(digest)
        if current is None:
            by_hash[digest] = entry
            continue
        if current["split"] != entry["split"]:
            cross_split += 1
        if len(entry["annotations"]) > len(current["annotations"]):
            by_hash[digest] = entry
    if cross_split:
        print(
            f"  [warn] {cross_split} duplicate image(s) span multiple splits; the copy with most annotations won"
        )
    return list(by_hash.values())


def slug(name):
    return "".join(ch if ch.isalnum() or ch in "-." else "_" for ch in name)


def write_split(split, entries, ann_dir, img_root, copy_images):
    split_dir = img_root / split
    if split_dir.exists():
        shutil.rmtree(split_dir)
    split_dir.mkdir(parents=True)

    categories = [{"id": i + 1, "name": name} for i, name in enumerate(UNIFIED_CLASSES)]
    images, annotations = [], []
    taken_names = set()
    for new_id, entry in enumerate(
        sorted(entries, key=lambda e: str(e["path"])), start=1
    ):
        file_name = entry["path"].name
        if file_name in taken_names:
            file_name = f"{slug(entry['source'])}__{file_name}"
        taken_names.add(file_name)
        if copy_images:
            shutil.copy2(entry["path"], split_dir / file_name)
        else:
            (split_dir / file_name).symlink_to(entry["path"].resolve())
        images.append(
            {
                "id": new_id,
                "file_name": file_name,
                "width": entry["width"],
                "height": entry["height"],
            }
        )
        for ann in entry["annotations"]:
            annotations.append(
                {
                    "id": len(annotations) + 1,
                    "image_id": new_id,
                    "category_id": ann["category_id"],
                    "segmentation": ann["segmentation"],
                    "area": ann["area"],
                    "bbox": ann["bbox"],
                    "iscrowd": ann["iscrowd"],
                }
            )

    with open(ann_dir / f"{split}.json", "w") as f:
        json.dump(
            {"images": images, "annotations": annotations, "categories": categories}, f
        )

    class_counts = Counter(a["category_id"] for a in annotations)
    per_class = ", ".join(
        f"{UNIFIED_CLASSES[cid - 1]}={n}" for cid, n in sorted(class_counts.items())
    )
    print(
        f"  {split:<5} images={len(images):>6}  anns={len(annotations):>7}  [{per_class}]"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Unify and deduplicate raw COCO defect datasets into the 7-class taxonomy"
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--copy-images", action="store_true", help="copy images instead of symlinking"
    )
    args = parser.parse_args()

    ann_dir = args.output_dir / "annotations"
    img_root = args.output_dir / "images"
    ann_dir.mkdir(parents=True, exist_ok=True)

    sources = discover_sources(args.raw_dir)
    if not sources:
        raise SystemExit(f"No COCO sources found under {args.raw_dir}")

    all_entries = []
    totals = Counter()
    for src in sources:
        entries, stats = process_source(src)
        all_entries.extend(entries)
        totals.update(stats)
        print(
            f"[{src['name']}] {src['json'].name}: kept={stats['images_kept']} "
            f"unmapped_anns_dropped={stats['anns_dropped_unmapped']} "
            f"images_no_kept_anns={stats['images_without_kept_anns']} "
            f"images_missing={stats['images_missing_on_disk']}"
        )

    print(f"Candidate images: {len(all_entries)}")
    kept = deduplicate(all_entries)
    print(
        f"Unique images after MD5 dedup: {len(kept)} (removed {len(all_entries) - len(kept)} duplicates)"
    )

    by_split = defaultdict(list)
    for entry in kept:
        by_split[entry["split"]].append(entry)
    for split in ("train", "val", "test"):
        write_split(split, by_split.get(split, []), ann_dir, img_root, args.copy_images)


if __name__ == "__main__":
    main()
