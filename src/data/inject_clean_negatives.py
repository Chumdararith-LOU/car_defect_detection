#!/usr/bin/env python3
"""Inject clean (undamaged) car images into the YOLO-seg training set as 
hard negatives.

Maintains idempotency by prefixing injected files with 'cneg__'. Re-running 
this script with a different ratio will cleanly remove previous injections 
before adding the new ones.

Usage:
    python src/data/inject_clean_negatives.py --neg-ratio 0.10
    python src/data/inject_clean_negatives.py --neg-ratio 0.15 --seed 42
"""

import argparse
import json
import random
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CLEAN_IMG_DIR = REPO_ROOT / "data/processed/clean_cars/images/clean_train"
CLEAN_LBL_DIR = REPO_ROOT / "data/processed/clean_cars/labels/clean_train"

PREFIX = "cneg__"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--neg-ratio", 
        type=float, 
        default=0.10,
        help="Target fraction of clean images in the final combined train set (e.g. 0.10 for 10%%)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="yolo_seg",
        help="Dataset directory name under data/processed/ (default: yolo_seg)"
    )
    args = parser.parse_args()

    if not (0.0 < args.neg_ratio < 1.0):
        raise ValueError("--neg-ratio must be between 0.0 and 1.0")

    base = REPO_ROOT / "data/processed" / args.target
    pos_img_dir = base / "images/train"
    pos_lbl_dir = base / "labels/train"
    manifest_path = base / ".injected_clean.json"

    # 1. Clean up any previous injections (Idempotency)
    removed = 0
    for d in [pos_img_dir, pos_lbl_dir]:
        if d.exists():
            for f in d.glob(f"{PREFIX}*"):
                f.unlink()
                removed += 1
    if removed > 0:
        print(f"[cleanup] removed {removed} previously injected files.")

    # 2. Count true positive images (ignoring any leftover prefixed files)
    pos_imgs = [f for f in pos_img_dir.iterdir() if not f.name.startswith(PREFIX)]
    n_pos = len(pos_imgs)
    print(f"[count] positive training images: {n_pos}")

    # 3. Calculate required clean images: X = P * R / (1 - R)
    n_clean_target = round(n_pos * args.neg_ratio / (1.0 - args.neg_ratio))

    # 4. Sample from the clean pool
    clean_pool = sorted(CLEAN_IMG_DIR.iterdir())
    if not clean_pool:
        raise RuntimeError("Clean pool is empty. Run build_clean_pool.py first.")

    if n_clean_target > len(clean_pool):
        print(f"[warn] requested {n_clean_target} but only {len(clean_pool)} available. Capping.")
        n_clean_target = len(clean_pool)

    random.seed(args.seed)
    sampled = random.sample(clean_pool, n_clean_target)

    # 5. Copy images and empty labels
    copied = 0
    for img_path in sampled:
        new_img_name = f"{PREFIX}{img_path.name}"
        lbl_name = img_path.stem + ".txt"
        new_lbl_name = f"{PREFIX}{lbl_name}"

        shutil.copy2(img_path, pos_img_dir / new_img_name)

        src_lbl = CLEAN_LBL_DIR / lbl_name
        if src_lbl.exists():
            shutil.copy2(src_lbl, pos_lbl_dir / new_lbl_name)
        else:
            # Fallback: create empty file if somehow missing
            (pos_lbl_dir / new_lbl_name).touch()
        copied += 1

    # 6. Write manifest for auditability
    total_train = n_pos + copied
    manifest = {
        "neg_ratio_target": args.neg_ratio,
        "neg_ratio_actual": copied / total_train if total_train > 0 else 0,
        "positive_images": n_pos,
        "injected_clean_images": copied,
        "total_train_images": total_train,
        "seed": args.seed,
        "prefix": PREFIX
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\n=== injection summary ===")
    print(f"target ratio : {args.neg_ratio:.2%}")
    print(f"actual ratio : {manifest['neg_ratio_actual']:.2%}")
    print(f"positive imgs: {n_pos}")
    print(f"injected     : {copied}")
    print(f"total train  : {total_train}")
    print(f"manifest     : {manifest_path}")


if __name__ == "__main__":
    main()