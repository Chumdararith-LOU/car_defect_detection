#!/usr/bin/env python3
"""Build the clean-negative (undamaged car) pool for Stage 2 hard-negative
injection.

Scans known clean-car sources, MD5-deduplicates them, leak-checks against
the locked YOLO-seg dataset, splits into an injectable train pool and a
held-out evaluation slice (for the clean-image false-positive metric), and
writes empty YOLO label files.

Output layout (relative to repo root):

    data/processed/clean_cars/
        images/clean_train/     injectable into training
        images/clean_eval/      held-out, FP-rate metric only
        labels/clean_train/     one empty .txt per image
        labels/clean_eval/
        manifest.json           per-file provenance + stats

Usage:
    python src/data/build_clean_pool.py
    python src/data/build_clean_pool.py --eval-fraction 0.15
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

# Clean sources. BMW screenshot folder (undamaged_car_images) intentionally
# skipped: dealer-listing screenshots with UI chrome (see clean_car_dataset.md).
CLEAN_SOURCES = [
    ("data1a-train", Path("data/raw/data1a/training/01-whole")),
    ("data1a-val", Path("data/raw/data1a/validation/01-whole")),
]

# Locked dataset used for the leakage check.
YOLO_SEG_IMAGE_DIRS = [
    Path("data/processed/yolo_seg/images/train"),
    Path("data/processed/yolo_seg/images/val"),
    Path("data/processed/yolo_seg/images/test"),
]

OUTPUT_DIR = Path("data/processed/clean_cars")


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_source_images():
    for tag, rel_dir in CLEAN_SOURCES:
        src_dir = REPO_ROOT / rel_dir
        if not src_dir.is_dir():
            print(f"[warn] source missing, skipped: {rel_dir}")
            continue
        files = sorted(
            p for p in src_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS
        )
        print(f"[scan] {rel_dir}: {len(files)} images")
        for p in files:
            yield tag, rel_dir, p


def hash_locked_dataset():
    hashes = set()
    for rel_dir in YOLO_SEG_IMAGE_DIRS:
        d = REPO_ROOT / rel_dir
        if not d.is_dir():
            print(f"[warn] dataset dir missing, skipped: {rel_dir}")
            continue
        for p in d.iterdir():
            if p.suffix.lower() in IMAGE_EXTS:
                hashes.add(md5_of(p))
    print(f"[leak-check] locked dataset images hashed: {len(hashes)}")
    return hashes


def deterministic_split(new_name: str, eval_fraction: float) -> str:
    """Stable train/eval assignment, independent of file order or machine."""
    bucket = int(hashlib.md5(new_name.encode()).hexdigest(), 16) % 1000
    return "clean_eval" if bucket < eval_fraction * 1000 else "clean_train"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-fraction",
        type=float,
        default=0.15,
        help="fraction of the pool held out for the clean-image FP metric",
    )
    args = parser.parse_args()

    out = REPO_ROOT / OUTPUT_DIR
    if out.exists():
        shutil.rmtree(out)  # idempotent rebuild, same pattern as phase1 Cell 7
    dirs = {}
    for split in ("clean_train", "clean_eval"):
        dirs[split] = {
            "images": out / "images" / split,
            "labels": out / "labels" / split,
        }
        dirs[split]["images"].mkdir(parents=True)
        dirs[split]["labels"].mkdir(parents=True)

    locked_hashes = hash_locked_dataset()

    seen, records = {}, []
    n_dup = n_leak = 0
    for tag, rel_dir, p in iter_source_images():
        h = md5_of(p)
        new_name = f"{tag}-{p.name}"
        if h in seen:
            n_dup += 1
            continue
        if h in locked_hashes:
            n_leak += 1
            print(f"[leak] dropped (matches locked dataset): {rel_dir / p.name}")
            continue
        seen[h] = new_name
        split = deterministic_split(new_name, args.eval_fraction)
        shutil.copy2(p, dirs[split]["images"] / new_name)
        (dirs[split]["labels"] / (Path(new_name).stem + ".txt")).touch()
        records.append(
            {
                "original": str(rel_dir / p.name),
                "md5": h,
                "new_name": new_name,
                "split": split,
            }
        )

    manifest = {
        "generated_by": "src/data/build_clean_pool.py",
        "eval_fraction": args.eval_fraction,
        "sources": [str(rel) for _, rel in CLEAN_SOURCES],
        "total_scanned": len(records) + n_dup + n_leak,
        "duplicates_dropped": n_dup,
        "leaks_dropped": n_leak,
        "kept": {
            "clean_train": sum(r["split"] == "clean_train" for r in records),
            "clean_eval": sum(r["split"] == "clean_eval" for r in records),
        },
        "files": records,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print("\n=== clean pool summary ===")
    print(f"scanned      : {manifest['total_scanned']}")
    print(f"duplicates   : {n_dup}")
    print(f"leaks dropped: {n_leak}")
    print(f"clean_train  : {manifest['kept']['clean_train']}")
    print(f"clean_eval   : {manifest['kept']['clean_eval']}")
    print(f"output       : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()