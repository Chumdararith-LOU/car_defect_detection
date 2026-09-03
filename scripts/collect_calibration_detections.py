"""Collect raw detections from all test + clean images for threshold calibration.

Runs inference with the lowest possible thresholds to capture ALL detections,
then saves them to a JSON file for offline threshold sweeping.

Usage:
    python scripts/collect_calibration_detections.py          # full run
    python scripts/collect_calibration_detections.py 5        # smoke test, 5 images
"""

import json
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.stage2_sahi import SAHI_CFG, run_sahi_inference  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# --- CONFIG ---
# Use calib preset and override thresholds to capture every detection.
PRESET = "calib"
DEVICE = "mps"
OUTPUT_PATH = ROOT / "data" / "calibration" / "calibration_raw_detections.json"

TEST_DIR = ROOT / "data" / "processed" / "yolo_seg" / "images" / "test"
CLEAN_DIR = ROOT / "data" / "processed" / "clean_cars" / "images" / "clean_eval"

# Optional smoke-test limit: python collect_calibration_detections.py N
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None

if not TEST_DIR.exists():
    print(f"ERROR: Test image directory not found: {TEST_DIR}")
    sys.exit(1)
if not CLEAN_DIR.exists():
    print(f"WARNING: Clean image directory not found: {CLEAN_DIR}")
    CLEAN_DIR = None

# Override two-tier gating so nothing is suppressed or relabeled.
SAHI_CFG["two_tier_gating"]["obj_threshold"] = 0.01
SAHI_CFG["two_tier_gating"]["cls_threshold"] = 0.01

# Override per-class acceptance rules so every detection above the model
# floor (0.01) is captured for offline sweeping (name-keyed rules).
SAHI_CFG["presets"][PRESET]["class_rules"] = {
    name: {"conf": 0.01, "min_area": 0}
    for name in [
        "default",
        "dent",
        "scratch",
        "crack",
        "glass_shatter",
        "broken_part",
        "corrosion",
        "disjoint_part",
    ]
}


def collect_images(d: Path) -> list:
    return sorted(
        p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")
    )


test_images = collect_images(TEST_DIR)
clean_images = collect_images(CLEAN_DIR) if CLEAN_DIR else []

if LIMIT is not None:
    test_images = test_images[:LIMIT]
    clean_images = clean_images[:LIMIT]

print(f"Test images: {len(test_images)}")
print(f"Clean images: {len(clean_images)}")
print(f"Preset: {PRESET}, Device: {DEVICE}")
print(
    f"Two-tier override: obj={SAHI_CFG['two_tier_gating']['obj_threshold']}, "
    f"cls={SAHI_CFG['two_tier_gating']['cls_threshold']}"
)
print("-" * 60)

results = []
total = len(test_images) + len(clean_images)

for idx, img_path in enumerate(test_images + clean_images):
    label = "defect" if idx < len(test_images) else "clean"
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"  SKIP (unreadable): {img_path.name}")
        continue
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    t0 = time.time()
    detections = run_sahi_inference(
        img_rgb, f"calib_{idx:04d}", preset=PRESET, device=DEVICE
    )
    elapsed = time.time() - t0

    img_dets = []
    for d in detections:
        img_dets.append(
            {
                "class": d["defect_class"],
                "confidence": d["confidence"],
                "bbox": list(d["global_bbox_xyxy"]),
            }
        )

    results.append(
        {
            "image_path": str(img_path),
            "image_name": img_path.name,
            "label": label,
            "detections": img_dets,
            "num_detections": len(img_dets),
            "inference_time_s": round(elapsed, 2),
        }
    )

    if (idx + 1) % 20 == 0 or idx == total - 1:
        print(
            f"  [{idx + 1}/{total}] {img_path.name}: "
            f"{len(img_dets)} dets ({elapsed:.1f}s)"
        )

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    json.dump(results, f, indent=1)

total_dets = sum(r["num_detections"] for r in results)
avg_time = (
    sum(r["inference_time_s"] for r in results) / len(results) if results else 0.0
)

print("-" * 60)
print(f"Saved {len(results)} image results to {OUTPUT_PATH}")
print(f"   Total detections: {total_dets}")
print(f"   Avg time/image: {avg_time:.1f}s")
