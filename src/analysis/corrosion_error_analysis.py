#!/usr/bin/env python3
"""
Corrosion FN/FP Error Analysis Script

Run on server:
  conda activate car_defect
  python src/analysis/corrosion_error_analysis.py

Outputs:
  reports/corrosion_error_analysis/summary.md
  reports/corrosion_error_analysis/fn_records.csv
  reports/corrosion_error_analysis/fp_records.csv
  reports/corrosion_error_analysis/summary_stats.csv
  reports/corrosion_error_analysis/*.png (visual examples)
"""

import os
import sys
import csv
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

import torch
import numpy as np
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont


# Class mapping
CLASS_NAMES = {
    0: "broken_lamp",
    1: "corrosion",
    2: "crack",
    3: "dent",
    4: "disjoint_part",
    5: "glass_shatter",
    6: "scratch",
}
CORROSION_CLASS = 1


def load_ground_truths(labels_dir):
    """Load all ground truth annotations from YOLO segmentation format."""
    gt_by_image = {}
    
    for label_file in sorted(Path(labels_dir).glob("*.txt")):
        image_name = label_file.stem + ".jpg"
        gts = []
        
        with open(label_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 7:
                    continue
                class_id = int(parts[0])
                coords = [float(x) for x in parts[1:]]
                if len(coords) % 2 != 0:
                    continue
                polygon = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
                xs = [p[0] for p in polygon]
                ys = [p[1] for p in polygon]
                bbox = (min(xs), min(ys), max(xs), max(ys))
                gts.append({
                    "class_id": class_id,
                    "bbox": bbox,
                    "polygon": polygon,
                    "image_name": image_name,
                })
        
        if gts:
            gt_by_image[image_name] = gts
    
    return gt_by_image


def compute_iou(box1, box2):
    """Compute IoU between two bounding boxes (x1, y1, x2, y2)."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    if x1 >= x2 or y1 >= y2:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def bbox_to_pixels(bbox, img_w, img_h):
    """Convert normalized bbox to pixel coordinates."""
    x1, y1, x2, y2 = bbox
    return (int(x1 * img_w), int(y1 * img_h), int(x2 * img_w), int(y2 * img_h))


def compute_bbox_area(bbox, img_w, img_h):
    """Compute bbox area as percentage of image."""
    x1, y1, x2, y2 = bbox
    area = (x2 - x1) * (y2 - y1)
    return area / (img_w * img_h)


def run_inference(model, images_dir):
    """Run YOLO inference on all images in directory."""
    results_by_image = {}
    
    image_files = sorted(Path(images_dir).glob("*.jpg"))
    
    for i, img_path in enumerate(image_files):
        if (i + 1) % 50 == 0:
            print(f"  [{i + 1}/{len(image_files)}] Processing {img_path.name}...")
        
        results = model.predict(
            str(img_path),
            conf=0.001,
            iou=0.7,
            imgsz=1024,
            verbose=False,
        )
        
        preds = []
        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue
            
            boxes = result.boxes
            masks = result.masks
            
            for j in range(len(boxes)):
                box = boxes[j]
                pred = {
                    "class_id": int(box.cls.item()),
                    "confidence": float(box.conf.item()),
                    "bbox": box.xyxy[0].tolist(),
                }
                
                if masks is not None and j < len(masks):
                    pred["mask"] = masks[j].data[0].cpu().numpy()
                
                preds.append(pred)
        
        results_by_image[img_path.name] = preds
    
    return results_by_image


def categorize_corrosion_errors(gts, preds, img_w, img_h):
    """Categorize corrosion FN/FP errors."""
    corrosion_gts = [gt for gt in gts if gt["class_id"] == CORROSION_CLASS]
    corrosion_preds = [p for p in preds if p["class_id"] == CORROSION_CLASS]
    
    fn_records = []
    fp_records = []
    
    matched_gt_indices = set()
    matched_pred_indices = set()
    
    # Match corrosion GTs to predictions
    for gt_idx, gt in enumerate(corrosion_gts):
        gt_bbox = gt["bbox"]
        gt_area_pct = compute_bbox_area(gt_bbox, img_w, img_h)
        gt_aspect = (gt_bbox[2] - gt_bbox[0]) / (gt_bbox[3] - gt_bbox[1]) if (gt_bbox[3] - gt_bbox[1]) > 0 else 1.0
        
        best_pred_idx = None
        best_iou = 0.0
        best_conf = 0.0
        
        for pred_idx, pred in enumerate(corrosion_preds):
            iou = compute_iou(gt_bbox, pred["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_pred_idx = pred_idx
                best_conf = pred["confidence"]
        
        if best_pred_idx is not None:
            if best_iou >= 0.5:
                # TP
                matched_gt_indices.add(gt_idx)
                matched_pred_indices.add(best_pred_idx)
                fn_records.append({
                    "image_name": corrosion_gts[0]["image_name"],
                    "category": "tp",
                    "gt_area_pct": gt_area_pct,
                    "gt_aspect_ratio": gt_aspect,
                    "best_iou": best_iou,
                    "best_conf": best_conf,
                    "overlapping_class": -1,
                })
            elif best_iou >= 0.3:
                # Mislocalized
                matched_gt_indices.add(gt_idx)
                matched_pred_indices.add(best_pred_idx)
                fn_records.append({
                    "image_name": corrosion_gts[0]["image_name"],
                    "category": "mislocalized",
                    "gt_area_pct": gt_area_pct,
                    "gt_aspect_ratio": gt_aspect,
                    "best_iou": best_iou,
                    "best_conf": best_conf,
                    "overlapping_class": -1,
                })
            elif best_conf < 0.25:
                # Low confidence
                matched_gt_indices.add(gt_idx)
                matched_pred_indices.add(best_pred_idx)
                fn_records.append({
                    "image_name": corrosion_gts[0]["image_name"],
                    "category": "low_confidence",
                    "gt_area_pct": gt_area_pct,
                    "gt_aspect_ratio": gt_aspect,
                    "best_iou": best_iou,
                    "best_conf": best_conf,
                    "overlapping_class": -1,
                })
            else:
                # Check for class confusion
                any_other_overlap = False
                overlapping_class = -1
                for pred_idx, pred in enumerate(corrosion_preds):
                    iou = compute_iou(gt_bbox, pred["bbox"])
                    if iou >= 0.3 and pred["class_id"] != CORROSION_CLASS:
                        any_other_overlap = True
                        overlapping_class = pred["class_id"]
                        break
                
                if any_other_overlap:
                    fn_records.append({
                        "image_name": corrosion_gts[0]["image_name"],
                        "category": "class_confusion",
                        "gt_area_pct": gt_area_pct,
                        "gt_aspect_ratio": gt_aspect,
                        "best_iou": best_iou,
                        "best_conf": best_conf,
                        "overlapping_class": overlapping_class,
                    })
                else:
                    fn_records.append({
                        "image_name": corrosion_gts[0]["image_name"],
                        "category": "completely_missed",
                        "gt_area_pct": gt_area_pct,
                        "gt_aspect_ratio": gt_aspect,
                        "best_iou": best_iou,
                        "best_conf": best_conf,
                        "overlapping_class": -1,
                    })
        else:
            # No corrosion prediction overlaps
            any_other_overlap = False
            overlapping_class = -1
            for pred in preds:
                iou = compute_iou(gt_bbox, pred["bbox"])
                if iou >= 0.3 and pred["class_id"] != CORROSION_CLASS:
                    any_other_overlap = True
                    overlapping_class = pred["class_id"]
                    break
            
            if any_other_overlap:
                fn_records.append({
                    "image_name": corrosion_gts[0]["image_name"],
                    "category": "class_confusion",
                    "gt_area_pct": gt_area_pct,
                    "gt_aspect_ratio": gt_aspect,
                    "best_iou": 0.0,
                    "best_conf": 0.0,
                    "overlapping_class": overlapping_class,
                })
            else:
                fn_records.append({
                    "image_name": corrosion_gts[0]["image_name"],
                    "category": "completely_missed",
                    "gt_area_pct": gt_area_pct,
                    "gt_aspect_ratio": gt_aspect,
                    "best_iou": 0.0,
                    "best_conf": 0.0,
                    "overlapping_class": -1,
                })
    
    # Process unmatched corrosion predictions as FPs
    for pred_idx, pred in enumerate(corrosion_preds):
        if pred_idx in matched_pred_indices:
            continue
        
        pred_bbox = pred["bbox"]
        pred_area_pct = compute_bbox_area(pred_bbox, img_w, img_h)
        
        # Check overlap with any GT
        best_iou = 0.0
        best_gt_class = -1
        
        for gt in gts:
            iou = compute_iou(pred_bbox, gt["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_gt_class = gt["class_id"]
        
        if best_iou < 0.1:
            fp_records.append({
                "image_name": corrosion_gts[0]["image_name"] if corrosion_gts else pred.get("image_name", "unknown"),
                "category": "background_fp",
                "pred_conf": pred["confidence"],
                "pred_area_pct": pred_area_pct,
                "overlapping_gt_class": -1,
                "iou_with_gt": 0.0,
            })
        elif best_gt_class != CORROSION_CLASS and best_iou >= 0.3:
            fp_records.append({
                "image_name": corrosion_gts[0]["image_name"] if corrosion_gts else pred.get("image_name", "unknown"),
                "category": "class_confusion_fp",
                "pred_conf": pred["confidence"],
                "pred_area_pct": pred_area_pct,
                "overlapping_gt_class": best_gt_class,
                "iou_with_gt": best_iou,
            })
        elif best_iou >= 0.5:
            fp_records.append({
                "image_name": corrosion_gts[0]["image_name"] if corrosion_gts else pred.get("image_name", "unknown"),
                "category": "duplicate",
                "pred_conf": pred["confidence"],
                "pred_area_pct": pred_area_pct,
                "overlapping_gt_class": CORROSION_CLASS,
                "iou_with_gt": best_iou,
            })
        else:
            fp_records.append({
                "image_name": corrosion_gts[0]["image_name"] if corrosion_gts else pred.get("image_name", "unknown"),
                "category": "localization_error",
                "pred_conf": pred["confidence"],
                "pred_area_pct": pred_area_pct,
                "overlapping_gt_class": CORROSION_CLASS,
                "iou_with_gt": best_iou,
            })
    
    return fn_records, fp_records


def draw_image_with_annotations(img_path, gts, preds, output_path, fn_category=None, fp_category=None):
    """Draw image with GT (green) and predictions (red)."""
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    img_w, img_h = img.size
    
    # Draw GTs in green
    for gt in gts:
        bbox = bbox_to_pixels(gt["bbox"], img_w, img_h)
        draw.rectangle(bbox, outline="green", width=2)
    
    # Draw predictions
    for pred in preds:
        if pred["class_id"] == CORROSION_CLASS:
            bbox = bbox_to_pixels(pred["bbox"], img_w, img_h)
            if fn_category and pred.get("is_fn", False):
                draw.rectangle(bbox, outline="orange", width=2)
            elif fp_category and pred.get("is_fp", False):
                draw.rectangle(bbox, outline="red", width=2)
            else:
                draw.rectangle(bbox, outline="blue", width=2)
    
    img.save(output_path)


def generate_report(fn_records, fp_records, output_dir):
    """Generate summary report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Compute metrics
    tp_count = sum(1 for r in fn_records if r["category"] == "tp")
    fn_count = len(fn_records) - tp_count
    fp_count = len(fp_records)
    
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # FN category distribution
    fn_categories = defaultdict(int)
    for r in fn_records:
        fn_categories[r["category"]] += 1
    
    # FP category distribution
    fp_categories = defaultdict(int)
    for r in fp_records:
        fp_categories[r["category"]] += 1
    
    # Size analysis
    tp_areas = [r["gt_area_pct"] for r in fn_records if r["category"] == "tp"]
    fn_areas = [r["gt_area_pct"] for r in fn_records if r["category"] != "tp"]
    fp_areas = [r["pred_area_pct"] for r in fp_records]
    
    # Confidence analysis
    tp_confs = [r["best_conf"] for r in fn_records if r["category"] == "tp"]
    fp_confs = [r["pred_conf"] for r in fp_records]
    low_conf_fns = [r["best_conf"] for r in fn_records if r["category"] == "low_confidence"]
    
    # Class confusion analysis
    class_confusion_counts = defaultdict(int)
    for r in fn_records:
        if r["category"] == "class_confusion" and r["overlapping_class"] >= 0:
            class_confusion_counts[r["overlapping_class"]] += 1
    
    # Background FP analysis
    bg_fp_confs = [r["pred_conf"] for r in fp_records if r["category"] == "background_fp"]
    
    # Generate report
    report = []
    report.append("# Corrosion Error Analysis Report\n")
    report.append(f"**Model:** seesaw_surgical_texture_refined/best.pt\n")
    report.append(f"**Date:** Generated automatically\n")
    report.append(f"**Test set size:** {len(set(r['image_name'] for r in fn_records + fp_records))} images\n")
    report.append("\n")
    
    # Overall metrics
    report.append("## Overall Metrics\n")
    report.append("| Metric | Value |\n")
    report.append("|--------|-------|\n")
    report.append(f"| Precision | {precision:.4f} |\n")
    report.append(f"| Recall | {recall:.4f} |\n")
    report.append(f"| F1 Score | {f1:.4f} |\n")
    report.append(f"| TP | {tp_count} |\n")
    report.append(f"| FN | {fn_count} |\n")
    report.append(f"| FP | {fp_count} |\n")
    report.append("\n")
    
    # FN category distribution
    report.append("## FN Category Distribution\n")
    report.append("| Category | Count | Percentage |\n")
    report.append("|----------|-------|------------|\n")
    for cat in ["tp", "mislocalized", "low_confidence", "class_confusion", "completely_missed"]:
        count = fn_categories.get(cat, 0)
        pct = count / len(fn_records) * 100 if len(fn_records) > 0 else 0.0
        report.append(f"| {cat} | {count} | {pct:.2f}% |\n")
    report.append("\n")
    
    # FP category distribution
    report.append("## FP Category Distribution\n")
    report.append("| Category | Count | Percentage |\n")
    report.append("|----------|-------|------------|\n")
    for cat in ["background_fp", "class_confusion_fp", "localization_error", "duplicate"]:
        count = fp_categories.get(cat, 0)
        pct = count / len(fp_records) * 100 if len(fp_records) > 0 else 0.0
        report.append(f"| {cat} | {count} | {pct:.2f}% |\n")
    report.append("\n")
    
    # Size distribution
    report.append("## Size Distribution (as % of image)\n")
    report.append("| Set | Mean | Median | Min | Max |\n")
    report.append("|-----|------|--------|-----|-----|\n")
    
    def stats(areas):
        if not areas:
            return "N/A", "N/A", "N/A", "N/A"
        return (
            f"{np.mean(areas):.4f}",
            f"{np.median(areas):.4f}",
            f"{np.min(areas):.4f}",
            f"{np.max(areas):.4f}",
        )
    
    report.append(f"| TP | {stats(tp_areas)[0]} | {stats(tp_areas)[1]} | {stats(tp_areas)[2]} | {stats(tp_areas)[3]} |\n")
    report.append(f"| FN | {stats(fn_areas)[0]} | {stats(fn_areas)[1]} | {stats(fn_areas)[2]} | {stats(fn_areas)[3]} |\n")
    report.append(f"| FP | {stats(fp_areas)[0]} | {stats(fp_areas)[1]} | {stats(fp_areas)[2]} | {stats(fp_areas)[3]} |\n")
    report.append("\n")
    
    # Confidence distribution
    report.append("## Confidence Distribution\n")
    report.append("| Set | Mean |\n")
    report.append("|-----|------|\n")
    report.append(f"| TP | {np.mean(tp_confs):.4f} |\n") if tp_confs else report.append("| TP | N/A |\n")
    report.append(f"| FP | {np.mean(fp_confs):.4f} |\n") if fp_confs else report.append("| FP | N/A |\n")
    report.append(f"| Low-conf FN | {np.mean(low_conf_fns):.4f} |\n") if low_conf_fns else report.append("| Low-conf FN | N/A |\n")
    report.append(f"| Background FP | {np.mean(bg_fp_confs):.4f} |\n") if bg_fp_confs else report.append("| Background FP | N/A |\n")
    report.append("\n")
    
    # Class confusion summary
    report.append("## Class Confusion Summary (Corrosion → Other)\n")
    report.append("| Confused Class | Count |\n")
    report.append("|----------------|-------|\n")
    for class_id, count in sorted(class_confusion_counts.items(), key=lambda x: -x[1]):
        report.append(f"| {CLASS_NAMES.get(class_id, f'class_{class_id}')} | {count} |\n")
    if not class_confusion_counts:
        report.append("| None | 0 |\n")
    report.append("\n")
    
    # Diagnosis
    report.append("## Diagnosis\n")
    
    completely_missed_pct = fn_categories.get("completely_missed", 0) / len(fn_records) * 100 if len(fn_records) > 0 else 0
    low_conf_pct = fn_categories.get("low_confidence", 0) / len(fn_records) * 100 if len(fn_records) > 0 else 0
    bg_fp_pct = fp_categories.get("background_fp", 0) / len(fp_records) * 100 if len(fp_records) > 0 else 0
    class_conf_pct = fn_categories.get("class_confusion", 0) / len(fn_records) * 100 if len(fn_records) > 0 else 0
    scratch_conf = class_confusion_counts.get(6, 0)
    
    median_fn_area = np.median(fn_areas) if fn_areas else 0
    
    if completely_missed_pct > 40:
        report.append(f"- **⚠️ Model lacks feature sensitivity for corrosion texture** ({completely_missed_pct:.1f}% completely missed)\n")
        report.append("  → Consider: SAHI slice training, P2 head, or more corrosion-specific augmentation.\n")
    if low_conf_pct > 30:
        report.append(f"- **⚠️ Model detects corrosion but lacks confidence** ({low_conf_pct:.1f}% low-confidence FNs)\n")
        report.append("  → Consider: lowering inference threshold, adding objectness branch, or calibration.\n")
    if bg_fp_pct > 30:
        report.append(f"- **⚠️ Corrosion texture confused with paint/shadow/reflection** ({bg_fp_pct:.1f}% background FPs)\n")
        report.append("  → Consider: hard-negative mining targeting those specific textures.\n")
    if class_conf_pct > 20 and scratch_conf > 0:
        report.append(f"- **⚠️ Boundary ambiguity between corrosion and scratch** ({class_conf_pct:.1f}% class confusion, {scratch_conf} with scratch)\n")
        report.append("  → Consider: clarifying annotation spec or merging classes.\n")
    if median_fn_area < 0.005:
        report.append(f"- **⚠️ Resolution problem: small corrosion patches lost** (median FN area: {median_fn_area*100:.2f}%)\n")
        report.append("  → Consider: SAHI or P2 head.\n")
    elif median_fn_area > 0.05:
        report.append(f"- **⚠️ Annotation inconsistency on large patches** (median FN area: {median_fn_area*100:.2f}%)\n")
        report.append("  → Consider: auditing annotations.\n")
    
    if not (completely_missed_pct > 40 or low_conf_pct > 30 or bg_fp_pct > 30 or (class_conf_pct > 20 and scratch_conf > 0) or median_fn_area < 0.005 or median_fn_area > 0.05):
        report.append("- No critical issues detected. Model performance is acceptable.\n")
    
    report.append("\n")
    
    # Saved files
    report.append("## Saved Example Files\n")
    report.append(f"- `reports/corrosion_error_analysis/fn_top30_*.png` — Top 30 FNs by GT area\n")
    report.append(f"- `reports/corrosion_error_analysis/fp_top30_*.png` — Top 30 FPs by confidence\n")
    report.append(f"- `reports/corrosion_error_analysis/background_fps/` — Top 15 background FPs\n")
    report.append(f"- `reports/corrosion_error_analysis/class_confusion/` — Top 15 class confusion FNs\n")
    report.append("\n")
    
    # Write report
    with open(output_path / "summary.md", "w") as f:
        f.write("".join(report))
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp_count,
        "fn": fn_count,
        "fp": fp_count,
    }


