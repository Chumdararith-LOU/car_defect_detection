"""Size-bucketed evaluation metrics for object detection.

Implements Commandment #1: "Aggregate Metrics Lie for Rare Events."
Use size-bucketed recall, not just loss curves or aggregate mAP.

This module computes precision, recall, F1, and AP separately for small,
medium, and large objects, ensuring that poor performance on small defects
(like hairline cracks or corrosion spots) is not masked by good performance
on large defects (like shattered glass).

References:
    - eval.md, Module 20, Commandment #1
    - COCO evaluation protocol (size buckets: 32², 96²)
"""

import numpy as np
from typing import List, Dict, Optional

# COCO-standard size thresholds (area in pixels²)
SMALL_AREA_MAX = 32**2  # 1024 px²
MEDIUM_AREA_MAX = 96**2  # 9216 px²

SIZE_BUCKETS = {
    "small": (0, SMALL_AREA_MAX),
    "medium": (SMALL_AREA_MAX, MEDIUM_AREA_MAX),
    "large": (MEDIUM_AREA_MAX, float("inf")),
}


def compute_box_area(box: np.ndarray) -> float:
    """Compute area of a bounding box [x1, y1, x2, y2]."""
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def compute_iou(box1: np.ndarray, box2: np.ndarray) -> float:
    """Compute IoU between two boxes [x1, y1, x2, y2]."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = compute_box_area(box1)
    area2 = compute_box_area(box2)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def compute_iou_matrix(pred_boxes: np.ndarray, gt_boxes: np.ndarray) -> np.ndarray:
    """Compute pairwise IoU matrix between predictions and ground truths.

    Args:
        pred_boxes: [N, 4] array of prediction boxes [x1, y1, x2, y2]
        gt_boxes: [M, 4] array of ground truth boxes [x1, y1, x2, y2]

    Returns:
        [N, M] IoU matrix
    """
    if len(pred_boxes) == 0 or len(gt_boxes) == 0:
        return np.zeros((len(pred_boxes), len(gt_boxes)))

    iou_matrix = np.zeros((len(pred_boxes), len(gt_boxes)))
    for i in range(len(pred_boxes)):
        for j in range(len(gt_boxes)):
            iou_matrix[i, j] = compute_iou(pred_boxes[i], gt_boxes[j])
    return iou_matrix


def get_size_bucket(area: float) -> str:
    """Assign a box area to a size bucket."""
    if area < SMALL_AREA_MAX:
        return "small"
    elif area < MEDIUM_AREA_MAX:
        return "medium"
    else:
        return "large"


def match_predictions_to_ground_truths(
    pred_boxes: np.ndarray,
    pred_scores: np.ndarray,
    pred_classes: np.ndarray,
    gt_boxes: np.ndarray,
    gt_classes: np.ndarray,
    iou_threshold: float = 0.5,
) -> Dict:
    """Match predictions to ground truths using greedy IoU matching.

    Predictions are processed in descending confidence order. Each prediction
    is matched to the highest-IoU ground truth of the same class that has not
    yet been matched.

    Args:
        pred_boxes: [N, 4] prediction boxes
        pred_scores: [N] confidence scores
        pred_classes: [N] predicted class IDs
        gt_boxes: [M, 4] ground truth boxes
        gt_classes: [M] ground truth class IDs
        iou_threshold: minimum IoU for a valid match

    Returns:
        Dict with:
            'tp_mask': bool[N] - True if prediction is a true positive
            'fn_mask': bool[M] - True if ground truth is a false negative
            'pred_buckets': str[N] - size bucket per prediction
            'gt_buckets': str[M] - size bucket per ground truth
    """
    sorted_indices = np.argsort(-pred_scores)

    matched_gt = np.zeros(len(gt_boxes), dtype=bool)
    tp_mask = np.zeros(len(pred_boxes), dtype=bool)

    gt_areas = (
        np.array([compute_box_area(b) for b in gt_boxes])
        if len(gt_boxes) > 0
        else np.array([])
    )
    gt_buckets = np.array([get_size_bucket(a) for a in gt_areas])

    pred_areas = (
        np.array([compute_box_area(b) for b in pred_boxes])
        if len(pred_boxes) > 0
        else np.array([])
    )
    pred_buckets = np.array([get_size_bucket(a) for a in pred_areas])

    if len(pred_boxes) > 0 and len(gt_boxes) > 0:
        iou_matrix = compute_iou_matrix(np.array(pred_boxes), np.array(gt_boxes))
    else:
        iou_matrix = np.zeros((len(pred_boxes), len(gt_boxes)))

    for pred_idx in sorted_indices:
        if len(gt_boxes) == 0:
            break

        best_iou = iou_threshold
        best_gt_idx = -1

        for gt_idx in range(len(gt_boxes)):
            if matched_gt[gt_idx]:
                continue
            if pred_classes[pred_idx] != gt_classes[gt_idx]:
                continue
            if iou_matrix[pred_idx, gt_idx] >= best_iou:
                best_iou = iou_matrix[pred_idx, gt_idx]
                best_gt_idx = gt_idx

        if best_gt_idx >= 0:
            tp_mask[pred_idx] = True
            matched_gt[best_gt_idx] = True

    fn_mask = ~matched_gt

    return {
        "tp_mask": tp_mask,
        "fn_mask": fn_mask,
        "pred_buckets": pred_buckets,
        "gt_buckets": gt_buckets,
    }


def compute_ap(recalls: np.ndarray, precisions: np.ndarray) -> float:
    """Compute Average Precision using monotone decreasing interpolation.

    Args:
        recalls: cumulative recall values (sorted ascending)
        precisions: precision values corresponding to recalls

    Returns:
        AP value as a float
    """
    if len(recalls) == 0:
        return 0.0

    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([1.0], precisions, [0.0]))

    # Envelope: make precision monotonically decreasing
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])

    indices = np.where(mrec[1:] != mrec[:-1])[0]
    ap = np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1])
    return float(ap)


def compute_size_bucketed_metrics(
    all_pred_boxes: List[np.ndarray],
    all_pred_scores: List[np.ndarray],
    all_pred_classes: List[np.ndarray],
    all_gt_boxes: List[np.ndarray],
    all_gt_classes: List[np.ndarray],
    iou_threshold: float = 0.5,
    num_classes: int = 7,
) -> Dict:
    """Compute size-bucketed metrics across all images.

    This is the main entry point for size-bucketed evaluation.

    Args:
        all_pred_boxes: List of [N_i, 4] prediction boxes per image
        all_pred_scores: List of [N_i] confidence scores per image
        all_pred_classes: List of [N_i] class IDs per image
        all_gt_boxes: List of [M_i, 4] ground truth boxes per image
        all_gt_classes: List of [M_i] ground truth class IDs per image
        iou_threshold: IoU threshold for matching (default 0.5)
        num_classes: number of defect classes (default 7)

    Returns:
        Dict with 'overall' (per-bucket metrics), 'per_class' (per-class
        per-bucket metrics), 'iou_threshold', and 'num_images'.
    """
    results = {
        bucket: {"tp": 0, "fp": 0, "fn": 0, "num_gt": 0} for bucket in SIZE_BUCKETS
    }

    class_bucket_results = {}
    for cls_id in range(num_classes):
        class_bucket_results[cls_id] = {
            bucket: {"tp": 0, "fp": 0, "fn": 0, "num_gt": 0} for bucket in SIZE_BUCKETS
        }

    bucket_scores = {bucket: [] for bucket in SIZE_BUCKETS}
    bucket_tp_flags = {bucket: [] for bucket in SIZE_BUCKETS}

    for img_idx in range(len(all_pred_boxes)):
        pred_boxes = all_pred_boxes[img_idx]
        pred_scores = all_pred_scores[img_idx]
        pred_classes = all_pred_classes[img_idx]
        gt_boxes = all_gt_boxes[img_idx]
        gt_classes = all_gt_classes[img_idx]

        if len(pred_boxes) == 0:
            pred_boxes = np.zeros((0, 4))
            pred_scores = np.zeros(0)
            pred_classes = np.zeros(0, dtype=int)
        if len(gt_boxes) == 0:
            gt_boxes = np.zeros((0, 4))
            gt_classes = np.zeros(0, dtype=int)

        matching = match_predictions_to_ground_truths(
            pred_boxes, pred_scores, pred_classes, gt_boxes, gt_classes, iou_threshold
        )

        tp_mask = matching["tp_mask"]
        fn_mask = matching["fn_mask"]
        pred_buckets = matching["pred_buckets"]
        gt_buckets = matching["gt_buckets"]

        # Count TP/FP per prediction
        for pred_idx in range(len(pred_boxes)):
            bucket = pred_buckets[pred_idx]
            is_tp = tp_mask[pred_idx]

            results[bucket]["tp" if is_tp else "fp"] += 1
            bucket_scores[bucket].append(float(pred_scores[pred_idx]))
            bucket_tp_flags[bucket].append(1 if is_tp else 0)

            cls_id = int(pred_classes[pred_idx])
            if cls_id < num_classes:
                class_bucket_results[cls_id][bucket]["tp" if is_tp else "fp"] += 1

        # Count FN per unmatched GT
        for gt_idx in range(len(gt_boxes)):
            if fn_mask[gt_idx]:
                bucket = gt_buckets[gt_idx]
                results[bucket]["fn"] += 1
                cls_id = int(gt_classes[gt_idx])
                if cls_id < num_classes:
                    class_bucket_results[cls_id][bucket]["fn"] += 1

        # Count total GTs per bucket
        for gt_idx in range(len(gt_boxes)):
            bucket = gt_buckets[gt_idx]
            results[bucket]["num_gt"] += 1
            cls_id = int(gt_classes[gt_idx])
            if cls_id < num_classes:
                class_bucket_results[cls_id][bucket]["num_gt"] += 1

    # Compute precision, recall, F1, AP per bucket
    for bucket in SIZE_BUCKETS:
        tp = results[bucket]["tp"]
        fp = results[bucket]["fp"]
        fn = results[bucket]["fn"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            (2 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )

        results[bucket]["precision"] = precision
        results[bucket]["recall"] = recall
        results[bucket]["f1"] = f1

        # AP computation
        if len(bucket_scores[bucket]) > 0 and results[bucket]["num_gt"] > 0:
            scores = np.array(bucket_scores[bucket])
            tp_flags = np.array(bucket_tp_flags[bucket])
            sorted_idx = np.argsort(-scores)
            tp_sorted = tp_flags[sorted_idx]
            cum_tp = np.cumsum(tp_sorted)
            cum_fp = np.cumsum(1 - tp_sorted)
            recalls_arr = cum_tp / results[bucket]["num_gt"]
            precisions_arr = cum_tp / (cum_tp + cum_fp)
            results[bucket]["ap"] = compute_ap(recalls_arr, precisions_arr)
        else:
            results[bucket]["ap"] = 0.0

    # Compute per-class recall
    for cls_id in range(num_classes):
        for bucket in SIZE_BUCKETS:
            counts = class_bucket_results[cls_id][bucket]
            tp = counts["tp"]
            fp = counts["fp"]
            fn = counts["fn"]
            counts["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            counts["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "overall": results,
        "per_class": class_bucket_results,
        "iou_threshold": iou_threshold,
        "num_images": len(all_pred_boxes),
    }


def format_size_bucket_report(
    metrics: Dict,
    class_names: Optional[List[str]] = None,
) -> str:
    """Format size-bucketed metrics as a human-readable Markdown table.

    Args:
        metrics: Output from compute_size_bucketed_metrics
        class_names: Optional list of class names (length = num_classes)

    Returns:
        Markdown-formatted string with overall and per-class tables.
    """
    lines = []
    lines.append("## Size-Bucketed Evaluation Results")
    lines.append("")
    lines.append(
        f"IoU threshold: {metrics['iou_threshold']} | Images: {metrics['num_images']}"
    )
    lines.append("")

    # Overall bucket table
    lines.append("### Overall Metrics by Object Size")
    lines.append("")
    lines.append("| Bucket | GT Count | TP | FP | FN | Precision | Recall | F1 | AP |")
    lines.append("|--------|----------|----|----|----|-----------|--------|----|----|")

    for bucket in ["small", "medium", "large"]:
        d = metrics["overall"][bucket]
        lines.append(
            f"| {bucket} | {d['num_gt']} | {d['tp']} | {d['fp']} | {d['fn']} | "
            f"{d['precision']:.3f} | {d['recall']:.3f} | {d['f1']:.3f} | {d['ap']:.3f} |"
        )

    lines.append("")

    # Per-class recall breakdown
    if class_names:
        lines.append("### Per-Class Recall by Size")
        lines.append("")
        lines.append("| Class | Small Recall | Medium Recall | Large Recall |")
        lines.append("|-------|-------------|---------------|--------------|")

        for cls_id, cls_name in enumerate(class_names):
            if cls_id in metrics["per_class"]:
                cls_data = metrics["per_class"][cls_id]
                sr = cls_data["small"]["recall"]
                mr = cls_data["medium"]["recall"]
                lr = cls_data["large"]["recall"]
                lines.append(f"| {cls_name} | {sr:.3f} | {mr:.3f} | {lr:.3f} |")

    lines.append("")
    lines.append(
        "> **Commandment #1**: If small-object recall is significantly lower than "
        "large-object recall, aggregate mAP is hiding a critical failure mode."
    )

    return "\n".join(lines)
