import os
import time
import yaml
import numpy as np
import cv2
import torch
from stage1.inference.router import RawStage1Router

MODELS_SUITE = [
    {
        "id": "Model 1",
        "name": "Nano (Focal, 1024px)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/122e3f76a2ee4d6abbcc94698b217266/artifacts/weights/best.pt",
        "imgsz": 1024,
        "backbone": "yolo26n",
        "gating": {"high": 0.47, "low": 0.35, "min_cc": 20, "max_cc": 5000},
    },
    {
        "id": "Model 2",
        "name": "Nano (Focal, 640px, B32)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/403d6b3100d24013ad035979df412e97/artifacts/weights/best.pt",
        "imgsz": 640,
        "backbone": "yolo26n",
        "gating": {"high": 0.47, "low": 0.35, "min_cc": 20, "max_cc": 5000},
    },
    {
        "id": "Model 3",
        "name": "Medium (Focal, 640px)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt",
        "imgsz": 640,
        "backbone": "yolo26m",
        "gating": {"high": 0.28, "low": 0.18, "min_cc": 20, "max_cc": 999999},
    },
    {
        "id": "Model 4",
        "name": "Medium (CE, 640px, B32)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt",
        "imgsz": 640,
        "backbone": "yolo26m",
        "gating": {
            "high": 0.70,
            "low": 0.70,
            "min_cc": 0,
            "max_cc": 999999,
        },  # Single Threshold
    },
    {
        "id": "Model 5",
        "name": "Medium (CE, 640px, B16)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/fa5389756f3e4704af9f25c56bb4cccb/artifacts/weights/best.pt",
        "imgsz": 640,
        "backbone": "yolo26m",
        "gating": {
            "high": 0.70,
            "low": 0.70,
            "min_cc": 0,
            "max_cc": 999999,
        },  # Single Threshold
    },
    {
        "id": "Model 6",
        "name": "Nano (CE, 640px, B16)",
        "path": "/home/rith/secure_workspace/car_defect_detection/mlruns/1/0b8ace4baec142448ce7e06434938ac2/artifacts/weights/best.pt",
        "imgsz": 640,
        "backbone": "yolo26n",
        "gating": {
            "high": 0.70,
            "low": 0.70,
            "min_cc": 0,
            "max_cc": 999999,
        },  # Single Threshold
    },
]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_defect_size_bucket(mask_path):
    if not os.path.exists(mask_path):
        return None
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return None
    area = np.sum(mask > 0)
    if area == 0:
        return None
    return "Small" if area < 1000 else ("Medium" if area < 10000 else "Large")


def profile_latency(router, img, imgsz, warmups=3, iterations=10):
    for _ in range(warmups):
        _, _, _, _ = router.route_image(img, imgsz=imgsz)

    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _, _, _, _ = router.route_image(img, imgsz=imgsz)
        latencies.append((time.perf_counter() - t0) * 1000)

    return np.percentile(latencies, 95)


