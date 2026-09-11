"""Per-class evaluation metrics for object detection.

Computes precision, recall, F1, and AP for each defect class individually.
This is critical for identifying class-specific failures that aggregate
metrics would hide (Commandment #1: Aggregate Metrics Lie for Rare Events).

References:
    - eval.md, Module 20, Commandment #1
    - eval.md, Module 17: Confidence Thresholding and Class Filtering
"""

import numpy as np
from typing import List, Dict, Optional

from src.stage2.eval.metrics.size_bucketed import (
    compute_iou_matrix,
    compute_ap,
)


def compute_classwise_metrics(
    all_pred_boxes: List[np.ndarray],
    all_pred_scores: List[np.ndarray],
    all_pred_classes: List[np.ndarray],
    all_gt_boxes: List[np.ndarray],
    all_gt_classes: List[np.ndarray],
    iou_threshold: float = 0.5,
    num_classes: int = 7,
    class_names: Optional[List[str]] = None,
) -> Dict:
    """Compute per-class detection metrics across all images.

    Args:
        all_pred_boxes: List of [N_i, 4] prediction boxes per image
        all_pred_scores: List of [N_i] confidence scores per image
        all_pred_classes: List of [N_i] class IDs per image
        all_gt_boxes: List of [M_i, 4] ground truth boxes per image
        all_gt_classes: List of [M_i] ground truth class IDs per image
        iou_threshold: IoU threshold for matching (default 0.5)
        num_classes: Number of defect classes (default 7)
        class_names: Optional list of class names

    Returns:
        Dict with per-class metrics and overall summary.
    """
    if class_names is None:
        class_names = [f"class_{i}" for i in range(num_classes)]

    # Per-class accumulators
    class_metrics = {}
    for cls_id in range(num_classes):
        class_metrics[cls_id] = {
            "name": class_names[cls_id],
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "num_gt": 0,
            "num_pred": 0,
            "scores": [],
            "tp_flags": [],
        }

    # Process each image
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

        # Count GTs per class
        for gt_cls in gt_classes:
            gt_cls = int(gt_cls)
            if gt_cls < num_classes:
                class_metrics[gt_cls]["num_gt"] += 1

        # Count predictions per class
        for pred_cls in pred_classes:
            pred_cls = int(pred_cls)
            if pred_cls < num_classes:
                class_metrics[pred_cls]["num_pred"] += 1

        if len(pred_boxes) == 0:
            for gt_cls in gt_classes:
                gt_cls = int(gt_cls)
                if gt_cls < num_classes:
                    class_metrics[gt_cls]["fn"] += 1
            continue

        if len(gt_boxes) == 0:
            for pred_idx in range(len(pred_boxes)):
                pred_cls = int(pred_classes[pred_idx])
                if pred_cls < num_classes:
                    class_metrics[pred_cls]["fp"] += 1
                    class_metrics[pred_cls]["scores"].append(
                        float(pred_scores[pred_idx])
                    )
                    class_metrics[pred_cls]["tp_flags"].append(0)
            continue

        sorted_indices = np.argsort(-pred_scores)
        matched_gt = np.zeros(len(gt_boxes), dtype=bool)

        iou_matrix = compute_iou_matrix(np.array(pred_boxes), np.array(gt_boxes))

        for pred_idx in sorted_indices:
            pred_cls = int(pred_classes[pred_idx])
            if pred_cls >= num_classes:
                continue

            best_iou = iou_threshold
            best_gt_idx = -1

            for gt_idx in range(len(gt_boxes)):
                if matched_gt[gt_idx]:
                    continue
                if int(gt_classes[gt_idx]) != pred_cls:
                    continue
                if iou_matrix[pred_idx, gt_idx] >= best_iou:
                    best_iou = iou_matrix[pred_idx, gt_idx]
                    best_gt_idx = gt_idx

            if best_gt_idx >= 0:
                class_metrics[pred_cls]["tp"] += 1
                class_metrics[pred_cls]["scores"].append(float(pred_scores[pred_idx]))
                class_metrics[pred_cls]["tp_flags"].append(1)
                matched_gt[best_gt_idx] = True
            else:
                class_metrics[pred_cls]["fp"] += 1
                class_metrics[pred_cls]["scores"].append(float(pred_scores[pred_idx]))
                class_metrics[pred_cls]["tp_flags"].append(0)

        for gt_idx in range(len(gt_boxes)):
            if not matched_gt[gt_idx]:
                gt_cls = int(gt_classes[gt_idx])
                if gt_cls < num_classes:
                    class_metrics[gt_cls]["fn"] += 1

    for cls_id in range(num_classes):
        m = class_metrics[cls_id]
        tp = m["tp"]
        fp = m["fp"]
        fn = m["fn"]
        num_gt = m["num_gt"]

        m["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        m["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        m["f1"] = (
            2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"])
            if (m["precision"] + m["recall"]) > 0
            else 0.0
        )

        if len(m["scores"]) > 0 and num_gt > 0:
            scores = np.array(m["scores"])
            tp_flags = np.array(m["tp_flags"])
            sorted_idx = np.argsort(-scores)
            tp_sorted = tp_flags[sorted_idx]
            cum_tp = np.cumsum(tp_sorted)
            cum_fp = np.cumsum(1 - tp_sorted)
            recalls = cum_tp / num_gt
            precisions = cum_tp / (cum_tp + cum_fp)
            m["ap50"] = compute_ap(recalls, precisions)
        else:
            m["ap50"] = 0.0

        del m["scores"]
        del m["tp_flags"]

    total_tp = sum(class_metrics[c]["tp"] for c in range(num_classes))
    total_fp = sum(class_metrics[c]["fp"] for c in range(num_classes))
    total_fn = sum(class_metrics[c]["fn"] for c in range(num_classes))
    total_gt = sum(class_metrics[c]["num_gt"] for c in range(num_classes))

    overall_precision = (
        total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    )
    overall_recall = (
        total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    )
    overall_f1 = (
        2 * overall_precision * overall_recall / (overall_precision + overall_recall)
        if (overall_precision + overall_recall) > 0
        else 0.0
    )
    overall_ap50 = np.mean([class_metrics[c]["ap50"] for c in range(num_classes)])

    return {
        "per_class": class_metrics,
        "overall": {
            "precision": overall_precision,
            "recall": overall_recall,
            "f1": overall_f1,
            "ap50": float(overall_ap50),
            "total_tp": total_tp,
            "total_fp": total_fp,
            "total_fn": total_fn,
            "total_gt": total_gt,
        },
        "iou_threshold": iou_threshold,
        "num_images": len(all_pred_boxes),
        "num_classes": num_classes,
    }


def format_classwise_report(
    metrics: Dict,
    model_name: str = "Model",
) -> str:
    """Format per-class metrics as a human-readable Markdown table.

    Args:
        metrics: Output from compute_classwise_metrics
        model_name: Name of the model being evaluated

    Returns:
        Markdown-formatted string
    """
    lines = []
    lines.append(f"## Per-Class Evaluation Report: {model_name}")
    lines.append("")
    lines.append(
        f"IoU threshold: {metrics['iou_threshold']} | Images: {metrics['num_images']}"
    )
    lines.append("")

    lines.append(
        "| Class | GT Count | Pred Count | TP | FP | FN | Precision | Recall | F1 | AP50 |"
    )
    lines.append(
        "|-------|----------|------------|----|----|----|-----------|--------|----|----- |"
    )

    for cls_id in range(metrics["num_classes"]):
        m = metrics["per_class"][cls_id]
        lines.append(
            f"| {m['name']} | {m['num_gt']} | {m['num_pred']} | {m['tp']} | "
            f"{m['fp']} | {m['fn']} | {m['precision']:.3f} | {m['recall']:.3f} | "
            f"{m['f1']:.3f} | {m['ap50']:.3f} |"
        )

    lines.append("")

    o = metrics["overall"]
    lines.append("### Overall Summary")
    lines.append("")
    lines.append(f"- **Precision**: {o['precision']:.3f}")
    lines.append(f"- **Recall**: {o['recall']:.3f}")
    lines.append(f"- **F1**: {o['f1']:.3f}")
    lines.append(f"- **mAP50**: {o['ap50']:.3f}")
    lines.append("")

    sorted_by_ap = sorted(
        range(metrics["num_classes"]), key=lambda c: metrics["per_class"][c]["ap50"]
    )
    worst_3 = sorted_by_ap[:3]
    lines.append("### Weakest Classes (Lowest AP50)")
    lines.append("")
    for cls_id in worst_3:
        m = metrics["per_class"][cls_id]
        if m["num_gt"] > 0:
            lines.append(
                f"- **{m['name']}**: AP50={m['ap50']:.3f}, Recall={m['recall']:.3f}"
            )

    lines.append("")
    return "\n".join(lines)
