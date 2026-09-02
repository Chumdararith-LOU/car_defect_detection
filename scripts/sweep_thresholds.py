"""Sweep two-tier gating thresholds offline and calculate image-level FPR and Recall."""

import csv
import json
from pathlib import Path

INPUT_PATH = Path("data/calibration/calibration_raw_detections.json")
OUTPUT_PATH = Path("data/calibration/threshold_sweep_results.csv")

with open(INPUT_PATH) as f:
    data = json.load(f)

clean_imgs = [img for img in data if img["label"] == "clean"]
defect_imgs = [img for img in data if img["label"] == "defect"]

print(f"Loaded {len(clean_imgs)} clean images, {len(defect_imgs)} defect images.")

obj_thresholds = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]
cls_thresholds = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

results = []

for obj_t in obj_thresholds:
    for cls_t in cls_thresholds:
        # Ensure cls_t > obj_t logically, though math handles it anyway
        if cls_t < obj_t:
            continue

        clean_triggers = 0
        defect_triggers = 0
        defect_known_triggers = 0

        for img in data:
            # A detection survives background suppression if score >= obj_t
            surviving = [d for d in img["detections"] if d["confidence"] >= obj_t]
            # It gets a known class if score >= cls_t, otherwise it's defect_unknown
            known = [d for d in surviving if d["confidence"] >= cls_t]

            has_trigger = len(surviving) > 0
            has_known = len(known) > 0

            if img["label"] == "clean":
                if has_trigger:
                    clean_triggers += 1
            else:
                if has_trigger:
                    defect_triggers += 1
                if has_known:
                    defect_known_triggers += 1

        fpr = clean_triggers / len(clean_imgs) if clean_imgs else 0
        recall = defect_triggers / len(defect_imgs) if defect_imgs else 0
        known_recall = defect_known_triggers / len(defect_imgs) if defect_imgs else 0

        results.append(
            {
                "obj_thresh": obj_t,
                "cls_thresh": cls_t,
                "FPR": round(fpr, 4),
                "Recall": round(recall, 4),
                "Known_Recall": round(known_recall, 4),
            }
        )

# Save to CSV
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["obj_thresh", "cls_thresh", "FPR", "Recall", "Known_Recall"]
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved {len(results)} combinations to {OUTPUT_PATH}")

# Print best operating points for our target presets
print("\n--- RECOMMENDED OPERATING POINTS ---")
for target_fpr, preset_name in [
    (0.30, "balanced"),
    (0.45, "safety"),
    (0.60, "max_recall"),
]:
    # Filter for FPR <= target, then sort by highest Recall
    valid = [r for r in results if r["FPR"] <= target_fpr]
    if valid:
        best = max(valid, key=lambda x: x["Recall"])
        print(
            f"{preset_name:10} (FPR <= {target_fpr*100:.0f}%): "
            f"obj={best['obj_thresh']:.2f}, cls={best['cls_thresh']:.2f} | "
            f"FPR={best['FPR']*100:.1f}%, Recall={best['Recall']*100:.1f}%, "
            f"Known={best['Known_Recall']*100:.1f}%"
        )
    else:
        print(
            f"{preset_name:10} (FPR <= {target_fpr*100:.0f}%): "
            "No valid combinations found!"
        )
