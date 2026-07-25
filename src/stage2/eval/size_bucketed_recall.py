import os
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm
from shapely.geometry import Polygon
from ultralytics import YOLO
from PIL import Image


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
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        help="Device for inference ('mps', 'cuda', 'cpu')",
    )
    parser.add_argument(
        "--use_sahi", action="store_true", help="Enable SAHI patch tiling inference"
    )
    parser.add_argument(
        "--slice_size", type=int, default=640, help="SAHI slice patch height and width"
    )
    parser.add_argument(
        "--overlap_ratio",
        type=float,
        default=0.25,
        help="SAHI patch overlap ratio (25% enabled by 5s budget)",
    )
    args = parser.parse_args()

    val_images_dir = Path(args.data_dir) / "val" / "images"
    val_labels_dir = Path(args.data_dir) / "val" / "labels"

    print(f"[*] Loading model on device '{args.device}': {args.model}")
    if args.use_sahi:
        from sahi import AutoDetectionModel

        detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=args.model,
            confidence_threshold=0.25,
            device=args.device,
        )
    else:
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

        preds = []
        if args.use_sahi:
            from sahi.predict import get_sliced_prediction

            with Image.open(img_path) as img:
                img_w, img_h = img.size

            sahi_result = get_sliced_prediction(
                image=str(img_path),
                detection_model=detection_model,
                slice_height=args.slice_size,
                slice_width=args.slice_size,
                overlap_height_ratio=args.overlap_ratio,
                overlap_width_ratio=args.overlap_ratio,
                postprocess_type="NMS",
                postprocess_match_metric="IOS",
                postprocess_match_threshold=0.50,
                verbose=False,
            )

            for obj in sahi_result.object_prediction_list:
                cid = obj.category.id
                if obj.mask is not None:
                    try:
                        # obj.mask.segmentation is COCO-style: a list of
                        # [x1, y1, x2, y2, ...] polygons in full-image pixel
                        # coords (sahi.annotation.Mask has no to_polygon()).
                        segmentation = obj.mask.segmentation
                        if not segmentation:
                            continue

                        candidate_polys = []
                        for seg in segmentation:
                            if len(seg) < 6:
                                continue
                            norm_points = [
                                (seg[i] / img_w, seg[i + 1] / img_h)
                                for i in range(0, len(seg), 2)
                            ]
                            p = Polygon(norm_points)
                            if p.is_valid and p.area > 0:
                                candidate_polys.append(p)

                        if not candidate_polys:
                            continue

                        # A mask can decode into multiple disjoint polygon
                        # parts (e.g. an occluded instance); keep the largest.
                        poly = max(candidate_polys, key=lambda p: p.area)
                        preds.append({"class_id": int(cid), "poly": poly})
                    except Exception as e:
                        tqdm.write(f"[!] Mask parse failed on {img_path.name}: {e}")
                        continue
        else:
            results = model.predict(
                source=str(img_path),
                imgsz=1024,
                verbose=False,
                conf=0.25,
                device=args.device,
            )
            result = results[0]

            if result.masks is not None:
                for cls_tensor, seg_coords in zip(result.boxes.cls, result.masks.xyn):
                    try:
                        poly = Polygon(seg_coords)
                        if poly.is_valid:
                            preds.append(
                                {"class_id": int(cls_tensor.item()), "poly": poly}
                            )
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
