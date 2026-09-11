"""Clean-image False Positive Rate (FPR) metrics.

Measures how often the model hallucinates defects on clean (defect-free) car
images. This is the critical production metric: a model that flags clean cars
as damaged will erode operator trust and slow down the inspection line.

Design: This is a pure metrics module. It receives predictions that have
already been computed by the inference pipeline (sahi_eval.py), and computes
FPR statistics. This separation of concerns keeps inference and metrics
independent.

References:
    - eval.md, Module 17: Confidence Thresholding and Class Filtering
    - eval.md, Commandment #1: Aggregate Metrics Lie for Rare Events
"""

import numpy as np
from typing import List, Dict, Optional


def compute_clean_fpr(
    all_predictions: List[np.ndarray],
    conf_threshold: float = 0.25,
    class_names: Optional[List[str]] = None,
) -> Dict:
    """Compute false positive rate on clean (defect-free) images.

    A clean image is considered a "false positive" if it produces at least
    one detection with confidence >= conf_threshold. Since clean images have
    no ground truth defects, ANY detection is a false positive.

    Args:
        all_predictions: List of [N_i, 6] arrays per image, where columns are
            [x1, y1, x2, y2, score, class_id]. Empty images have shape (0, 6).
        conf_threshold: Minimum confidence for a detection to count.
        class_names: Optional list of class names for per-class breakdown.

    Returns:
        Dict with:
            'total_clean_images': int
            'images_with_fp': int - number of clean images with >=1 detection
            'fpr_percent': float - (images_with_fp / total) * 100
            'total_false_positives': int - total detection count across all images
            'avg_fp_per_fp_image': float - mean detections per FP image
            'avg_fp_confidence': float - mean confidence of all FPs
            'fp_by_class': Dict[str, int] - FP count per class
            'fp_confidence_by_class': Dict[str, float] - mean FP conf per class
            'max_fp_count_single_image': int - worst-case FP count
    """
    total_images = len(all_predictions)
    images_with_fp = 0
    total_false_positives = 0
    all_fp_confidences = []
    fp_per_image_counts = []

    num_classes = len(class_names) if class_names else 0
    fp_by_class = {}
    fp_conf_by_class = {}

    for pred in all_predictions:
        if pred is None or len(pred) == 0:
            continue

        # Filter by confidence threshold
        if pred.shape[1] >= 5:
            scores = pred[:, 4]
            mask = scores >= conf_threshold
            filtered = pred[mask]
        else:
            filtered = pred

        if len(filtered) == 0:
            continue

        # This clean image has false positives
        images_with_fp += 1
        num_fp = len(filtered)
        total_false_positives += num_fp
        fp_per_image_counts.append(num_fp)
        all_fp_confidences.extend(filtered[:, 4].tolist())

        # Per-class breakdown
        if filtered.shape[1] >= 6 and num_classes > 0:
            class_ids = filtered[:, 5].astype(int)
            for cls_id in class_ids:
                if cls_id < num_classes:
                    cls_name = class_names[cls_id]
                    fp_by_class[cls_name] = fp_by_class.get(cls_name, 0) + 1

    # Compute FPR
    fpr_percent = (images_with_fp / total_images * 100) if total_images > 0 else 0.0

    # Compute averages
    avg_fp_per_fp_image = (
        np.mean(fp_per_image_counts) if len(fp_per_image_counts) > 0 else 0.0
    )
    avg_fp_confidence = (
        np.mean(all_fp_confidences) if len(all_fp_confidences) > 0 else 0.0
    )
    max_fp_count = max(fp_per_image_counts) if fp_per_image_counts else 0

    # Per-class average confidence
    if class_names and all_fp_confidences:
        for pred in all_predictions:
            if pred is None or len(pred) == 0 or pred.shape[1] < 6:
                continue
            scores = pred[:, 4]
            mask = scores >= conf_threshold
            filtered = pred[mask]
            if len(filtered) == 0:
                continue
            class_ids = filtered[:, 5].astype(int)
            for i, cls_id in enumerate(class_ids):
                if cls_id < num_classes:
                    cls_name = class_names[cls_id]
                    if cls_name not in fp_conf_by_class:
                        fp_conf_by_class[cls_name] = []
                    fp_conf_by_class[cls_name].append(float(filtered[i, 4]))

        fp_conf_by_class = {
            k: float(np.mean(v)) for k, v in fp_conf_by_class.items() if len(v) > 0
        }

    return {
        "total_clean_images": total_images,
        "images_with_fp": images_with_fp,
        "fpr_percent": round(fpr_percent, 2),
        "total_false_positives": total_false_positives,
        "avg_fp_per_fp_image": round(float(avg_fp_per_fp_image), 2),
        "avg_fp_confidence": round(float(avg_fp_confidence), 4),
        "fp_by_class": fp_by_class,
        "fp_confidence_by_class": fp_conf_by_class,
        "max_fp_count_single_image": max_fp_count,
        "conf_threshold": conf_threshold,
    }


def format_clean_fpr_report(
    metrics: Dict,
    model_name: str = "Model",
) -> str:
    """Format clean FPR metrics as a human-readable Markdown report.

    Args:
        metrics: Output from compute_clean_fpr
        model_name: Name of the model being evaluated

    Returns:
        Markdown-formatted string
    """
    lines = []
    lines.append(f"## Clean Image FPR Report: {model_name}")
    lines.append("")
    lines.append(f"Confidence threshold: {metrics['conf_threshold']}")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total clean images | {metrics['total_clean_images']} |")
    lines.append(f"| Images with false positives | {metrics['images_with_fp']} |")
    lines.append(f"| **FPR (%)** | **{metrics['fpr_percent']}%** |")
    lines.append(f"| Total false positives | {metrics['total_false_positives']} |")
    lines.append(f"| Avg FPs per FP image | {metrics['avg_fp_per_fp_image']} |")
    lines.append(f"| Avg FP confidence | {metrics['avg_fp_confidence']} |")
    lines.append(
        f"| Max FPs in single image | {metrics['max_fp_count_single_image']} |"
    )
    lines.append("")

    # Per-class breakdown
    if metrics["fp_by_class"]:
        lines.append("### False Positives by Class")
        lines.append("")
        lines.append("| Class | FP Count | Avg Confidence |")
        lines.append("|-------|----------|----------------|")

        sorted_classes = sorted(
            metrics["fp_by_class"].items(), key=lambda x: x[1], reverse=True
        )
        for cls_name, count in sorted_classes:
            avg_conf = metrics["fp_confidence_by_class"].get(cls_name, 0.0)
            lines.append(f"| {cls_name} | {count} | {avg_conf:.3f} |")

        lines.append("")
        lines.append("> **Production insight**: The class with the most FPs is likely")
        lines.append("> being confused with clean-car surface features (reflections,")
        lines.append(
            "> shadows, panel seams). Consider raising its confidence threshold."
        )

    lines.append("")
    return "\n".join(lines)
