"""Live sweep of safety disjoint_part conf over the full calibration set."""

import json
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from services.stage2_sahi import SAHI_CFG, run_sahi_inference  # noqa: E402

# reuse image list + labels from the Phase 4D calibration JSON
data = json.load(open("data/calibration/calibration_raw_detections.json"))

for conf in [0.10, 0.15, 0.20, 0.25, 0.30]:
    SAHI_CFG["presets"]["safety"]["class_rules"]["disjoint_part"]["conf"] = conf
    clean_trig = defect_trig = disjoint_count = 0
    t0 = time.time()
    for item in data:
        img = cv2.imread(item["image_path"])
        if img is None:
            continue
        dets = run_sahi_inference(
            cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
            f"sw_{item['image_name']}",
            preset="safety",
            device="mps",
        )
        if dets:
            clean_trig += item["label"] == "clean"
            defect_trig += item["label"] == "defect"
        disjoint_count += sum(1 for d in dets if d["defect_class"] == "disjoint_part")
    print(
        f"conf={conf:.2f} | FPR={clean_trig/150*100:.1f}% | "
        f"Recall={defect_trig/593*100:.1f}% | "
        f"disjoint_dets={disjoint_count} | {time.time()-t0:.0f}s",
        flush=True,
    )
