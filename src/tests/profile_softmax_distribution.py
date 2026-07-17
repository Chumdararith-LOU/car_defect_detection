import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from src.inference.router import get_stitched_probability_map


def run_softmax_profiling():
    model_weight = "runs/semantic/runs/semantic/Automated_Car_Defect_Stage1_SOD/Stage1_SOD_FocalLoss_Full/weights/best.pt"

    print("[+] Loading retrained Stage 1 Model...")
    model = YOLO(model_weight, task="semantic")
    net = model.model
    net.eval()
    device = next(net.parameters()).device

    clean_tiles = [
        "data/processed/sod_tiled/images/val/000105_t0.png",
        "data/processed/sod_tiled/images/val/000707_t0.png",
        "data/processed/sod_tiled/images/val/000784_t0.png",
    ]

    defect_tiles = [
        "data/processed/sod_tiled/images/val/000552_t2.png",  # Branching crack tail
        "data/processed/sod_tiled/images/val/003594_t1.png",  # Door scratch
        "data/processed/sod_tiled/images/val/003074_t0.png",  # Windshield shatter
    ]

    print("\n" + "=" * 80)
    print(" 📊 PROFILING CLEAN BACKGROUND TILES (ESTABLISHING THE NOISE FLOOR)")
    print("=" * 80)
    clean_maxes = []
    for f in clean_tiles:
        path = Path(f)
        if not path.exists():
            print(f" [!] Missing: {f}")
            continue
        img = cv2.imread(str(path))
        probs = get_stitched_probability_map(
            img, net, device, overlap_frac=0.15, imgsz=1024
        )

        tile_max = float(np.max(probs))
        tile_mean = float(np.mean(probs))
        clean_maxes.append(tile_max)
        print(
            f" 🟢 {path.name:<15} | Peak Softmax: {tile_max:.5f} | Mean Noise: {tile_mean:.5f}"
        )

    print("\n" + "=" * 80)
    print(" 🔥 PROFILING CONFIRMED DEFECT TILES (ESTABLISHING THE SIGNAL PEAKS)")
    print("=" * 80)
    defect_peaks = []
    for f in defect_tiles:
        path = Path(f)
        if not path.exists():
            print(f" [!] Missing: {f}")
            continue
        img = cv2.imread(str(path))
        probs = get_stitched_probability_map(
            img, net, device, overlap_frac=0.15, imgsz=1024
        )

        tile_max = float(np.max(probs))
        tile_90th = float(np.percentile(probs, 99.9))
        defect_peaks.append(tile_max)
        print(
            f" 🔴 {path.name:<15} | Peak Softmax: {tile_max:.5f} | 99.9th Percentile: {tile_90th:.5f}"
        )

    print("\n" + "=" * 80)
    print(" 📈 HYSTERESIS CALIBRATION SUMMARY")
    print("=" * 80)
    if clean_maxes and defect_peaks:
        max_clean_noise = max(clean_maxes)
        min_defect_signal = min(defect_peaks)
        print(f"  Absolute Maximum Background Noise:      {max_clean_noise:.5f}")
        print(f"  Lowest Peak Defect Signal:              {min_defect_signal:.5f}")
        print("-" * 80)
        print("  Suggested Calibration Range:")
        print(
            f"    - Seed Anchor (tau_high):   Must be > {max_clean_noise:.5f} but < {min_defect_signal:.5f}"
        )
        print(
            "    - Pathway (tau_low):        Tuned lower to recover tails, but above mean noise."
        )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_softmax_profiling()
