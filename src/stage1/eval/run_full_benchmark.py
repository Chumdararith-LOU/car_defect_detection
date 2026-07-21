#!/usr/bin/env python3
"""
run_full_benchmark.py
======================
Unified evaluation + visual comparison pipeline for the 6 trained YOLO26-sem
checkpoints (paths taken from run_server_matrix.sh / benchmark.py).

For every model this script will:
  1. Run inference over the full test set (defect + clean images).
  2. Compute the same speed/accuracy matrix as benchmark.py:
     recall, size-bucketed recall (Small/Medium/Large), FPR, mIoU,
     p95 latency, and memory footprint.
  3. Save GT-vs-prediction comparison images (like visualize_test_predictions.py)
     so you can *see* where each model succeeds or fails, with dedicated
     folders for the cases that actually matter when comparing models:
       - small_defects/    every Small-bucket case (hairline crack/scratch),
                            hit or miss -> this is where models usually differ
       - missed_defects/   every false negative, any size
       - false_positives/  clean images the model wrongly flagged
       - all/              (optional, --save-all) every processed image
  4. Print a consolidated matrix, export it to CSV, and recommend a "best"
     model using a configurable weighted score (small-defect recall is
     weighted heaviest since that's the hardest case).

Usage:
    python run_full_benchmark.py
    python run_full_benchmark.py --save-all
    python run_full_benchmark.py --splits configs/data/val_splits.yaml --device cuda:0
"""

import os
import csv
import cv2
import time
import yaml
import torch
import psutil
import argparse
import numpy as np
from glob import glob
from pathlib import Path
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Paths & model registry (same 6 checkpoints as run_server_matrix.sh)
# ---------------------------------------------------------------------------
VAL_SPLITS_PATH = "configs/data/val_splits.yaml"
DEFAULT_IMG_DIR = "data/processed/sod/test/images"
DEFAULT_MASK_DIR = "data/processed/sod/test/masks"
OUTPUT_ROOT = "predictions_stitched"

MODELS_CONFIG = [
    {
        "name": "M1_yolo26n_1024_tiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt",
        "imgsz": 1024,
    },
    {
        "name": "M2_yolo26n_640_tiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt",
        "imgsz": 640,
    },
    {
        "name": "M3_yolo26m_640_tiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt",
        "imgsz": 640,
    },
    {
        "name": "M4_yolo26m_640_untiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt",
        "imgsz": 640,
    },
    {
        "name": "M5_yolo26m_640_untiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/fa5389756f3e4704af9f25c56bb4cccb/artifacts/weights/best.pt",
        "imgsz": 640,
    },
    {
        "name": "M6_yolo26n_640_untiled",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt",
        "imgsz": 640,
    },
]

SMALL_AREA_MAX = 1000  # px; area < this -> "Small" (hairline scratch / small crack)
MEDIUM_AREA_MAX = 10000  # px; area < this -> "Medium", else "Large"

# Weights for the composite "best model" score. Tune to your priorities.
# small_recall is weighted heaviest because catching hairline/small defects
# is usually the whole point of this comparison.
SCORE_WEIGHTS = {
    "small_recall": 0.40,
    "overall_recall": 0.25,
    "fpr": 0.15,  # lower FPR is better, scored as (1 - fpr)
    "miou": 0.10,
    "latency": 0.10,  # lower latency is better, normalized against slowest model
}

np.random.seed(42)
COLOR_PALETTE = np.random.randint(0, 255, size=(256, 3), dtype=np.uint8)
COLOR_PALETTE[0] = [0, 0, 0]  # background stays uncolored


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_peak_memory(device):
    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / (1024 * 1024)
    vram_mb = 0.0
    if torch.cuda.is_available():
        vram_mb = torch.cuda.max_memory_allocated(device=device) / (1024 * 1024)
    return ram_mb, vram_mb


def get_defect_size_bucket(mask):
    if mask is None:
        return None
    area = int(np.sum(mask > 0))
    if area == 0:
        return None
    if area < SMALL_AREA_MAX:
        return "Small"
    elif area < MEDIUM_AREA_MAX:
        return "Medium"
    return "Large"


