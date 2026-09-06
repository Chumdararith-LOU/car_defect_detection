import statistics
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
YAML_PATH = ROOT / "data" / "processed" / "yolo_seg" / "data.yaml"
LABELS_DIR = ROOT / "data" / "processed" / "yolo_seg" / "labels" / "train"
REPORT_PATH = ROOT / "reports" / "phase0_deep_analysis.md"

TINY_AREA = 0.001  # < 0.1% of image (~32x32 px at 1024)


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def main():
    with open(YAML_PATH) as f:
        names = yaml.safe_load(f)["names"]
    print("YAML ID -> Name mapping:")
    for cid in sorted(names):
        print(f"  {cid}: {names[cid]}")
    print()

    stats = {cid: {"areas": [], "malformed": 0} for cid in names}
    for path in sorted(LABELS_DIR.glob("*.txt")):
        for line in path.read_text().splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            cid = int(parts[0])
            if cid not in stats:
                continue
            w, h = float(parts[3]), float(parts[4])
            if w <= 0 or h <= 0:
                stats[cid]["malformed"] += 1
                continue
            stats[cid]["areas"].append(w * h * 100)

    lines = [
        "| Class (YAML) | Count | 10th %ile | Median %ile | 90th %ile | Tiny (<0.1%) | Malformed (0 area) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cid in sorted(names):
        s = stats[cid]
        areas = sorted(s["areas"])
        tiny = sum(1 for a in areas if a < TINY_AREA * 100)
        if areas:
            lines.append(
                f"| {names[cid]} | {len(areas)} | "
                f"{percentile(areas, 10):.4f} | {percentile(areas, 50):.4f} | "
                f"{percentile(areas, 90):.4f} | {tiny} | {s['malformed']} |"
            )
        else:
            lines.append(f"| {names[cid]} | 0 | - | - | - | 0 | {s['malformed']} |")

    table = "\n".join(lines)
    print(table)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(f"# Phase 0 — Deep Dataset Analysis\n\n{table}\n")


if __name__ == "__main__":
    main()
