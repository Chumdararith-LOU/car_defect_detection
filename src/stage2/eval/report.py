"""Evaluation report writer.

Combines all evaluation metrics into comprehensive reports:
- Markdown report for human reading
- JSON results for programmatic access and CI regression checks
- Optional MLflow logging for experiment tracking

References:
    - eval.md, Module 20, Commandment #9: Log everything to MLflow
"""

import os
import json
import datetime
from typing import Dict, List, Optional


def combine_metrics(
    model_name: str,
    classwise_metrics: Optional[Dict] = None,
    size_bucketed_metrics: Optional[Dict] = None,
    clean_fpr_metrics: Optional[Dict] = None,
    latency_metrics: Optional[Dict] = None,
    memory_metrics: Optional[Dict] = None,
) -> Dict:
    """Combine all metric outputs into a single structured dictionary.

    Args:
        model_name: Name of the evaluated model
        classwise_metrics: Output from compute_classwise_metrics
        size_bucketed_metrics: Output from compute_size_bucketed_metrics
        clean_fpr_metrics: Output from compute_clean_fpr
        latency_metrics: Output from LatencyResult.to_dict()
        memory_metrics: Output from profile_memory

    Returns:
        Combined metrics dictionary
    """
    combined = {
        "model_name": model_name,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    if classwise_metrics is not None:
        combined["classwise"] = classwise_metrics
    if size_bucketed_metrics is not None:
        combined["size_bucketed"] = size_bucketed_metrics
    if clean_fpr_metrics is not None:
        combined["clean_fpr"] = clean_fpr_metrics
    if latency_metrics is not None:
        combined["latency"] = latency_metrics
    if memory_metrics is not None:
        combined["memory"] = memory_metrics

    return combined


def write_json_report(
    combined_metrics: Dict,
    output_path: str,
) -> str:
    """Write combined metrics to a JSON file.

    Args:
        combined_metrics: Output from combine_metrics
        output_path: Path to write the JSON file

    Returns:
        Absolute path to the written file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(combined_metrics, f, indent=2, default=str)

    return os.path.abspath(output_path)


def write_markdown_report(
    combined_metrics: Dict,
    output_path: str,
    comparison_metrics: Optional[List[Dict]] = None,
) -> str:
    """Write a comprehensive Markdown evaluation report.

    Args:
        combined_metrics: Output from combine_metrics
        output_path: Path to write the Markdown file
        comparison_metrics: Optional list of other models' metrics for comparison

    Returns:
        Absolute path to the written file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = []
    model_name = combined_metrics.get("model_name", "Unknown Model")
    timestamp = combined_metrics.get("timestamp", "N/A")

    lines.append(f"# Evaluation Report: {model_name}")
    lines.append("")
    lines.append(f"**Generated**: {timestamp}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if "classwise" in combined_metrics:
        cw = combined_metrics["classwise"]
        o = cw.get("overall", {})
        lines.append("## 1. Overall Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Precision | {o.get('precision', 0):.3f} |")
        lines.append(f"| Recall | {o.get('recall', 0):.3f} |")
        lines.append(f"| F1 | {o.get('f1', 0):.3f} |")
        lines.append(f"| mAP50 | {o.get('ap50', 0):.3f} |")
        lines.append(f"| Total GT | {o.get('total_gt', 0)} |")
        lines.append(f"| Total TP | {o.get('total_tp', 0)} |")
        lines.append(f"| Total FP | {o.get('total_fp', 0)} |")
        lines.append(f"| Total FN | {o.get('total_fn', 0)} |")
        lines.append("")

    if "classwise" in combined_metrics:
        lines.append("## 2. Per-Class Metrics")
        lines.append("")
        cw = combined_metrics["classwise"]
        lines.append("| Class | GT | TP | FP | FN | Precision | Recall | F1 | AP50 |")
        lines.append("|-------|----|----|----|----|-----------|--------|----|----- |")
        per_class = cw.get("per_class", {})
        for cls_id in range(cw.get("num_classes", 7)):
            m = per_class.get(cls_id, {})
            if m:
                lines.append(
                    f"| {m['name']} | {m['num_gt']} | {m['tp']} | {m['fp']} | {m['fn']} | "
                    f"{m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['ap50']:.3f} |"
                )
        lines.append("")

    if "size_bucketed" in combined_metrics:
        lines.append("## 3. Size-Bucketed Metrics (Commandment #1)")
        lines.append("")
        sb = combined_metrics["size_bucketed"]
        lines.append("| Bucket | GT | TP | FP | FN | Precision | Recall | F1 | AP |")
        lines.append("|--------|----|----|----|----|-----------|--------|----|----|")
        for bucket in ["small", "medium", "large"]:
            if bucket in sb.get("overall", {}):
                d = sb["overall"][bucket]
                lines.append(
                    f"| {bucket} | {d.get('num_gt', 0)} | {d.get('tp', 0)} | "
                    f"{d.get('fp', 0)} | {d.get('fn', 0)} | {d.get('precision', 0):.3f} | "
                    f"{d.get('recall', 0):.3f} | {d.get('f1', 0):.3f} | {d.get('ap', 0):.3f} |"
                )
        lines.append("")
        lines.append(
            "> **Commandment #1**: If small-object recall is significantly lower"
        )
        lines.append(
            "> than large-object recall, aggregate mAP is hiding a critical failure."
        )
        lines.append("")

    if "clean_fpr" in combined_metrics:
        lines.append("## 4. Clean Image FPR (Production Metric)")
        lines.append("")
        fpr = combined_metrics["clean_fpr"]
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total clean images | {fpr.get('total_clean_images', 0)} |")
        lines.append(f"| Images with FP | {fpr.get('images_with_fp', 0)} |")
        lines.append(f"| **FPR (%)** | **{fpr.get('fpr_percent', 0):.1f}%** |")
        lines.append(
            f"| Total false positives | {fpr.get('total_false_positives', 0)} |"
        )
        lines.append(f"| Avg FP confidence | {fpr.get('avg_fp_confidence', 0):.3f} |")
        lines.append("")

        fp_by_class = fpr.get("fp_by_class", {})
        if fp_by_class:
            lines.append("### FP Breakdown by Class")
            lines.append("")
            lines.append("| Class | FP Count |")
            lines.append("|-------|----------|")
            for cls_name, count in sorted(
                fp_by_class.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"| {cls_name} | {count} |")
            lines.append("")

    if "latency" in combined_metrics:
        lines.append("## 5. Inference Latency")
        lines.append("")
        lat = combined_metrics["latency"]
        lines.append("| Stage | Time (ms) |")
        lines.append("|-------|-----------|")
        if lat.get("preprocess_ms", 0) > 0:
            lines.append(f"| Preprocess | {lat['preprocess_ms']:.1f} |")
        if lat.get("inference_ms", 0) > 0:
            lines.append(f"| Inference | {lat['inference_ms']:.1f} |")
        if lat.get("postprocess_ms", 0) > 0:
            lines.append(f"| Postprocess/NMS | {lat['postprocess_ms']:.1f} |")
        lines.append(f"| **Total** | **{lat.get('total_ms', 0):.1f}** |")
        lines.append(f"| FPS | {lat.get('fps', 0):.2f} |")
        lines.append("")

        total_ms = lat.get("total_ms", 0)
        if total_ms > 0:
            if total_ms <= 500:
                lines.append("✅ Within 500ms production budget")
            else:
                lines.append(f"⚠️ Exceeds 500ms budget by {total_ms - 500:.1f}ms")
            lines.append("")

    if "memory" in combined_metrics:
        lines.append("## 6. Memory Usage")
        lines.append("")
        mem = combined_metrics["memory"]
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Backend | {mem.get('backend', 'unknown')} |")
        lines.append(f"| Peak Memory | {mem.get('peak_memory_mb', 0):.1f} MB |")
        lines.append(f"| Peak Memory | {mem.get('peak_memory_mb', 0) / 1024:.2f} GB |")
        lines.append("")

    if comparison_metrics:
        lines.append("## 7. Model Comparison")
        lines.append("")
        lines.append(
            "| Model | mAP50 | Recall | Clean FPR | Latency (ms) | Peak Mem (GB) |"
        )
        lines.append(
            "|-------|-------|--------|-----------|--------------|---------------|"
        )

        cw_overall = combined_metrics.get("classwise", {}).get("overall", {})
        fpr_pct = combined_metrics.get("clean_fpr", {}).get("fpr_percent", "N/A")
        lat_ms = combined_metrics.get("latency", {}).get("total_ms", "N/A")
        mem_gb = combined_metrics.get("memory", {}).get("peak_memory_mb", 0) / 1024

        lines.append(
            f"| **{model_name}** | {cw_overall.get('ap50', 0):.3f} | "
            f"{cw_overall.get('recall', 0):.3f} | {fpr_pct} | {lat_ms} | {mem_gb:.2f} |"
        )

        for comp in comparison_metrics:
            comp_name = comp.get("model_name", "Unknown")
            comp_cw = comp.get("classwise", {}).get("overall", {})
            comp_fpr = comp.get("clean_fpr", {}).get("fpr_percent", "N/A")
            comp_lat = comp.get("latency", {}).get("total_ms", "N/A")
            comp_mem = comp.get("memory", {}).get("peak_memory_mb", 0) / 1024

            lines.append(
                f"| {comp_name} | {comp_cw.get('ap50', 0):.3f} | "
                f"{comp_cw.get('recall', 0):.3f} | {comp_fpr} | {comp_lat} | {comp_mem:.2f} |"
            )
        lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)

    return os.path.abspath(output_path)


def log_to_mlflow(
    combined_metrics: Dict,
    experiment_name: str = "car_defect_eval",
) -> None:
    """Log evaluation metrics to MLflow.

    Args:
        combined_metrics: Output from combine_metrics
        experiment_name: MLflow experiment name
    """
    try:
        import mlflow

        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(
            run_name=f"eval_{combined_metrics.get('model_name', 'unknown')}"
        ):
            if "classwise" in combined_metrics:
                o = combined_metrics["classwise"].get("overall", {})
                mlflow.log_metric("precision", o.get("precision", 0))
                mlflow.log_metric("recall", o.get("recall", 0))
                mlflow.log_metric("f1", o.get("f1", 0))
                mlflow.log_metric("map50", o.get("ap50", 0))

                for cls_id, m in (
                    combined_metrics["classwise"].get("per_class", {}).items()
                ):
                    mlflow.log_metric(f"ap50_{m['name']}", m.get("ap50", 0))
                    mlflow.log_metric(f"recall_{m['name']}", m.get("recall", 0))

            if "clean_fpr" in combined_metrics:
                fpr = combined_metrics["clean_fpr"]
                mlflow.log_metric("clean_fpr_percent", fpr.get("fpr_percent", 0))
                mlflow.log_metric(
                    "total_false_positives", fpr.get("total_false_positives", 0)
                )

            if "latency" in combined_metrics:
                lat = combined_metrics["latency"]
                mlflow.log_metric("latency_total_ms", lat.get("total_ms", 0))
                mlflow.log_metric("fps", lat.get("fps", 0))

            if "memory" in combined_metrics:
                mem = combined_metrics["memory"]
                mlflow.log_metric("peak_memory_mb", mem.get("peak_memory_mb", 0))

            mlflow.set_tag("model_name", combined_metrics.get("model_name", "unknown"))
            mlflow.set_tag("eval_timestamp", combined_metrics.get("timestamp", ""))

    except ImportError:
        print("[⚠️] MLflow not installed. Skipping MLflow logging.")
    except Exception as e:
        print(f"[⚠️] MLflow logging failed: {e}")


def generate_full_report(
    combined_metrics: Dict,
    report_dir: str = "reports/eval/",
    comparison_metrics: Optional[List[Dict]] = None,
    log_mlflow: bool = False,
    mlflow_experiment: str = "car_defect_eval",
) -> Dict:
    """Generate all report artifacts.

    This is the main entry point for report generation.

    Args:
        combined_metrics: Output from combine_metrics
        report_dir: Directory to write reports to
        comparison_metrics: Optional list of other models' metrics
        log_mlflow: Whether to log to MLflow
        mlflow_experiment: MLflow experiment name

    Returns:
        Dict with paths to generated files
    """
    model_name = combined_metrics.get("model_name", "unknown_model")
    safe_name = model_name.replace("/", "_").replace(" ", "_")

    run_dir = os.path.join(report_dir, safe_name)
    os.makedirs(run_dir, exist_ok=True)

    json_path = os.path.join(run_dir, "results.json")
    write_json_report(combined_metrics, json_path)

    md_path = os.path.join(run_dir, "report.md")
    write_markdown_report(combined_metrics, md_path, comparison_metrics)

    if log_mlflow:
        log_to_mlflow(combined_metrics, mlflow_experiment)

    return {
        "json_path": json_path,
        "markdown_path": md_path,
        "run_dir": run_dir,
    }