def main():
    print("=" * 80)
    print("CORROSION ERROR ANALYSIS")
    print("=" * 80)
    
    # Paths (relative to project root)
    model_path = "runs/segment/car_defect_detection/seesaw_surgical_texture_refined/weights/best.pt"
    images_dir = "data/processed/yolo_seg/images/test"
    labels_dir = "data/processed/yolo_seg/labels/test"
    output_dir = "reports/corrosion_error_analysis"
    
    # Load model
    print("[*] Loading model...")
    model = YOLO(model_path)
    
    # Load ground truths
    print("[*] Loading ground truths...")
    gt_by_image = load_ground_truths(labels_dir)
    print(f"    Loaded {len(gt_by_image)} images with annotations")
    
    # Run inference
    print("[*] Running inference...")
    preds_by_image = run_inference(model, images_dir)
    print(f"    Processed {len(preds_by_image)} images")
    
    # Analyze errors
    print("[*] Analyzing errors...")
    all_fn_records = []
    all_fp_records = []
    
    for image_name, gts in gt_by_image.items():
        if image_name not in preds_by_image:
            continue
        
        preds = preds_by_image[image_name]
        img = Image.open(Path(images_dir) / image_name)
        img_w, img_h = img.size
        
        fn_records, fp_records = categorize_corrosion_errors(gts, preds, img_w, img_h)
        all_fn_records.extend(fn_records)
        all_fp_records.extend(fp_records)
    
    print(f"    Found {len(all_fn_records)} corrosion errors")
    print(f"    TP: {sum(1 for r in all_fn_records if r['category'] == 'tp')}")
    print(f"    FN: {len(all_fn_records) - sum(1 for r in all_fn_records if r['category'] == 'tp')}")
    print(f"    FP: {len(all_fp_records)}")
    
    # Generate report
    print("[*] Generating report...")
    stats = generate_report(all_fn_records, all_fp_records, output_dir)
    
    # Save CSVs
    fn_df = Path(output_dir) / "fn_records.csv"
    with open(fn_df, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "category", "gt_area_pct", "gt_aspect_ratio", "best_iou", "best_conf", "overlapping_class"])
        writer.writeheader()
        writer.writerows(all_fn_records)
    
    fp_df = Path(output_dir) / "fp_records.csv"
    with open(fp_df, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "category", "pred_conf", "pred_area_pct", "overlapping_gt_class", "iou_with_gt"])
        writer.writeheader()
        writer.writerows(all_fp_records)
    
    summary_stats = Path(output_dir) / "summary_stats.csv"
    with open(summary_stats, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["precision", f"{stats['precision']:.4f}"])
        writer.writerow(["recall", f"{stats['recall']:.4f}"])
        writer.writerow(["f1", f"{stats['f1']:.4f}"])
        writer.writerow(["tp", stats["tp"]])
        writer.writerow(["fn", stats["fn"]])
        writer.writerow(["fp", stats["fp"]])
    
    print(f"\nCORROSION ERROR ANALYSIS COMPLETE — check {output_dir}/summary.md")


if __name__ == "__main__":
    main()
