import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LABELS_DIR = ROOT / "data" / "processed" / "yolo_seg" / "labels" / "train"
REPORT_PATH = ROOT / "reports" / "phase0_dataset_analysis.md"

CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_lamp",
    5: "corrosion",
    6: "disjoint_part",
}


def collect_stats():
    stats = {cid: {"areas": [], "ratios": []} for cid in CLASS_NAMES}
    for path in sorted(LABELS_DIR.glob("*.txt")):
        for line in path.read_text().splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            cid = int(parts[0])
            if cid not in stats:
                continue
            w, h = float(parts[3]), float(parts[4])
            stats[cid]["areas"].append(w * h * 100)
            if h > 0:
                stats[cid]["ratios"].append(w / h)
    return stats


def build_table(stats):
    lines = [
        "| Class | Instances | Mean Area % | Min Area % | Max Area % | Mean Aspect (w/h) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for cid in sorted(CLASS_NAMES):
        s = stats[cid]
        areas, ratios = s["areas"], s["ratios"]
        lines.append(
            f"| {CLASS_NAMES[cid]} | {len(areas)} | "
            f"{statistics.mean(areas):.4f} | {min(areas):.4f} | {max(areas):.4f} | "
            f"{statistics.mean(ratios):.3f} |" if areas else
            f"| {CLASS_NAMES[cid]} | 0 | - | - | - | - |"
        )
    lines.append(f"\nTotal labeled images scanned: {len(list(LABELS_DIR.glob('*.txt')))}")
    return "\n".join(lines)


def main():
    table = build_table(collect_stats())
    print(table)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(f"# Phase 0 — Dataset Imbalance Analysis\n\n{table}\n")


if __name__ == "__main__":
    main()
