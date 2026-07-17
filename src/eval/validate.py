import argparse
import os
import yaml
from pathlib import Path
from src.inference.router import RawStage1Router
from src.utils.config_helpers import load_pipeline_config


def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_set(router, file_paths, set_name, expected_outcome=True, imgsz=640):
    """Evaluates a list of files using the router and returns success metrics."""
    tp, tn, fp, fn = 0, 0, 0, 0
    evaluated = 0

    print(f"\n[+] Evaluating {set_name} (n={len(file_paths)}):")
    for f in file_paths:
        path = Path(f)
        if not path.exists():
            print(f"  [!] Skipping missing file: {f}")
            continue
        evaluated += 1
        _, _, _, detected = router.route_image(path, imgsz=imgsz)

        if expected_outcome:  # Expecting defects (True Positives)
            if detected:
                tp += 1
                print(f"  [✅] {path.name}: Defect Detected (True Positive)")
            else:
                fn += 1
                print(f"  [❌] {path.name}: Blind / Missed (False Negative)")
        else:  # Expecting clean (True Negatives)
            if detected:
                fp += 1
                print(f"  [❌] {path.name}: False Trigger (False Positive)")
            else:
                tn += 1
                print(f"  [✅] {path.name}: Clean / Ignored (True Negative)")

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "evaluated": evaluated,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Modular Stage 1 Dual-Threshold Hysteresis Validation Harness"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to YOLO weights. If not provided, it is dynamically resolved from the configuration.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pipeline_config.yaml",
        help="Path to central pipeline config containing gating parameters",
    )
    parser.add_argument(
        "--splits",
        type=str,
        default="configs/data/val_splits.yaml",
        help="Path to validation splits YAML",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image resolution size",
    )
    parser.add_argument(
        "--device", type=str, default=None, help="Hardware target (e.g., cuda:0)"
    )
    parser.add_argument(
        "--high", type=float, default=None, help="Override high hysteresis threshold"
    )
    parser.add_argument(
        "--low", type=float, default=None, help="Override low hysteresis threshold"
    )
    args = parser.parse_args()

    pipeline_cfg = load_pipeline_config(args.config)
    splits_cfg = load_yaml(args.splits)

    gating = pipeline_cfg.get("gating_thresholds", {})
    pixel_thresh_high = (
        args.high if args.high is not None else gating.get("pixel_thresh_high", 0.47)
    )
    pixel_thresh_low = (
        args.low if args.low is not None else gating.get("pixel_thresh_low", 0.35)
    )
    min_cc_area = gating.get("min_cc_area", 20)
    max_cc_area_reject = gating.get("max_cc_area_reject", 5000)

    imgsz = (
        args.imgsz
        if args.imgsz != 640
        else pipeline_cfg.get("dataset", {}).get("imgsz", 640)
    )

    if args.model is None:
        project_name = pipeline_cfg.get("project", {}).get(
            "name", "car_defect_detection"
        )
        run_name = pipeline_cfg.get("project", {}).get("run_name", "experiment_run")
        model_path = os.path.join(project_name, run_name, "weights", "best.pt")
    else:
        model_path = args.model

    print("=" * 85)
    print(" 🛡️  MODULAR STAGE 1 VALIDATION HARNESS (SOFTMAX ACTIVATED)")
    print("=" * 85)
    print(f"[i] Model:              {args.model}")
    print(f"[i] Gating Parameters:  high={pixel_thresh_high}, low={pixel_thresh_low}")
    print(
        f"                        min_area={min_cc_area}, max_area_reject={max_cc_area_reject}"
    )
    print("=" * 85)

    router = RawStage1Router(
        model_path=model_path,
        pixel_thresh_high=pixel_thresh_high,
        pixel_thresh_low=pixel_thresh_low,
        min_cc_area=min_cc_area,
        max_cc_area_reject=max_cc_area_reject,
        device=args.device,
    )

    cal_res = evaluate_set(
        router,
        splits_cfg.get("calibration_files", []),
        "Calibration Images",
        expected_outcome=True,
        imgsz=imgsz,
    )
    ho_res = evaluate_set(
        router,
        splits_cfg.get("held_out_defect_files", []),
        "Held-Out Defect Files",
        expected_outcome=True,
        imgsz=imgsz,
    )
    clean_res = evaluate_set(
        router,
        splits_cfg.get("clean_files", []),
        "Clean Background Files",
        expected_outcome=False,
        imgsz=imgsz,
    )

    # 4. Calculate Final Metrics
    cal_evaluated = cal_res["evaluated"]
    cal_recall = (cal_res["tp"] / cal_evaluated) * 100 if cal_evaluated > 0 else 0.0

    ho_total = ho_res["tp"] + ho_res["fn"]
    held_out_recall = (ho_res["tp"] / ho_total) * 100 if ho_total > 0 else 0.0

    agg_tp = cal_res["tp"] + ho_res["tp"]
    agg_total = cal_evaluated + ho_total
    aggregate_recall = (agg_tp / agg_total) * 100 if agg_total > 0 else 0.0

    clean_total = clean_res["fp"] + clean_res["tn"]
    fpr = (clean_res["fp"] / clean_total) * 100 if clean_total > 0 else 0.0

    # 5. Output Report
    print("\n" + "=" * 85)
    print(" STATISTICAL PERFORMANCE MATRIX")
    print("=" * 85)
    print(f"  Calibration Recall (n={cal_evaluated}):      {cal_recall:.2f}%")
    print(
        f"  Held-Out Recall (n={ho_total}):          {held_out_recall:.2f}%  "
        "<-- REAL Performance"
    )
    print(f"  Aggregate Recall (n={agg_total}):        {aggregate_recall:.2f}%")
    print(f"  False Positive Rate (n={clean_total}):     {fpr:.2f}%")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    main()
