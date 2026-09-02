"""Quick MPS integration test for multi-model SAHI pipeline."""

import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.stage2_sahi import SAHI_CFG, run_sahi_inference  # noqa: E402

TEST_IMAGE = None
for candidate in [
    "data/processed/stage2/test/images",
    "data/processed/yolo_seg_clean_2200_7cls/test/images",
    "data/test/images",
    "datasets/test/images",
    "backend/data/test/images",
]:
    p = Path(candidate)
    if p.exists():
        imgs = list(p.glob("*.jpg")) + list(p.glob("*.png"))
        if imgs:
            TEST_IMAGE = str(imgs[0])
            break

if TEST_IMAGE is None:
    print("ERROR: No test image found. Please provide a path.")
    sys.exit(1)

print(f"Test image: {TEST_IMAGE}")
print(f"Device: {SAHI_CFG.get('device')}")
print(f"Models registered: {list(SAHI_CFG.get('model_registry', {}).keys())}")

img = cv2.imread(TEST_IMAGE)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
print(f"Image shape: {img_rgb.shape}")

print("\n--- Test 1: balanced (objectness_branch_new only) ---")
t0 = time.time()
results = run_sahi_inference(img_rgb, "test_mps_1", preset="balanced", device="mps")
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s | Detections: {len(results)}")
for r in results[:5]:
    print(f"    {r['defect_class']} conf={r['confidence']:.3f}")

print("\n--- Test 2: safety (objectness_branch_new + baseline_m5, union) ---")
t0 = time.time()
results = run_sahi_inference(img_rgb, "test_mps_2", preset="safety", device="mps")
t1 = time.time()
print(f"  Time: {t1-t0:.1f}s | Detections: {len(results)}")
for r in results[:5]:
    print(f"    {r['defect_class']} conf={r['confidence']:.3f}")

print("\n✅ MPS integration test complete!")