def main():
    splits_path = "configs/data/val_splits.yaml"
    if not os.path.exists(splits_path):
        print(f"[!] Target splits missing at {splits_path}")
        return
    splits = load_yaml(splits_path)

    ref_image_path = "data/processed/sod/val/images/000552.jpg"

    print("=" * 110)
    print(
        f" 🚀 RUNNING MULTI-MODEL COMPARATIVE SUITE ON {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}"
    )
    print("=" * 110)

    results = []

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    for m in MODELS_SUITE:
        if not os.path.exists(m["path"]):
            print(f"[!] {m['id']} missing weights file at: {m['path']}. Skipping.")
            continue

        print(f"[*] Profiling {m['id']}: {m['name']}...")

        # Instantiate dynamic router settings bound to your RTX 3090
        router = RawStage1Router(
            model_path=m["path"],
            pixel_thresh_high=m["gating"]["high"],
            pixel_thresh_low=m["gating"]["low"],
            min_cc_area=m["gating"]["min_cc"],
            max_cc_area_reject=m["gating"]["max_cc"],
            overlap_frac=0.15,
            device=device,
        )

        # Accuracy evaluations
        buckets = {
            "Small": {"tp": 0, "total": 0},
            "Medium": {"tp": 0, "total": 0},
            "Large": {"tp": 0, "total": 0},
        }
        fpr_stats = {"fp": 0, "total": 0}

        for img_str in splits.get("held_out_defect_files", []):
            if not os.path.exists(img_str):
                continue
            mask_str = img_str.replace("images", "masks").replace(".jpg", ".png")
            size_class = get_defect_size_bucket(mask_str)
            if not size_class:
                continue

            _, _, _, detected = router.route_image(img_str, imgsz=m["imgsz"])
            buckets[size_class]["total"] += 1
            if detected:
                buckets[size_class]["tp"] += 1

        for img_str in splits.get("clean_files", []):
            if not os.path.exists(img_str):
                continue
            _, _, _, detected = router.route_image(img_str, imgsz=m["imgsz"])
            fpr_stats["total"] += 1
            if detected:
                fpr_stats["fp"] += 1

        # Latency calculations
        p95_time = profile_latency(router, ref_image_path, m["imgsz"])

        # Metrics formatting
        rec_s = (
            (buckets["Small"]["tp"] / buckets["Small"]["total"] * 100)
            if buckets["Small"]["total"] > 0
            else 0.0
        )
        rec_m = (
            (buckets["Medium"]["tp"] / buckets["Medium"]["total"] * 100)
            if buckets["Medium"]["total"] > 0
            else 0.0
        )
        rec_l = (
            (buckets["Large"]["tp"] / buckets["Large"]["total"] * 100)
            if buckets["Large"]["total"] > 0
            else 0.0
        )
        fpr = (
            (fpr_stats["fp"] / fpr_stats["total"] * 100)
            if fpr_stats["total"] > 0
            else 0.0
        )

        results.append(
            {
                "id": m["id"],
                "name": m["name"],
                "arch": m["backbone"],
                "res": m["imgsz"],
                "p95": p95_time,
                "recall": f"S:{rec_s:.1f}%|M:{rec_m:.1f}%|L:{rec_l:.1f}%",
                "fpr": f"{fpr:.1f}%",
            }
        )

    # Print Final Academic Comparison Table
    print("\n" + "┌" + "─" * 113 + "┐")
    print(
        f"│{'STAGE 1 MODEL SELECTION MATRIX (PRODUCTION EXPERIMENTS EVALUATION)':^113}│"
    )
    print(
        "├"
        + "─" * 8
        + "┬"
        + "─" * 26
        + "┬"
        + "─" * 10
        + "┬"
        + "─" * 8
        + "┬"
        + "─" * 14
        + "┬"
        + "─" * 32
        + "┬"
        + "─" * 10
        + "┤"
    )
    print(
        f"│ {'ID':<6} │ {'Experiment Configuration':<24} │ {'Arch':<8} │ {'Res':<6} │ {'Latency (p95)':<12} │ {'Size-Bucketed Recall (S/M/L)':<30} │ {'FP Rate':<8} │"
    )
    print(
        "├"
        + "─" * 8
        + "┼"
        + "─" * 26
        + "┼"
        + "─" * 10
        + "┼"
        + "─" * 8
        + "┼"
        + "─" * 14
        + "┼"
        + "─" * 32
        + "┼"
        + "─" * 10
        + "┤"
    )
    for r in results:
        print(
            f"│ {r['id']:<6} │ {r['name']:<24} │ {r['arch']:<8} │ {r['res']:<6} │ {r['p95']:7.1f} ms    │ {r['recall']:<30} │ {r['fpr']:<8} │"
        )
    print(
        "└"
        + "─" * 8
        + "┴"
        + "─" * 26
        + "┴"
        + "─" * 10
        + "┴"
        + "─" * 8
        + "┴"
        + "─" * 14
        + "┴"
        + "─" * 32
        + "┴"
        + "─" * 10
        + "┘\n"
    )


if __name__ == "__main__":
    main()
