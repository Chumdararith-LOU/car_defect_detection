"""Stage 2 Evaluation Entry Point.

Single CLI command to run the complete evaluation pipeline for car defect
detection models. Supports multiple evaluation modes and model comparison.

Usage:
    python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml
    python -m src.stage2.eval.evaluate --config configs/eval/clean_images.yaml
    python -m src.stage2.eval.evaluate --config configs/eval/stage2_benchmark.yaml --mode benchmark

Modes:
    benchmark   - Compute accuracy metrics (mAP, precision, recall) on test set
    clean_fpr   - Compute false positive rate on clean (defect-free) images
    latency     - Measure inference speed (preprocess, inference, NMS)
    memory      - Measure peak memory usage
    full        - Run all modes and generate comprehensive report

References:
    - eval.md, Module 20: The 10 Commandments of Industrial ML
    - eval.md, Module 17: Confidence Thresholding and Class Filtering
"""

import os
import sys
import argparse
import yaml
import numpy as np
from typing import Dict, List

# Ensure project root is in path
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

from src.stage2.eval.sahi_eval import (
    load_model,
    run_batch_inference,
    load_test_dataset,
    resolve_device,
)
from src.stage2.eval.metrics.classwise import compute_classwise_metrics
from src.stage2.eval.metrics.size_bucketed import compute_size_bucketed_metrics
from src.stage2.eval.metrics.clean_fpr import compute_clean_fpr
from src.stage2.eval.perf.latency import LatencyProfiler
from src.stage2.eval.perf.memory import profile_memory
from src.stage2.eval.report import combine_metrics, generate_full_report

# Default class names for the 7 defect classes
DEFAULT_CLASS_NAMES = [
    "broken_lamp",
    "corrosion",
    "crack",
    "dent",
    "disjoint_part",
    "glass_shatter",
    "scratch",
]


