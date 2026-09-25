#!/usr/bin/env python3
"""Split leak check: MD5 every image in the candidate splits and assert zero
overlap between any pair.

Splits checked:
    yolo_seg_clean_augmented/{train,val,test}
    clean_cars/{clean_train,clean_eval}

Exits non-zero if any MD5 appears in more than one split.
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def md5_of(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = Path("data/processed")
    splits = {
        "yolo_seg_clean_augmented/train": root / "yolo_seg_clean_augmented/images/train",
        "yolo_seg_clean_augmented/val": root / "yolo_seg_clean_augmented/images/val",
        "yolo_seg_clean_augmented/test": root / "yolo_seg_clean_augmented/images/test",
        "clean_cars/clean_train": root / "clean_cars/images/clean_train",
        "clean_cars/clean_eval": root / "clean_cars/images/clean_eval",
    }

    by_hash = defaultdict(list)
    counts = {}
    for name, d in splits.items():
        if not d.is_dir():
            print(f"[error] missing dir: {d}")
            sys.exit(2)
        files = [p for p in sorted(d.iterdir()) if p.suffix.lower() in IMAGE_EXTS]
        counts[name] = len(files)
        for i, p in enumerate(files, 1):
            by_hash[md5_of(p)].append(name)
            if i % 1000 == 0:
                print(f"  [{name}] {i}/{len(files)} hashed", flush=True)

    print(f"\n{'split':<35} {'images':>8}")
    for name in splits:
        print(f"{name:<35} {counts[name]:>8}")

    # Overlap between the dataset train split and clean_cars/clean_train is the
    # INTENDED hard-negative injection (cneg__ files, see .injected_clean.json).
    # Any other cross-split overlap is a leak.
    EXPECTED_PAIR = frozenset({"yolo_seg_clean_augmented/train", "clean_cars/clean_train"})

    leaks, expected = {}, 0
    for h, s in by_hash.items():
        if len(set(s)) > 1:
            if frozenset(set(s)) == EXPECTED_PAIR:
                expected += 1
            else:
                leaks[h] = s
    if leaks:
        print(f"\n[FAIL] {len(leaks)} MD5 hash(es) leak across disjoint splits:")
        for h, s in list(leaks.items())[:20]:
            print(f"  {h}: {sorted(set(s))}")
        sys.exit(1)

    print(f"\n[OK] zero leak between disjoint splits "
          f"({len(by_hash)} unique hashes across {sum(counts.values())} images)")
    print(f"[note] {expected} expected overlap(s): dataset train <-> clean_cars/clean_train "
          f"(intended cneg__ hard-negative injection)")

    dup_within = {h: s for h, s in by_hash.items() if len(s) > 1 and len(set(s)) == 1}
    if dup_within:
        print(f"[note] {len(dup_within)} hash(es) duplicated WITHIN a single split (not a leak):")
        for h, s in list(dup_within.items())[:10]:
            print(f"  {h}: {s}")


if __name__ == "__main__":
    main()
