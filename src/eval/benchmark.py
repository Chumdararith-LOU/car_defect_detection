import os
import time
import argparse
import yaml
import numpy as np
import cv2
import torch
import psutil
from pathlib import Path
from src.inference.router import RawStage1Router
from src.utils.config_helpers import load_pipeline_config


def load_yaml(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_peak_memory():
    """Returns current RAM usage in MB, and VRAM if CUDA is available."""
    process = psutil.Process(os.getpid())
    ram_mb = process.memory_info().rss / (1024 * 1024)
    vram_mb = 0.0
    if torch.cuda.is_available():
        vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
    return ram_mb, vram_mb


def get_defect_size_bucket(mask_path):
    """Categorizes ground truth mask by defect pixel area."""
    if not os.path.exists(mask_path):
        return None
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    area = np.sum(mask > 0)
    if area == 0:
        return None
    if area < 1000:
        return "Small"
    elif area < 10000:
        return "Medium"
    else:
        return "Large"


def profile_stages(router, img, imgsz):
    """Profiles the pipeline stages step-by-step to isolate execution costs."""
    # 1. Tiling Preprocessing
    t0 = time.perf_counter()
    h_orig, w_orig = img.shape[:2]
    tile_bounds = router.get_tile_coords(h_orig, w_orig)

    tiles = []
    for (y0, y1), (x0, x1) in tile_bounds:
        tile_crop = img[y0:y1, x0:x1]
        tile_resized = cv2.resize(tile_crop, (imgsz, imgsz))
        tiles.append((tile_resized, (y0, y1), (x0, x1), tile_crop.shape[:2]))
    t_tile_prep = (time.perf_counter() - t0) * 1000

    # 2. Model Inference Forward Pass
    t0 = time.perf_counter()
    tile_probs = []
    for tile_resized, _, _, _ in tiles:
        img_tensor = (
            (
                torch.from_numpy(tile_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            .unsqueeze(0)
            .to(router.device)
        )

        with torch.no_grad():
            raw_output = router.net(img_tensor)

        logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output

        if logits.shape[1] == 1:
            extended_logits = torch.cat([torch.zeros_like(logits), logits], dim=1)
            probs = torch.softmax(extended_logits, dim=1)
        else:
            probs = torch.softmax(logits, dim=1)

        raw_probs_map = probs[0, 1, :, :].cpu().numpy()
        tile_probs.append(raw_probs_map)

    if router.device.type == "cuda":
        torch.cuda.synchronize()
    elif router.device.type == "mps":
        _ = img_tensor.cpu()
    t_inference = (time.perf_counter() - t0) * 1000

    # 3. Stitching Postprocessing
    t0 = time.perf_counter()
    global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)
    for idx, (_, (y0, y1), (x0, x1), (t_h, t_w)) in enumerate(tiles):
        tile_probs_resized = cv2.resize(
            tile_probs[idx], (t_w, t_h), interpolation=cv2.INTER_LINEAR
        )
        global_probs[y0:y1, x0:x1] = np.maximum(
            global_probs[y0:y1, x0:x1], tile_probs_resized
        )
    t_tile_post = (time.perf_counter() - t0) * 1000

    # 4. Hysteresis Double-Gate Gating
    t0 = time.perf_counter()
    router.run_hysteresis_gate(global_probs)
    t_hysteresis = (time.perf_counter() - t0) * 1000

    return t_tile_prep, t_inference, t_tile_post, t_hysteresis


def main():
    parser = argparse.ArgumentParser(
        description="Stage 1 Industrial Gatekeeper Hardware Benchmark"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/pipeline_config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--splits",
        type=str,
        default="configs/data/val_splits.yaml",
        help="Path to splits file",
    )
    parser.add_argument(
        "--iterations", type=int, default=20, help="Performance profiling iterations"
    )
    parser.add_argument("--warmup", type=int, default=5, help="GPU warmup runs")
    args = parser.parse_args()

    # Load configurations
    cfg = load_pipeline_config(args.config)
    splits = load_yaml(args.splits)

    project_name = cfg.get("project", {}).get("name", "car_defect_detection")
    run_name = cfg.get("project", {}).get("run_name", "stage1_focal_yolo26n_run")
    imgsz = cfg.get("dataset", {}).get("imgsz", 640)

    # Dynamically resolve weights path
    model_path = os.path.join(project_name, run_name, "weights", "best.pt")
    if not os.path.exists(model_path):
        print(
            f"[!] Target run weights not found at {model_path}. Defaulting to configuration preset."
        )
        model_path = cfg.get("model", {}).get("preset", "yolo26n-sem.pt")

    # Instantiate Router
    router = RawStage1Router.from_config(
        config_path=args.config, model_path_override=model_path
    )
    device_name = str(router.device).upper()

    # Determine Model format
    model_format = "PyTorch (.pt)"
    if model_path.endswith(".onnx"):
        model_format = "ONNX (.onnx)"
    elif model_path.endswith(".engine"):
        model_format = "TensorRT (.engine)"

    # Size-Bucketed Recall and FPR Tracking
    buckets = {
        "Small": {"tp": 0, "total": 0},
        "Medium": {"tp": 0, "total": 0},
        "Large": {"tp": 0, "total": 0},
    }
    fpr_stats = {"fp": 0, "total": 0}

    print("[*] Processing accuracy evaluation over validation sets...")

    # Evaluate recall on held-out defects
    for img_path_str in splits.get("held_out_defect_files", []):
        img_path = Path(img_path_str)
        if not img_path.exists():
            continue
        mask_path = Path(img_path_str.replace("images", "masks")).with_suffix(".png")
        size_class = get_defect_size_bucket(mask_path)
        if size_class is None:
            continue

        _, _, _, detected = router.route_image(img_path, imgsz=imgsz)
        buckets[size_class]["total"] += 1
        if detected:
            buckets[size_class]["tp"] += 1

    # Evaluate FPR on clean backgrounds
    for img_path_str in splits.get("clean_files", []):
        img_path = Path(img_path_str)
        if not img_path.exists():
            continue
        _, _, _, detected = router.route_image(img_path, imgsz=imgsz)
        fpr_stats["total"] += 1
        if detected:
            fpr_stats["fp"] += 1

    # Fetch reference profiling image
    ref_image_path = "data/processed/sod/val/images/000552.jpg"
    ref_img = cv2.imread(ref_image_path)
    if ref_img is None:
        print(
            f"[!] Warning: Reference profiling image not found at {ref_image_path}. Creating blank matrix."
        )
        ref_img = np.zeros((665, 1000, 3), dtype=np.uint8)

    # Performance Latency Profiling
    print(
        f"[*] Running latency profiling: {args.warmup} warmups, {args.iterations} iterations..."
    )
    for _ in range(args.warmup):
        _ = profile_stages(router, ref_img, imgsz)

    latencies = {"tile_prep": [], "inference": [], "tile_post": [], "hysteresis": []}
    for _ in range(args.iterations):
        t_prep, t_inf, t_post, t_hyst = profile_stages(router, ref_img, imgsz)
        latencies["tile_prep"].append(t_prep)
        latencies["inference"].append(t_inf)
        latencies["tile_post"].append(t_post)
        latencies["hysteresis"].append(t_hyst)

    # Calculate p95 Latencies
    p95_prep = np.percentile(latencies["tile_prep"], 95)
    p95_inf = np.percentile(latencies["inference"], 95)
    p95_post = np.percentile(latencies["tile_post"], 95)
    p95_hyst = np.percentile(latencies["hysteresis"], 95)
    p95_total = p95_prep + p95_inf + p95_post + p95_hyst

    # Calculate Accuracies
    rec_small = (
        (buckets["Small"]["tp"] / buckets["Small"]["total"] * 100)
        if buckets["Small"]["total"] > 0
        else 0.0
    )
    rec_med = (
        (buckets["Medium"]["tp"] / buckets["Medium"]["total"] * 100)
        if buckets["Medium"]["total"] > 0
        else 0.0
    )
    rec_large = (
        (buckets["Large"]["tp"] / buckets["Large"]["total"] * 100)
        if buckets["Large"]["total"] > 0
        else 0.0
    )
    fpr_rate = (
        (fpr_stats["fp"] / fpr_stats["total"] * 100) if fpr_stats["total"] > 0 else 0.0
    )

    ram_mb, vram_mb = get_peak_memory()
    mem_footprint = f"{ram_mb:.1f} MB" if vram_mb == 0.0 else f"{vram_mb:.1f} MB (VRAM)"

    # Print ASCII Report
    print("\n┌" + "─" * 88 + "┐")
    print(f"│{'STAGE 1 INDUSTRIAL GATEKEEPER BENCHMARK REPORT':^88}│")
    print(
        "├"
        + "─" * 15
        + "┬"
        + "─" * 10
        + "┬"
        + "─" * 12
        + "┬"
        + "─" * 36
        + "┬"
        + "─" * 11
        + "┤"
    )
    print(
        f"│ {'Model Format':<13} │ {'Target':<8} │ {'Inf. (p95)':<10} │ {'Size-Bucketed Recall (S/M/L)':<34} │ {'FP Rate':<9} │"
    )
    print(
        "├"
        + "─" * 15
        + "┼"
        + "─" * 10
        + "┼"
        + "─" * 12
        + "┼"
        + "─" * 36
        + "┼"
        + "─" * 11
        + "┤"
    )
    recall_str = f"S:{rec_small:.1f}% | M:{rec_med:.1f}% | L:{rec_large:.1f}%"
    print(
        f"│ {model_format:<13} │ {device_name:<8} │ {p95_total:5.1f} ms   │ {recall_str:<34} │ {fpr_rate:6.2f}%   │"
    )
    print(
        "└"
        + "─" * 15
        + "┴"
        + "─" * 10
        + "┴"
        + "─" * 12
        + "┴"
        + "─" * 36
        + "┴"
        + "─" * 11
        + "┘"
    )

    print("\n" + "=" * 90)
    print(" ⏱️  P95 COMPONENT-LEVEL LATENCY BREAKDOWN")
    print("=" * 90)
    print(f"  - Tiling Preprocessing:     {p95_prep:6.2f} ms")
    print(f"  - Neural Network Inference:  {p95_inf:6.2f} ms  <-- Core Model Speed")
    print(f"  - Tiling Postprocessing:    {p95_post:6.2f} ms")
    print(f"  - Hysteresis Routing Gate:   {p95_hyst:6.2f} ms")
    print(f"  - Total Pipeline Latency:    {p95_total:6.2f} ms")
    print(f"  - Active Memory Footprint:   {mem_footprint}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
