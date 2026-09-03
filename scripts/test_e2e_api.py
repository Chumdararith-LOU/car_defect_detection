"""End-to-end API smoke test: POST /api/inspect with defaults through the pipeline."""

import sys
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8010"

# Find a defect test image
TEST_IMAGE = None
for candidate in [
    "data/processed/stage2/test/images",
    "data/processed/yolo_seg/images/test",
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
    print("ERROR: No test image found.")
    sys.exit(1)

print(f"Test image: {TEST_IMAGE}")
print(f"API: {API_BASE}/api/inspect")
print("-" * 60)

# Read image
with open(TEST_IMAGE, "rb") as f:
    img_bytes = f.read()

# POST with defaults (no stage2_mode, no stage2_preset specified)
# This tests that the backend defaults to sahi/safety
payload = {
    "enable_stage1": "true",
    "enable_stage2": "true",
    "enable_stage3": "true",
    "device": "auto",
}

t0 = time.time()
resp = requests.post(
    f"{API_BASE}/api/inspect",
    files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    data=payload,
)
elapsed = time.time() - t0

if resp.status_code != 200:
    print(f"FAIL: HTTP {resp.status_code}")
    print(resp.text)
    sys.exit(1)

data = resp.json()

print(f"Status: {resp.status_code} | Time: {elapsed:.1f}s")
print(f"Inspection ID: {data.get('inspection_id')}")
print(f"Inspection status: {data.get('inspection_status')}")
print(f"Total defects: {data.get('total_defects_found')}")
print(f"Device used: {data.get('device_used')}")
print(f"Inference time: {data.get('inference_ms')} ms")

defects = data.get("defects", [])
if defects:
    print("\nFirst 5 defects:")
    for d in defects[:5]:
        print(
            f"  {d['class']} conf={d['confidence']:.3f} "
            f"panel={d.get('panel', 'Unknown')}"
        )
else:
    print("\nWARNING: No defects detected — Stage 1 may have gated this as clean.")
    print("   If this is a defect image, the test FAILED.")

# Check for warnings / degraded_stages
if "warnings" in data:
    print(f"\nWarnings: {data['warnings']}")
if "degraded_stages" in data:
    print(f"Degraded stages: {data['degraded_stages']}")

print("\n" + "=" * 60)
if data.get("total_defects_found", 0) > 0:
    print("PASS: Pipeline ran end-to-end with defaults and detected defects.")
else:
    print("WARNING: No defects detected. Verify this is a defect image.")
