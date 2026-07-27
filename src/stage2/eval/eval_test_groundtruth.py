import argparse
import os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from tqdm import tqdm
from ultralytics import YOLO

CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_component",
    5: "missing_component",
    6: "corrosion",
}


def parse_yolo_labels(label_path):
    """Parses YOLO normalized polygon labels into Shapely polygons."""
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
            points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]

            try:
                poly = Polygon(points)
                if poly.is_valid and poly.area > 0:
                    gts.append(
                        {
                            "class_id": class_id,
                            "poly": poly,
                            "matched": False,
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


def draw_visualizations(img_path, gts, preds, mode_name, save_dir, img_w, img_h):
    """Renders Ground Truth (Green) vs Predictions (Cyan/Red FP) overlay images."""
    cv_img = cv2.imread(str(img_path))
    if cv_img is None:
        return

    overlay = cv_img.copy()

    # 1. Draw Ground Truth Polygons (GREEN)
    for gt in gts:
        cid = gt["class_id"]
        cname = CLASS_NAMES.get(cid, f"cls_{cid}")
        pts = np.array(
            [
                (int(p[0] * img_w), int(p[1] * img_h))
                for p in gt["poly"].exterior.coords
            ],
            np.int32,
        )
        cv2.polylines(cv_img, [pts], isClosed=True, color=(0, 255, 0), thickness=3)
        cv2.putText(
            cv_img,
            f"GT: {cname}",
            (pts[0][0], max(15, pts[0][1] - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    # 2. Draw Model Predictions (CYAN for True Positive, RED for False Positive)
    for pred in preds:
        cid = pred["class_id"]
        conf = pred["conf"]
        is_tp = pred["matched"]
        cname = CLASS_NAMES.get(cid, f"cls_{cid}")

        # Color: Cyan (255, 255, 0) for True Positive, Red (0, 0, 255) for False Positive
        color = (255, 255, 0) if is_tp else (0, 0, 255)
        status = "TP" if is_tp else "FP [HALLUCINATION]"

        pts = np.array(
            [
                (int(p[0] * img_w), int(p[1] * img_h))
                for p in pred["poly"].exterior.coords
            ],
            np.int32,
        )
        cv2.fillPoly(overlay, [pts], color)
        cv2.polylines(cv_img, [pts], isClosed=True, color=color, thickness=2)

        label_str = f"{cname} {conf:.2f} ({status})"
        cv2.putText(
            cv_img,
            label_str,
            (pts[0][0], max(15, pts[0][1] + 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # Blend overlay mask transparency
    cv2.addWeighted(overlay, 0.3, cv_img, 0.7, 0, cv_img)

    out_file = save_dir / f"{img_path.stem}_{mode_name}.jpg"
    cv2.imwrite(str(out_file), cv_img)


def evaluate_mode(
    mode_name,
    all_images,
    val_labels_dir,
    args,
    detection_model=None,
    ultralytics_model=None,
    slice_height=None,
    slice_width=None,
):
    """
    Evaluate a single inference mode.

    Args:
        mode_name: Identifier string for this mode (e.g. "direct1024", "sahi1024", "sahi640")
        slice_height: Patch height for SAHI (ignored for direct inference)
        slice_width: Patch width for SAHI (ignored for direct inference)
    """
    stats = {
        cid: {"tp": 0, "fp": 0, "fn": 0, "total_gt": 0} for cid in CLASS_NAMES.keys()
    }

    save_dir = Path(args.output_dir) / mode_name
    save_dir.mkdir(parents=True, exist_ok=True)

    is_sahi = slice_height is not None and slice_width is not None

    for img_path in tqdm(all_images, desc=f"Evaluating {mode_name}"):
        label_path = val_labels_dir / f"{img_path.stem}.txt"
        gts = parse_yolo_labels(label_path)

        with Image.open(img_path) as img:
            img_w, img_h = img.size

        preds = []

        if is_sahi:
            from sahi.predict import get_sliced_prediction

            sahi_result = get_sliced_prediction(
                image=str(img_path),
                detection_model=detection_model,
                slice_height=slice_height,
                slice_width=slice_width,
                overlap_height_ratio=args.sahi_overlap,
                overlap_width_ratio=args.sahi_overlap,
                postprocess_type="NMS",
                postprocess_match_metric="IOS",
                postprocess_match_threshold=0.50,
                verbose=False,
            )

            for obj in sahi_result.object_prediction_list:
                cid = obj.category.id
                conf_val = float(obj.score.value) if obj.score else args.conf
                if obj.mask is not None:
                    try:
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
                        if candidate_polys:
                            poly = max(candidate_polys, key=lambda p: p.area)
                            preds.append(
                                {
                                    "class_id": int(cid),
                                    "poly": poly,
                                    "conf": conf_val,
                                    "matched": False,
                                }
                            )
                    except Exception:
                        continue
        else:
            results = ultralytics_model.predict(
                source=str(img_path),
                imgsz=args.imgsz,
                verbose=False,
                conf=args.conf,
                device=args.device,
            )
            result = results[0]
            if result.masks is not None:
                for cls_tensor, conf_tensor, seg_coords in zip(
                    result.boxes.cls, result.boxes.conf, result.masks.xyn
                ):
                    try:
                        poly = Polygon(seg_coords)
                        if poly.is_valid and poly.area > 0:
                            preds.append(
                                {
                                    "class_id": int(cls_tensor.item()),
                                    "poly": poly,
                                    "conf": float(conf_tensor.item()),
                                    "matched": False,
                                }
                            )
                    except Exception:
                        continue

        # Sort predictions by confidence score descending
        preds.sort(key=lambda x: x["conf"], reverse=True)

        # Match predictions to GTs greedy by IoU >= 0.50
        for pred in preds:
            best_iou = 0.0
            best_gt_idx = -1
            for idx, gt in enumerate(gts):
                if not gt["matched"] and gt["class_id"] == pred["class_id"]:
                    iou = calculate_iou(gt["poly"], pred["poly"])
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = idx

            if best_iou >= args.iou_thresh and best_gt_idx != -1:
                pred["matched"] = True
                gts[best_gt_idx]["matched"] = True
                stats[pred["class_id"]]["tp"] += 1
            else:
                stats[pred["class_id"]]["fp"] += 1

        # Count unmatched GTs as False Negatives
        for gt in gts:
            stats[gt["class_id"]]["total_gt"] += 1
            if not gt["matched"]:
                stats[gt["class_id"]]["fn"] += 1

        # Draw visual inspection outputs
        draw_visualizations(img_path, gts, preds, mode_name, save_dir, img_w, img_h)

    return stats


def print_report(mode_name, stats):
    print("\n" + "=" * 95)
    print(f" 📊 {mode_name.upper()} - FORMAL GROUND TRUTH EVALUATION REPORT")
    print("=" * 95)
    header = f"{'Class':<18} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10} | {'TP':<6} | {'FP':<6} | {'FN':<6} | GT Total"
    print(header)
    print("-" * 95)

    tot_tp, tot_fp, tot_fn, tot_gt = 0, 0, 0, 0

    for cid in sorted(CLASS_NAMES.keys()):
        cname = CLASS_NAMES[cid]
        s = stats[cid]
        tp, fp, fn, gt_tot = s["tp"], s["fp"], s["fn"], s["total_gt"]
        tot_tp += tp
        tot_fp += fp
        tot_fn += fn
        tot_gt += gt_tot

        prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        print(
            f"{cname:<18} | {prec:>8.1f}% | {rec:>8.1f}% | {f1:>8.1f}% | {tp:<6} | {fp:<6} | {fn:<6} | {gt_tot}"
        )

    print("-" * 95)
    overall_prec = (tot_tp / (tot_tp + tot_fp) * 100) if (tot_tp + tot_fp) > 0 else 0.0
    overall_rec = (tot_tp / (tot_tp + tot_fn) * 100) if (tot_tp + tot_fn) > 0 else 0.0
    overall_f1 = (
        (2 * overall_prec * overall_rec / (overall_prec + overall_rec))
        if (overall_prec + overall_rec) > 0
        else 0.0
    )
    print(
        f"{'OVERALL TOTAL':<18} | {overall_prec:>8.1f}% | {overall_rec:>8.1f}% | {overall_f1:>8.1f}% | {tot_tp:<6} | {tot_fp:<6} | {tot_fn:<6} | {tot_gt}"
    )
    print("=" * 95)

    return {
        "tp": tot_tp,
        "fp": tot_fp,
        "fn": tot_fn,
        "gt": tot_gt,
        "precision": overall_prec,
        "recall": overall_rec,
        "f1": overall_f1,
    }


def print_comparison_table(all_stats):
    """Print a side-by-side comparison of all evaluated modes."""
    print("\n" + "=" * 120)
    print(" 📊 HEAD-TO-HEAD COMPARISON: Direct 1024 vs SAHI 1024 vs SAHI 640")
    print("=" * 120)

    modes = list(all_stats.keys())

    # Per-class comparison
    header = f"{'Class':<18}"
    for mode in modes:
        header += f" | {mode.upper():>22}"
    print(header)
    print("-" * 120)

    for cid in sorted(CLASS_NAMES.keys()):
        cname = CLASS_NAMES[cid]
        row = f"{cname:<18}"
        for mode in modes:
            s = all_stats[mode][cid]
            tp, fp, fn = s["tp"], s["fp"], s["fn"]
            prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
            rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            row += f" | P:{prec:>5.1f} R:{rec:>5.1f} F1:{f1:>5.1f}"
        print(row)

    print("-" * 120)

    # Overall comparison
    row = f"{'OVERALL':<18}"
    for mode in modes:
        s = all_stats[mode]
        tot_tp = sum(s[cid]["tp"] for cid in CLASS_NAMES.keys())
        tot_fp = sum(s[cid]["fp"] for cid in CLASS_NAMES.keys())
        tot_fn = sum(s[cid]["fn"] for cid in CLASS_NAMES.keys())
        prec = (tot_tp / (tot_tp + tot_fp) * 100) if (tot_tp + tot_fp) > 0 else 0.0
        rec = (tot_tp / (tot_tp + tot_fn) * 100) if (tot_tp + tot_fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        row += f" | P:{prec:>5.1f} R:{rec:>5.1f} F1:{f1:>5.1f}"
    print(row)

    # Delta summary
    print("-" * 120)
    if "direct1024" in all_stats and "sahi1024" in all_stats and "sahi640" in all_stats:
        d = all_stats["direct1024"]
        s1 = all_stats["sahi1024"]
        s6 = all_stats["sahi640"]

        for label, stats_obj in [
            ("Direct 1024", d),
            ("SAHI 1024", s1),
            ("SAHI 640", s6),
        ]:
            tot_tp = sum(stats_obj[cid]["tp"] for cid in CLASS_NAMES.keys())
            tot_fp = sum(stats_obj[cid]["fp"] for cid in CLASS_NAMES.keys())
            tot_fn = sum(stats_obj[cid]["fn"] for cid in CLASS_NAMES.keys())
            print(f"{label}: TP={tot_tp}, FP={tot_fp}, FN={tot_fn}")

    print("=" * 120)


def main():
    parser = argparse.ArgumentParser(
        description="Formal Ground-Truth Evaluation: Direct 1024 vs SAHI 1024 vs SAHI 640"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to trained .pt model"
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/processed/stage2",
        help="Dataset root path",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Dataset split to evaluate ('test' or 'val')",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="runs/test_gt_eval_viz",
        help="Folder to save GT vs Prediction rendered images",
    )
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument(
        "--iou_thresh", type=float, default=0.50, help="IoU TP matching threshold"
    )
    parser.add_argument("--device", type=str, default="mps", help="Inference device")
    parser.add_argument(
        "--imgsz", type=int, default=1024, help="Direct inference image size"
    )
    parser.add_argument(
        "--sahi_overlap", type=float, default=0.25, help="SAHI patch overlap ratio"
    )
    parser.add_argument(
        "--skip_direct", action="store_true", help="Skip Direct 1024 evaluation"
    )
    parser.add_argument(
        "--skip_sahi1024", action="store_true", help="Skip SAHI 1024 evaluation"
    )
    parser.add_argument(
        "--skip_sahi640", action="store_true", help="Skip SAHI 640 evaluation"
    )
    args = parser.parse_args()

    split_dir = Path(args.data_dir) / args.split
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"

    # Fallback to 'val' if 'test' folder does not exist or has no images
    if not images_dir.exists() or not list(images_dir.glob("*.*")):
        print(
            f"[!] Split '{args.split}' not found or empty. Falling back to 'val' split..."
        )
        split_dir = Path(args.data_dir) / "val"
        images_dir = split_dir / "images"
        labels_dir = split_dir / "labels"

    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
    all_images = []
    for ext in image_extensions:
        all_images.extend(list(images_dir.glob(ext)))

    print(f"[*] Found {len(all_images)} ground-truth labeled images in '{split_dir}'")
    print(f"[*] Rendered GT vs Prediction images will be saved in '{args.output_dir}'")
    print(f"[*] Confidence threshold: {args.conf} | IoU threshold: {args.iou_thresh}")
    print(f"[*] SAHI overlap ratio: {args.sahi_overlap}")
    print("-" * 80)

    all_stats = {}

    # 1. Evaluate Direct 1024
    if not args.skip_direct:
        direct_model = YOLO(args.model)
        d1024_stats = evaluate_mode(
            "direct1024",
            all_images,
            labels_dir,
            args,
            ultralytics_model=direct_model,
        )
        # summary = print_report("Direct 1024", d1024_stats)
        all_stats["direct1024"] = d1024_stats
        print("\n[⏱] Direct 1024 complete.")

    # 2. Evaluate SAHI 1024
    if not args.skip_sahi1024:
        from sahi import AutoDetectionModel

        sahi_detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model_path=args.model,
            confidence_threshold=args.conf,
            device=args.device,
        )
        sahi1024_stats = evaluate_mode(
            "sahi1024",
            all_images,
            labels_dir,
            args,
            detection_model=sahi_detection_model,
            slice_height=1024,
            slice_width=1024,
        )
        # summary = print_report("SAHI 1024", sahi1024_stats)
        all_stats["sahi1024"] = sahi1024_stats
        print("\n[⏱] SAHI 1024 complete.")

    # 3. Evaluate SAHI 640
    if not args.skip_sahi640:
        # Reuse existing model if already loaded, otherwise create new one
        if args.skip_sahi1024:
            from sahi import AutoDetectionModel

            sahi_detection_model = AutoDetectionModel.from_pretrained(
                model_type="yolov8",
                model_path=args.model,
                confidence_threshold=args.conf,
                device=args.device,
            )

        sahi640_stats = evaluate_mode(
            "sahi640",
            all_images,
            labels_dir,
            args,
            detection_model=sahi_detection_model,
            slice_height=640,
            slice_width=640,
        )
        # summary = print_report("SAHI 640", sahi640_stats)
        all_stats["sahi640"] = sahi640_stats
        print("\n[⏱] SAHI 640 complete.")

    if len(all_stats) > 1:
        print_comparison_table(all_stats)

    print("\n[*] All evaluations complete. Visualizations saved to:", args.output_dir)


if __name__ == "__main__":
    main()
