"""Run a production preset over the calibration set; compute image-level FPR/recall.

Reuses the image list + labels from the Phase 4D calibration JSON so we test
the exact same 743 images. Unlike the sweep (single model via calib preset),
this runs the REAL preset routing — so safety/specialist/max_recall exercise
their full multi-model union/per_class merge.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.stage2_sahi import run_sahi_inference  # noqa: E402

CALIB_JSON = Path("data/calibration/calibration_raw_detections.json")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--preset",
    required=True,
    choices=[
        "balanced",
        "safety",
        "specialist",
        "max_recall",
        "legacy_champion",
        "single_objectness",
        "single_baseline_m5",
        "single_model_4",
    ],
)
parser.add_argument(
    "--limit", type=int, default=0, help="0 = all images; N = up to N per class"
)
parser.add_argument("--device", default="mps")
args = parser.parse_args()

with open(CALIB_JSON) as f:
    calib = json.load(f)

clean = [c for c in calib if c["label"] == "clean"]
defect = [c for c in calib if c["label"] == "defect"]
# JSON is defect-first (593) then clean (150), so a naive head slice
# would contain only defect images; cap per class so FPR stays measurable.
if args.limit:
    clean = clean[: args.limit]
    defect = defect[: args.limit]
calib = defect + clean
print(f"Preset: {args.preset} | {len(clean)} clean, {len(defect)} defect")

clean_triggers = 0
defect_triggers = 0
class_counts = {}
unknown_count = 0
t0 = time.time()

for i, item in enumerate(calib):
    img = cv2.imread(item["image_path"])
    if img is None:
        continue
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    dets = run_sahi_inference(
        img_rgb, f"integ_{i:04d}", preset=args.preset, device=args.device
    )

    if dets:
        if item["label"] == "clean":
            clean_triggers += 1
        else:
            defect_triggers += 1
    for d in dets:
        cls = d["defect_class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1
        if cls == "defect_unknown":
            unknown_count += 1

    if (i + 1) % 50 == 0:
        print(f"  [{i+1}/{len(calib)}] elapsed={time.time()-t0:.0f}s")

fpr = clean_triggers / len(clean) if clean else 0
recall = defect_triggers / len(defect) if defect else 0
print("\n" + "=" * 50)
print(f"PRESET: {args.preset}")
print(f"FPR:    {fpr*100:.1f}%  ({clean_triggers}/{len(clean)} clean triggered)")
print(
    f"Recall: {recall*100:.1f}%  " f"({defect_triggers}/{len(defect)} defect triggered)"
)
print(f"defect_unknown count: {unknown_count}")
print(f"Class distribution: {json.dumps(class_counts, indent=2)}")
print(f"Total time: {time.time()-t0:.0f}s")
