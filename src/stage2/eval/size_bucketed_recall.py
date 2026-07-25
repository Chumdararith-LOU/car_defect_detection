import os
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm
from shapely.geometry import Polygon
from ultralytics import YOLO


def parse_yolo_labels(label_path):
    """Parses a YOLO segmentation label file into Shapely polygons."""
    gts = []
    if not os.path.exists(label_path):
        return gts

    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 7:
                continue

            class_id = int(parts[0])
            coords = [float(x) for x in parts[1:]]

            # Group into (x, y) tuples
            points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]

            try:
                poly = Polygon(points)
                if poly.is_valid and poly.area > 0:
                    gts.append(
                        {
                            "class_id": class_id,
                            "poly": poly,
                            "area": poly.area,
                            "detected": False,
                        }
                    )
            except Exception:
                continue
    return gts


def calculate_iou(poly1, poly2):
    """Calculates Intersection over Union between two Shapely polygons."""
    if not poly1.intersects(poly2):
        return 0.0
    try:
        intersection = poly1.intersection(poly2).area
        union = poly1.union(poly2).area
        return intersection / union if union > 0 else 0.0
    except Exception:
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Size-Bucketed Recall Evaluator")
    parser.add_argument(
        "--model", type=str, required=True, help="Path to trained .pt model"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/processed/stage2",
        help="Path to stage 2 dataset root",
    )
    parser.add_argument(
        "--iou_thresh",
        type=float,
        default=0.5,
        help="IoU threshold for a True Positive",
    )
    args = parser.parse_args()

    val_images_dir = Path(args.data_dir) / "val" / "images"
    val_labels_dir = Path(args.data_dir) / "val" / "labels"

    print(f"[*] Loading model: {args.model}")
    model = YOLO(args.model)

    print("[*] Parsing Ground Truth and Calculating Areas...")
    image_files = list(val_images_dir.glob("*.jpg")) + list(
        val_images_dir.glob("*.png")
    )

    all_gts = {}
    all_areas = []

    for img_path in image_files:
        label_path = val_labels_dir / f"{img_path.stem}.txt"
        gts = parse_yolo_labels(label_path)
        all_gts[img_path.name] = gts
        for gt in gts:
            all_areas.append(gt["area"])

    if not all_areas:
        print("[-] No ground truth labels found. Exiting.")
        return

    # Calculate percentiles based on normalized area (fraction of image canvas)
    p10 = np.percentile(all_areas, 10)
    p60 = np.percentile(all_areas, 60)

    print(
        f"[*] Area Thresholds -> Bottom 10% < {p10:.6f} | Middle 50% | Top 40% > {p60:.6f}"
    )

    print("[*] Running Inference and Matching (IoU)...")
    for img_path in tqdm(image_files, desc="Evaluating"):
        gts = all_gts[img_path.name]
        if not gts:
            continue

        # Run inference (imgsz=1024 to match our strict baseline config)
        results = model.predict(
            source=str(img_path), imgsz=1024, verbose=False, conf=0.25
        )
        result = results[0]

        preds = []
        if result.masks is not None:
            # result.masks.xyn contains normalized coordinates
            for cls_tensor, seg_coords in zip(result.boxes.cls, result.masks.xyn):
                try:
                    poly = Polygon(seg_coords)
                    if poly.is_valid:
                        preds.append({"class_id": int(cls_tensor.item()), "poly": poly})
                except Exception:
                    continue

        # Match predictions to ground truth
        for gt in gts:
            best_iou = 0.0
            for pred in preds:
                if pred["class_id"] == gt["class_id"]:
                    iou = calculate_iou(gt["poly"], pred["poly"])
                    if iou > best_iou:
                        best_iou = iou

            if best_iou >= args.iou_thresh:
                gt["detected"] = True

    CLASS_NAMES = {
        0: "dent",
        1: "scratch",
        2: "crack",
        3: "glass_shatter",
        4: "broken_component",
        5: "missing_component",
        6: "corrosion",
    }

    per_class_buckets = {}

    for gts in all_gts.values():
        for gt in gts:
            cid = gt["class_id"]
            if cid not in per_class_buckets:
                per_class_buckets[cid] = {
                    "Bottom 10%": {"tp": 0, "total": 0},
                    "Middle 50%": {"tp": 0, "total": 0},
                    "Top 40%": {"tp": 0, "total": 0},
                }

            if gt["area"] <= p10:
                b = "Bottom 10%"
            elif gt["area"] <= p60:
                b = "Middle 50%"
            else:
                b = "Top 40%"

            per_class_buckets[cid][b]["total"] += 1
            if gt["detected"]:
                per_class_buckets[cid][b]["tp"] += 1

    print("\n" + "=" * 85)
    print(" 📊 PER-CLASS SIZE-BUCKETED RECALL REPORT")
    print("=" * 85)
    header = f"{'Class':<18} | {'Bottom 10% (Micro)':<18} | {'Middle 50% (Med)':<18} | {'Top 40% (Macro)':<18} | {'Overall':<10}"
    print(header)
    print("-" * 85)

    for cid in sorted(per_class_buckets.keys()):
        c_name = CLASS_NAMES.get(cid, f"Class {cid}")
        b_stats = per_class_buckets[cid]

        row_str = f"{c_name:<18} | "
        total_tp, total_gt = 0, 0

        for b_name in ["Bottom 10%", "Middle 50%", "Top 40%"]:
            tp = b_stats[b_name]["tp"]
            tot = b_stats[b_name]["total"]
            total_tp += tp
            total_gt += tot
            rec = (tp / tot * 100) if tot > 0 else 0.0
            row_str += f"{rec:>5.1f}% ({tp}/{tot})     | "

        overall_rec = (total_tp / total_gt * 100) if total_gt > 0 else 0.0
        row_str += f"{overall_rec:>5.1f}%"
        print(row_str)
    print("=" * 85)


if __name__ == "__main__":
    main()