def load_eval_config(config_path: str) -> Dict:
    """Load evaluation configuration from YAML.

    Args:
        config_path: Path to the config YAML file

    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    return cfg


def evaluate_benchmark(
    model,
    cfg: Dict,
    class_names: List[str],
    device: str = "auto",
) -> Dict:
    """Run benchmark evaluation (accuracy metrics) on test dataset.

    Args:
        model: Loaded YOLO model
        cfg: Evaluation configuration
        class_names: List of class names
        device: Compute device

    Returns:
        Dict with 'classwise' and 'size_bucketed' metrics
    """
    print("  [📊] Running benchmark evaluation on test set...")

    # Load test dataset
    data_cfg = cfg.get("data", {})
    test_yaml = data_cfg.get("test")
    if not test_yaml or not os.path.exists(test_yaml):
        print(f"  [⚠️] Test dataset not found: {test_yaml}")
        return {}

    image_paths, gt_boxes_list, gt_classes_list = load_test_dataset(
        test_yaml, split="test"
    )
    print(f"  Loaded {len(image_paths)} test images")

    if len(image_paths) == 0:
        print("  [⚠️] No test images found")
        return {}

    # Run inference
    inference_cfg = cfg.get("inference", {})
    sahi_cfg = cfg.get("sahi", {})
    use_sahi = sahi_cfg.get("enabled", False)

    predictions = run_batch_inference(
        model=model,
        image_paths=image_paths,
        conf_threshold=inference_cfg.get("conf_threshold", 0.25),
        imgsz=inference_cfg.get("imgsz", 1024),
        use_sahi=use_sahi,
        sahi_config=sahi_cfg if use_sahi else None,
        device=device,
        verbose=True,
    )

    # Convert predictions to format expected by metrics modules
    pred_boxes_list = []
    pred_scores_list = []
    pred_classes_list = []

    for pred in predictions:
        if pred is None or len(pred) == 0:
            pred_boxes_list.append(np.zeros((0, 4)))
            pred_scores_list.append(np.zeros(0))
            pred_classes_list.append(np.zeros(0, dtype=int))
        else:
            pred_boxes_list.append(pred[:, :4])
            pred_scores_list.append(pred[:, 4])
            pred_classes_list.append(pred[:, 5].astype(int))

    # Compute classwise metrics
    print("  Computing per-class metrics...")
    classwise = compute_classwise_metrics(
        pred_boxes_list,
        pred_scores_list,
        pred_classes_list,
        gt_boxes_list,
        gt_classes_list,
        iou_threshold=0.5,
        num_classes=len(class_names),
        class_names=class_names,
    )

    # Compute size-bucketed metrics
    print("  Computing size-bucketed metrics...")
    size_bucketed = compute_size_bucketed_metrics(
        pred_boxes_list,
        pred_scores_list,
        pred_classes_list,
        gt_boxes_list,
        gt_classes_list,
        iou_threshold=0.5,
        num_classes=len(class_names),
    )

    return {
        "classwise": classwise,
        "size_bucketed": size_bucketed,
    }


def evaluate_clean_fpr(
    model,
    cfg: Dict,
    class_names: List[str],
    device: str = "auto",
) -> Dict:
    """Run clean image FPR evaluation.

    Args:
        model: Loaded YOLO model
        cfg: Evaluation configuration
        class_names: List of class names
        device: Compute device

    Returns:
        Dict with 'clean_fpr' metrics
    """
    print("  [🧹] Running clean image FPR evaluation...")

    data_cfg = cfg.get("data", {})
    clean_dir = data_cfg.get("clean_images")

    if not clean_dir or not os.path.exists(clean_dir):
        print(f"  [⚠️] Clean images directory not found: {clean_dir}")
        return {}

    # Collect clean image paths
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
    image_paths = sorted(
        [
            os.path.join(clean_dir, f)
            for f in os.listdir(clean_dir)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]
    )

    # Limit to configured count
    clean_count = data_cfg.get("clean_count", len(image_paths))
    image_paths = image_paths[:clean_count]

    print(f"  Found {len(image_paths)} clean images")

    if len(image_paths) == 0:
        print("  [⚠️] No clean images found")
        return {}

    # Run inference
    inference_cfg = cfg.get("inference", {})
    sahi_cfg = cfg.get("sahi", {})
    use_sahi = sahi_cfg.get("enabled", False)
    conf_threshold = inference_cfg.get("conf_threshold", 0.25)

    predictions = run_batch_inference(
        model=model,
        image_paths=image_paths,
        conf_threshold=conf_threshold,
        imgsz=inference_cfg.get("imgsz", 1024),
        use_sahi=use_sahi,
        sahi_config=sahi_cfg if use_sahi else None,
        device=device,
        verbose=True,
    )

    # Compute FPR
    print("  Computing FPR metrics...")
    fpr_metrics = compute_clean_fpr(
        predictions,
        conf_threshold=conf_threshold,
        class_names=class_names,
    )

    return {"clean_fpr": fpr_metrics}


def evaluate_latency(
    model,
    cfg: Dict,
    image_paths: List[str],
    device: str = "auto",
) -> Dict:
    """Run latency profiling.

    Args:
        model: Loaded YOLO model
        cfg: Evaluation configuration
        image_paths: List of image paths to profile
        device: Compute device

    Returns:
        Dict with 'latency' metrics
    """
    print("  [⏱️] Running latency profiling...")

    if len(image_paths) == 0:
        print("  [⚠️] No images for latency profiling")
        return {}

    inference_cfg = cfg.get("inference", {})
    imgsz = inference_cfg.get("imgsz", 1024)

    profiler = LatencyProfiler(warmup_runs=3, measure_runs=10)

    for img_path in image_paths[:10]:  # Profile first 10 images
        profiler.start()

        # Preprocessing (image loading)
        profiler.mark("preprocess")

        # Inference
        model.predict(
            source=img_path,
            imgsz=imgsz,
            device=resolve_device(device),
            verbose=False,
        )
        profiler.mark("inference")

        # Postprocessing (NMS happens inside predict)
        profiler.mark("postprocess")
        profiler.end()

    results = profiler.get_results()
    return {"latency": results.to_dict()}


def evaluate_memory(
    model,
    cfg: Dict,
    image_paths: List[str],
    device: str = "auto",
) -> Dict:
    """Run memory profiling.

    Args:
        model: Loaded YOLO model
        cfg: Evaluation configuration
        image_paths: List of image paths to profile
        device: Compute device

    Returns:
        Dict with 'memory' metrics
    """
    print("  [💾] Running memory profiling...")

    if len(image_paths) == 0:
        print("  [⚠️] No images for memory profiling")
        return {}

    inference_cfg = cfg.get("inference", {})
    imgsz = inference_cfg.get("imgsz", 1024)

    def run_inference():
        model.predict(
            source=image_paths[0],
            imgsz=imgsz,
            device=resolve_device(device),
            verbose=False,
        )

    memory_stats = profile_memory(run_inference)
    return {"memory": memory_stats}


def evaluate_single_model(
    model_cfg: Dict,
    cfg: Dict,
    mode: str = "full",
    class_names: List[str] = None,
) -> Dict:
    """Evaluate a single model.

    Args:
        model_cfg: Model configuration (name, weights path)
        cfg: Full evaluation configuration
        mode: Evaluation mode
        class_names: List of class names

    Returns:
        Combined metrics dictionary
    """
    if class_names is None:
        class_names = DEFAULT_CLASS_NAMES

    model_name = model_cfg.get("name", "unknown")
    weights_path = model_cfg.get("weights")

    print(f"\n{'='*60}")
    print(f"Evaluating model: {model_name}")
    print(f"Weights: {weights_path}")
    print(f"Mode: {mode}")
    print(f"{'='*60}")

    # Load model
    device = cfg.get("inference", {}).get("device", "auto")
    try:
        model = load_model(weights_path, device=device)
    except FileNotFoundError as e:
        print(f"  [❌] Model not found: {e}")
        return {"model_name": model_name, "error": str(e)}

    # Collect metrics based on mode
    all_metrics = {}

    # Get image paths for latency/memory profiling
    data_cfg = cfg.get("data", {})
    test_yaml = data_cfg.get("test")
    profile_images = []
    if test_yaml and os.path.exists(test_yaml):
        try:
            img_paths, _, _ = load_test_dataset(test_yaml, split="test")
            profile_images = img_paths[:5]  # Use first 5 for profiling
        except Exception:
            pass

    if mode in ("benchmark", "full"):
        benchmark_results = evaluate_benchmark(model, cfg, class_names, device)
        all_metrics.update(benchmark_results)

    if mode in ("clean_fpr", "full"):
        fpr_results = evaluate_clean_fpr(model, cfg, class_names, device)
        all_metrics.update(fpr_results)

    if mode in ("latency", "full"):
        latency_results = evaluate_latency(model, cfg, profile_images, device)
        all_metrics.update(latency_results)

    if mode in ("memory", "full"):
        memory_results = evaluate_memory(model, cfg, profile_images, device)
        all_metrics.update(memory_results)

    # Combine all metrics
    combined = combine_metrics(
        model_name=model_name,
        classwise_metrics=all_metrics.get("classwise"),
        size_bucketed_metrics=all_metrics.get("size_bucketed"),
        clean_fpr_metrics=all_metrics.get("clean_fpr"),
        latency_metrics=all_metrics.get("latency"),
        memory_metrics=all_metrics.get("memory"),
    )

    return combined


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2 Evaluation Harness - Car Defect Detection"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to evaluation config YAML",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["benchmark", "clean_fpr", "latency", "memory", "full"],
        help="Override evaluation mode from config",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model weights path (single model evaluation)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow logging",
    )
    args = parser.parse_args()

    # Load config
    print(f"Loading evaluation config: {args.config}")
    cfg = load_eval_config(args.config)

    # Determine mode
    mode = args.mode or cfg.get("mode", "full")
    print(f"Evaluation mode: {mode}")

    # Get models to evaluate
    models_cfg = cfg.get("models", [])
    if args.model:
        models_cfg = [{"name": "override_model", "weights": args.model}]

    if not models_cfg:
        print("[❌] No models specified in config or command line")
        sys.exit(1)

    # Evaluate each model
    all_results = []
    for model_cfg in models_cfg:
        result = evaluate_single_model(model_cfg, cfg, mode=mode)
        all_results.append(result)

    # Generate reports
    output_cfg = cfg.get("output", {})
    report_dir = output_cfg.get("report_dir", "reports/eval/")
    log_mlflow = output_cfg.get("log_to_mlflow", True) and not args.no_mlflow

    print(f"\n{'='*60}")
    print("Generating reports...")
    print(f"{'='*60}")

    for result in all_results:
        if "error" in result:
            print(
                f"  [⚠️] Skipping report for failed model: {result.get('model_name')}"
            )
            continue

        report_paths = generate_full_report(
            combined_metrics=result,
            report_dir=report_dir,
            comparison_metrics=[
                r for r in all_results if r != result and "error" not in r
            ],
            log_mlflow=log_mlflow,
            mlflow_experiment=cfg.get("project_name", "car_defect_eval"),
        )

        print(f"\n  📄 Markdown report: {report_paths['markdown_path']}")
        print(f"  📊 JSON results:    {report_paths['json_path']}")

    # Print summary comparison table
    if len(all_results) > 1:
        print(f"\n{'='*60}")
        print("MODEL COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"{'Model':<25} {'mAP50':>8} {'Recall':>8} {'FPR%':>8} {'Latency':>10}")
        print("-" * 60)

        for result in all_results:
            if "error" in result:
                continue
            name = result.get("model_name", "unknown")[:24]
            cw = result.get("classwise", {}).get("overall", {})
            fpr = result.get("clean_fpr", {}).get("fpr_percent", "N/A")
            lat = result.get("latency", {}).get("total_ms", "N/A")

            map50 = (
                f"{cw.get('ap50', 0):.3f}"
                if isinstance(cw.get("ap50"), (int, float))
                else "N/A"
            )
            recall = (
                f"{cw.get('recall', 0):.3f}"
                if isinstance(cw.get("recall"), (int, float))
                else "N/A"
            )
            fpr_str = f"{fpr:.1f}" if isinstance(fpr, (int, float)) else "N/A"
            lat_str = f"{lat:.1f}ms" if isinstance(lat, (int, float)) else "N/A"

            print(f"{name:<25} {map50:>8} {recall:>8} {fpr_str:>8} {lat_str:>10}")

    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
