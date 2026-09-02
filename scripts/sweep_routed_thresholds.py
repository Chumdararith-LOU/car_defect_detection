"""Sweep per-class confidence thresholds on the routed-safety detections.

Finds the operating point that eliminates baseline_m5's low-confidence FPs
on scratch/dent/broken_lamp/crack while preserving high-confidence TPs.
"""

import csv
import itertools
import json
from pathlib import Path

INPUT_PATH = Path("data/calibration/routed_safety_detections.json")
OUTPUT_PATH = Path("data/calibration/routed_threshold_sweep.csv")

with open(INPUT_PATH) as f:
    data = json.load(f)

clean_imgs = [img for img in data if img["label"] == "clean"]
defect_imgs = [img for img in data if img["label"] == "defect"]

print(f"Loaded {len(clean_imgs)} clean images, {len(defect_imgs)} defect images.")

# Sweep parameters for the 4 problematic classes
classes_to_sweep = ["scratch", "dent", "broken_lamp", "crack"]
thresholds = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]

results = []

for t_scratch, t_dent, t_bl, t_crack in itertools.product(thresholds, repeat=4):
    thresh_map = {
        "scratch": t_scratch,
        "dent": t_dent,
        "broken_lamp": t_bl,
        "crack": t_crack,
    }

    clean_triggers = 0
    defect_triggers = 0

    for img in data:
        surviving = [
            d
            for d in img["detections"]
            if d["confidence"] >= thresh_map.get(d["class"], 0.0)
        ]

        has_trigger = len(surviving) > 0
        if img["label"] == "clean":
            if has_trigger:
                clean_triggers += 1
        else:
            if has_trigger:
                defect_triggers += 1

    fpr = clean_triggers / len(clean_imgs)
    recall = defect_triggers / len(defect_imgs)

    results.append(
        {
            "t_scratch": t_scratch,
            "t_dent": t_dent,
            "t_bl": t_bl,
            "t_crack": t_crack,
            "FPR": round(fpr, 4),
            "Recall": round(recall, 4),
            "Clean_Triggers": clean_triggers,
            "Defect_Triggers": defect_triggers,
        }
    )

# Save to CSV
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "t_scratch",
            "t_dent",
            "t_bl",
            "t_crack",
            "FPR",
            "Recall",
            "Clean_Triggers",
            "Defect_Triggers",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved {len(results)} combinations to {OUTPUT_PATH}")

# Find best operating points
# Strict target first
valid = [r for r in results if r["FPR"] <= 0.45 and r["Recall"] >= 0.93]
if not valid:
    # Fallback to just FPR target
    valid = [r for r in results if r["FPR"] <= 0.45]

valid.sort(key=lambda x: (-x["Recall"], x["FPR"]))

print("\nTop 5 combinations (Target: FPR <= 45%, Recall >= 93%):")
for r in valid[:5]:
    print(
        f"  FPR={r['FPR']*100:.1f}% ({r['Clean_Triggers']}/150), "
        f"Recall={r['Recall']*100:.1f}% ({r['Defect_Triggers']}/593)"
    )
    print(
        f"    scratch={r['t_scratch']:.2f}, dent={r['t_dent']:.2f}, "
        f"broken_lamp={r['t_bl']:.2f}, crack={r['t_crack']:.2f}"
    )

if not valid:
    print("\nWARNING: No combination achieves FPR <= 45%. Showing best FPR instead:")
    results.sort(key=lambda x: (x["FPR"], -x["Recall"]))
    for r in results[:5]:
        print(f"  FPR={r['FPR']*100:.1f}%, Recall={r['Recall']*100:.1f}%")
        print(
            f"    scratch={r['t_scratch']:.2f}, dent={r['t_dent']:.2f}, "
            f"broken_lamp={r['t_bl']:.2f}, crack={r['t_crack']:.2f}"
        )