def apply_mask_overlay(image, mask, palette, alpha=0.4):
    """Maps class IDs to colors and overlays them onto the original image."""
    colored_mask = palette[mask]
    mask_pixel_cond = mask > 0
    overlay = image.copy()
    overlay[mask_pixel_cond] = cv2.addWeighted(
        image, 1 - alpha, colored_mask, alpha, 0
    )[mask_pixel_cond]
    return overlay


def add_label_text(image, lines):
    """Draws one or more lines of text in the top-left corner with a dark outline."""
    img_labeled = image.copy()
    if isinstance(lines, str):
        lines = [lines]
    for i, text in enumerate(lines):
        y = 35 + i * 32
        cv2.putText(
            img_labeled,
            text,
            (15, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            img_labeled,
            text,
            (15, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return img_labeled


def get_pred_mask(result, ref_shape):
    """Extract a semantic prediction mask from a YOLO26-sem result object, resized to ref_shape."""
    if hasattr(result, "semantic_mask") and result.semantic_mask is not None:
        pred_mask = result.semantic_mask.data.cpu().numpy().astype(np.uint8)
    elif hasattr(result, "masks") and result.masks is not None:
        pred_mask = result.masks.data[0].cpu().numpy().astype(np.uint8)
    else:
        pred_mask = np.zeros(ref_shape, dtype=np.uint8)

    if pred_mask.shape[:2] != ref_shape:
        pred_mask = cv2.resize(
            pred_mask, (ref_shape[1], ref_shape[0]), interpolation=cv2.INTER_NEAREST
        )
    return pred_mask


def save_comparison(
    out_dir,
    basename,
    img,
    gt_mask,
    pred_mask,
    model_name,
    extra_lines_gt,
    extra_lines_pred,
):
    os.makedirs(out_dir, exist_ok=True)
    gt_overlay = apply_mask_overlay(img, gt_mask, COLOR_PALETTE)
    pred_overlay = apply_mask_overlay(
        img, (pred_mask > 0).astype(np.uint8), COLOR_PALETTE
    )

    gt_overlay = add_label_text(gt_overlay, ["Ground Truth"] + extra_lines_gt)
    pred_overlay = add_label_text(
        pred_overlay, [f"Pred: {model_name}"] + extra_lines_pred
    )

    stitched = np.hstack((gt_overlay, pred_overlay))
    save_path = os.path.join(out_dir, f"comparison_{basename}.png")
    cv2.imwrite(save_path, stitched)


# ---------------------------------------------------------------------------
# Dataset resolution / caching (mirrors benchmark.py)
# ---------------------------------------------------------------------------
def resolve_dataset(splits_path, img_dir, mask_dir):
    splits = load_yaml(splits_path)
    defect_paths, clean_paths = [], []

    if splits:
        defect_paths = [
            p for p in splits.get("held_out_defect_files", []) if os.path.exists(p)
        ]
        clean_paths = [p for p in splits.get("clean_files", []) if os.path.exists(p)]

    if not defect_paths and os.path.exists(img_dir):
        for p in glob(os.path.join(img_dir, "*")):
            fn = os.path.basename(p)
            mask_p = os.path.join(mask_dir, fn)
            if (
                os.path.exists(mask_p)
                and np.sum(cv2.imread(mask_p, cv2.IMREAD_GRAYSCALE) > 0) > 0
            ):
                defect_paths.append(p)
            else:
                clean_paths.append(p)

    return defect_paths, clean_paths


def cache_dataset(defect_paths, clean_paths, mask_dir):
    """Pre-loads images/masks once so all 6 models are compared on identical, disk-I/O-free data."""
    cached_defects = []
    for p in defect_paths:
        img = cv2.imread(p)
        fn = os.path.basename(p)
        basename = Path(fn).stem
        mask_p = os.path.join(mask_dir, basename + ".png")
        if not os.path.exists(mask_p):
            mask_p = os.path.join(mask_dir, fn)
        gt_mask = (
            cv2.imread(mask_p, cv2.IMREAD_GRAYSCALE) if os.path.exists(mask_p) else None
        )
        if img is None or gt_mask is None:
            continue
        gt_mask = (gt_mask > 0).astype(np.uint8)
        cached_defects.append(
            {
                "img": img,
                "mask": gt_mask,
                "bucket": get_defect_size_bucket(gt_mask),
                "basename": basename,
            }
        )

    cached_cleans = []
    for p in clean_paths:
        img = cv2.imread(p)
        if img is None:
            continue
        cached_cleans.append({"img": img, "basename": Path(os.path.basename(p)).stem})

    return cached_defects, cached_cleans


# ---------------------------------------------------------------------------
# Per-model evaluation
# ---------------------------------------------------------------------------
def evaluate_model(cfg, cached_defects, cached_cleans, device, save_all):
    name = cfg["name"]
    path = cfg["path"]
    imgsz = cfg["imgsz"]

    if not os.path.exists(path):
        print(f"[!] Warning: Missing weights checkpoint for {name} -> {path}")
        return None

    print(f"[*] Profiling {name}...")

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model = YOLO(path).to(device)
    model.model.eval()

    # Warmup pass
    if cached_defects:
        _ = model(cached_defects[0]["img"], device=device, verbose=False, imgsz=imgsz)

    buckets = {
        "Small": {"tp": 0, "total": 0},
        "Medium": {"tp": 0, "total": 0},
        "Large": {"tp": 0, "total": 0},
    }
    global_tp, global_fn, global_fp, global_tn = 0, 0, 0, 0
    iou_scores = []
    latencies = []

    model_out_dir = os.path.join(OUTPUT_ROOT, name)
    small_dir = os.path.join(model_out_dir, "small_defects")
    missed_dir = os.path.join(model_out_dir, "missed_defects")
    fp_dir = os.path.join(model_out_dir, "false_positives")
    all_dir = os.path.join(model_out_dir, "all")

    # --- Defect images -----------------------------------------------------
    for item in cached_defects:
        if torch.cuda.is_available():
            torch.cuda.synchronize(device=device)
        t0 = time.perf_counter()

        outputs = model(item["img"], device=device, verbose=False, imgsz=imgsz)
        res = outputs[0]
        pred_mask = get_pred_mask(res, item["mask"].shape)

        if torch.cuda.is_available():
            torch.cuda.synchronize(device=device)
        latencies.append((time.perf_counter() - t0) * 1000.0)

        pred_mask_bin = (pred_mask > 0).astype(np.uint8)
        detected = bool(np.any(pred_mask_bin > 0))

        b_type = item["bucket"]
        if b_type in buckets:
            buckets[b_type]["total"] += 1
            if detected:
                buckets[b_type]["tp"] += 1

        if detected:
            global_tp += 1
        else:
            global_fn += 1

        intersection = np.logical_and(item["mask"], pred_mask_bin).sum()
        union = np.logical_or(item["mask"], pred_mask_bin).sum()
        iou = 1.0 if union == 0 else intersection / union
        iou_scores.append(iou)

        status = "DETECTED (TP)" if detected else "MISSED (FN)"
        gt_lines = [f"Bucket: {b_type}", f"Area: {int(item['mask'].sum())}px"]
        pred_lines = [status, f"IoU: {iou:.2f}"]

        # Small defects (hairline crack/scratch) always get saved for review.
        if b_type == "Small":
            save_comparison(
                small_dir,
                item["basename"],
                item["img"],
                item["mask"],
                pred_mask_bin,
                name,
                gt_lines,
                pred_lines,
            )
        # Any missed defect, regardless of size, always gets saved for review.
        if not detected:
            save_comparison(
                missed_dir,
                item["basename"],
                item["img"],
                item["mask"],
                pred_mask_bin,
                name,
                gt_lines,
                pred_lines,
            )
        if save_all:
            save_comparison(
                all_dir,
                item["basename"],
                item["img"],
                item["mask"],
                pred_mask_bin,
                name,
                gt_lines,
                pred_lines,
            )

    # --- Clean images --------------------------------------------------------
    for item in cached_cleans:
        if torch.cuda.is_available():
            torch.cuda.synchronize(device=device)
        t0 = time.perf_counter()

        outputs = model(item["img"], device=device, verbose=False, imgsz=imgsz)
        res = outputs[0]
        pred_mask = get_pred_mask(res, item["img"].shape[:2])

        if torch.cuda.is_available():
            torch.cuda.synchronize(device=device)
        latencies.append((time.perf_counter() - t0) * 1000.0)

        pred_mask_bin = (pred_mask > 0).astype(np.uint8)
        detected = bool(np.any(pred_mask_bin > 0))

        if detected:
            global_fp += 1
        else:
            global_tn += 1
        iou_scores.append(0.0 if detected else 1.0)

        empty_mask = np.zeros(item["img"].shape[:2], dtype=np.uint8)
        if detected:
            save_comparison(
                fp_dir,
                item["basename"],
                item["img"],
                empty_mask,
                pred_mask_bin,
                name,
                ["Clean (no defect)"],
                ["FALSE POSITIVE"],
            )
        elif save_all:
            save_comparison(
                all_dir,
                item["basename"],
                item["img"],
                empty_mask,
                pred_mask_bin,
                name,
                ["Clean (no defect)"],
                ["TRUE NEGATIVE"],
            )

    # --- Aggregate stats -------------------------------------------------
    rec_s = (
        (buckets["Small"]["tp"] / buckets["Small"]["total"] * 100)
        if buckets["Small"]["total"] > 0
        else None
    )
    rec_m = (
        (buckets["Medium"]["tp"] / buckets["Medium"]["total"] * 100)
        if buckets["Medium"]["total"] > 0
        else None
    )
    rec_l = (
        (buckets["Large"]["tp"] / buckets["Large"]["total"] * 100)
        if buckets["Large"]["total"] > 0
        else None
    )

    total_defects = global_tp + global_fn
    overall_recall = (global_tp / total_defects * 100) if total_defects > 0 else 0.0
    total_cleans = global_fp + global_tn
    fpr_rate = (global_fp / total_cleans * 100) if total_cleans > 0 else 0.0

    p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
    mean_iou = float(np.mean(iou_scores)) * 100 if iou_scores else 0.0
    ram_mb, vram_mb = get_peak_memory(device)

    return {
        "name": name,
        "overall_recall": overall_recall,
        "small_recall": rec_s,
        "medium_recall": rec_m,
        "large_recall": rec_l,
        "fpr": fpr_rate,
        "miou": mean_iou,
        "p95_latency_ms": p95_latency,
        "vram_mb": vram_mb,
        "ram_mb": ram_mb,
        "small_total": buckets["Small"]["total"],
        "medium_total": buckets["Medium"]["total"],
        "large_total": buckets["Large"]["total"],
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def format_pct(value):
    return f"{value:.1f}%" if value is not None else "n/a"


def print_dashboard(results):
    print("\n┌" + "─" * 123 + "┐")
    print(f"│{'UNIFIED YOLO26-SEM MODEL COMPARISON MATRIX':^123}│")
    print(
        "├"
        + "─" * 27
        + "┬"
        + "─" * 10
        + "┬"
        + "─" * 25
        + "┬"
        + "─" * 11
        + "┬"
        + "─" * 11
        + "┬"
        + "─" * 16
        + "┬"
        + "─" * 15
        + "┤"
    )
    print(
        f"│ {'Model Run Identifier':<25} │ {'Recall':<8} │ {'Size-Bucketed (S/M/L)':<23} │ {'FPR Rate':<9} │ {'mIoU':<9} │ {'p95 Latency':<14} │ {'Memory footprint':<13} │"
    )
    print(
        "├"
        + "─" * 27
        + "┼"
        + "─" * 10
        + "┼"
        + "─" * 25
        + "┼"
        + "─" * 11
        + "┼"
        + "─" * 11
        + "┼"
        + "─" * 16
        + "┼"
        + "─" * 15
        + "┤"
    )
    for r in results:
        bucket_str = f"S:{format_pct(r['small_recall'])}|M:{format_pct(r['medium_recall'])}|L:{format_pct(r['large_recall'])}"
        mem_str = (
            f"{r['vram_mb']:.1f} MB"
            if r["vram_mb"] > 0
            else f"{r['ram_mb']:.1f} MB (RAM)"
        )
        latency_str = f"{r['p95_latency_ms']:.1f} ms"
        print(
            f"│ {r['name']:<25} │ {format_pct(r['overall_recall']):<8} │ {bucket_str:<23} │ {format_pct(r['fpr']):<9} │ {format_pct(r['miou']):<9} │ {latency_str:<14} │ {mem_str:<13} │"
        )
    print("└" + "─" * 123 + "┘\n")


def pick_best_model(results, weights):
    if not results:
        return []

    max_latency = max(r["p95_latency_ms"] for r in results) or 1.0

    scored = []
    for r in results:
        small_r = (
            r["small_recall"] if r["small_recall"] is not None else r["overall_recall"]
        )
        latency_score = 1.0 - (r["p95_latency_ms"] / max_latency)
        score = (
            weights["small_recall"] * (small_r / 100.0)
            + weights["overall_recall"] * (r["overall_recall"] / 100.0)
            + weights["fpr"] * (1.0 - r["fpr"] / 100.0)
            + weights["miou"] * (r["miou"] / 100.0)
            + weights["latency"] * latency_score
        )
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def export_csv(results, path):
    if not results:
        return
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    fieldnames = list(results[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global OUTPUT_ROOT

    parser = argparse.ArgumentParser(
        description="Unified YOLO26-sem model comparison: benchmark + visual matrix"
    )
    parser.add_argument("--splits", type=str, default=VAL_SPLITS_PATH)
    parser.add_argument("--img-dir", type=str, default=DEFAULT_IMG_DIR)
    parser.add_argument("--mask-dir", type=str, default=DEFAULT_MASK_DIR)
    parser.add_argument("--output-dir", type=str, default=OUTPUT_ROOT)
    parser.add_argument(
        "--save-all",
        action="store_true",
        help="Also save a stitched comparison for every single image, not just small/missed/false-positive cases.",
    )
    parser.add_argument(
        "--device", type=str, default="cuda:0" if torch.cuda.is_available() else "cpu"
    )
    args = parser.parse_args()

    OUTPUT_ROOT = args.output_dir
    device = torch.device(args.device)

    defect_paths, clean_paths = resolve_dataset(
        args.splits, args.img_dir, args.mask_dir
    )
    total_images = len(defect_paths) + len(clean_paths)
    if total_images == 0:
        print("[!] Error: No validation assets located.")
        return

    print("=" * 120)
    print(
        f"🚀 RUNNING UNIFIED BENCHMARK + VISUAL COMPARISON OVER {total_images} IMAGES "
        f"({len(defect_paths)} defect / {len(clean_paths)} clean) ON {device}"
    )
    print("=" * 120)

    cached_defects, cached_cleans = cache_dataset(
        defect_paths, clean_paths, args.mask_dir
    )

    results = []
    for cfg in MODELS_CONFIG:
        r = evaluate_model(cfg, cached_defects, cached_cleans, device, args.save_all)
        if r is not None:
            results.append(r)

    if not results:
        print(
            "[!] No models were evaluated (all checkpoints missing?). Nothing to report."
        )
        return

    print_dashboard(results)

    csv_path = os.path.join(OUTPUT_ROOT, "benchmark_matrix.csv")
    export_csv(results, csv_path)
    print(f"[i] Full metrics exported to {csv_path}")

    ranked = pick_best_model(results, SCORE_WEIGHTS)
    best_score, best = ranked[0]
    print("=" * 120)
    print(
        "🏆 RECOMMENDED MODEL (weighted score - see SCORE_WEIGHTS at top of file to tune priorities)"
    )
    print("=" * 120)
    print(f"  {best['name']}  (score={best_score:.3f})")
    print(
        f"    - Small-defect recall : {format_pct(best['small_recall'])}  <- weighted heaviest (hairline/small defects are the hardest case)"
    )
    print(f"    - Overall recall      : {format_pct(best['overall_recall'])}")
    print(f"    - False positive rate : {format_pct(best['fpr'])}")
    print(f"    - mIoU                : {format_pct(best['miou'])}")
    print(f"    - p95 latency         : {best['p95_latency_ms']:.1f} ms")
    print()
    print("  Full ranking:")
    for i, (score, r) in enumerate(ranked, start=1):
        print(f"    {i}. {r['name']:<25} score={score:.3f}")
    print()
    print(f"[i] Visual comparisons saved under: {OUTPUT_ROOT}/<model_name>/")
    print(
        "      - small_defects/    every Small-bucket (hairline crack/scratch) case, hit or miss"
    )
    print("      - missed_defects/   every false negative, any size")
    print("      - false_positives/  clean images the model wrongly flagged")
    if args.save_all:
        print(
            "      - all/              every single processed image (--save-all was set)"
        )


if __name__ == "__main__":
    main()
