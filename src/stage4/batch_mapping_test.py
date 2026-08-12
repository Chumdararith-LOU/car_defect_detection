#!/usr/bin/env python3
"""Stage 4: Batch stress-test of the spatial context mapper.

Runs the mapper on N images from the Stage 2 test split and prints an
aggregate summary of panel assignments, IoD distribution, and Boundary/Trim rate.
Crop saving is disabled by default to keep the reports folder clean.
"""

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

# Reuse the mapper we already validated.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spatial_context_mapper import run_mapping  # noqa: E402

DEFAULT_TEST_DIR = "data/processed/yolo_seg_clean_2200_7cls/test/images"


def main():
    ap = argparse.ArgumentParser(description="Stage 4 batch mapping stress-test")
    ap.add_argument("--test-dir", default=DEFAULT_TEST_DIR)
    ap.add_argument("--n", type=int, default=10, help="Number of images to test")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default="reports/stage4_batch")
    ap.add_argument(
        "--save-crops",
        action="store_true",
        help="Also save per-defect crops (off by default)",
    )
    ap.add_argument(
        "--stage2-weights",
        default="runs/segment/stage1_head_warmup_7cls_extended/"
        "stage1_head_warmup_7cls_extended/weights/best.pt",
    )
    ap.add_argument(
        "--stage3-weights",
        default="mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/"
        "artifacts/weights/best.pt",
    )
    ap.add_argument("--sahi-config", default="configs/inference/sahi_production.yaml")
    ap.add_argument("--preset", default=None)
    ap.add_argument("--panel-conf", type=float, default=0.25)
    ap.add_argument("--device-s2", default="mps")
    ap.add_argument("--device-s3", default="mps")
    a = ap.parse_args()

    test_dir = Path(a.test_dir)
    if not test_dir.exists():
        raise FileNotFoundError(
            f"Test image dir not found: {test_dir}\n"
            "Pass --test-dir <path> pointing to your Stage 2 test images."
        )

    exts = {".jpg", ".jpeg", ".png"}
    images = sorted(p for p in test_dir.iterdir() if p.suffix.lower() in exts)
    if not images:
        raise FileNotFoundError(f"No images found in {test_dir}")

    rng = random.Random(a.seed)
    sample = rng.sample(images, min(a.n, len(images)))
    print(f"Testing {len(sample)} / {len(images)} images from {test_dir}\n")

    # Aggregate accumulators
    panel_assignments = Counter()
    iod_buckets = Counter()  # high (>=0.9), mid (0.5-0.9), boundary (<0.5)
    defect_classes = Counter()
    total_defects = 0
    images_with_defects = 0
    dsi_values = []
    failures = []

    for i, img_path in enumerate(sample, start=1):
        print("=" * 70)
        print(f"[{i}/{len(sample)}] {img_path.name}")
        try:
            report = run_mapping(
                image_path=img_path,
                stage2_weights=a.stage2_weights,
                stage3_weights=a.stage3_weights,
                sahi_cfg_path=a.sahi_config,
                out_dir=a.out_dir,
                device_s2=a.device_s2,
                device_s3=a.device_s3,
                preset_override=a.preset,
                panel_conf=a.panel_conf,
            )
        except Exception as e:  # noqa: BLE001
            print(f"  !! FAILED: {e}")
            failures.append((img_path.name, str(e)))
            continue

        defects = report.get("defects", [])
        if defects:
            images_with_defects += 1
        for d in defects:
            total_defects += 1
            m = d["metrics"]
            panel = m["assigned_panel"]
            iod = m["containment_ratio_iod"]
            dsi = m["damage_severity_index_dsi"]

            panel_assignments[panel] += 1
            defect_classes[d["class"]] += 1
            dsi_values.append(dsi)

            if iod >= 0.9:
                iod_buckets["high (>=0.90)"] += 1
            elif iod >= 0.5:
                iod_buckets["mid  (0.50-0.90)"] += 1
            else:
                iod_buckets["boundary (<0.50)"] += 1

        # Optionally delete crops to save space (keep overlay + json only).
        if not a.save_crops:
            for d in defects:
                cp = Path(d["crop_storage_path"])
                if cp.exists():
                    cp.unlink()

    # ---- Aggregate summary ----
    print("\n" + "#" * 70)
    print("# STAGE 4 BATCH STRESS-TEST SUMMARY")
    print("#" * 70)
    print(f"Images tested:        {len(sample)}")
    print(f"Images w/ defects:    {images_with_defects}")
    print(f"Total defects found:  {total_defects}")
    print(f"Failures:             {len(failures)}")

    print("\n-- Panel assignment distribution --")
    for panel, cnt in panel_assignments.most_common():
        pct = 100.0 * cnt / total_defects if total_defects else 0.0
        print(f"  {panel:<16} {cnt:>4}  ({pct:5.1f}%)")

    print("\n-- IoD containment distribution --")
    for bucket in ["high (>=0.90)", "mid  (0.50-0.90)", "boundary (<0.50)"]:
        cnt = iod_buckets.get(bucket, 0)
        pct = 100.0 * cnt / total_defects if total_defects else 0.0
        print(f"  {bucket:<22} {cnt:>4}  ({pct:5.1f}%)")

    print("\n-- Defect class breakdown --")
    for cls, cnt in defect_classes.most_common():
        print(f"  {cls:<16} {cnt:>4}")

    if dsi_values:
        print(f"\n-- DSI stats (n={len(dsi_values)}) --")
        print(
            f"  min={min(dsi_values):.3f}%  "
            f"mean={sum(dsi_values)/len(dsi_values):.3f}%  "
            f"max={max(dsi_values):.3f}%"
        )

    if failures:
        print("\n-- FAILURES --")
        for name, err in failures:
            print(f"  {name}: {err}")


if __name__ == "__main__":
    main()
