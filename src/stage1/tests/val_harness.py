from pathlib import Path
from stage1.inference.router import RawStage1Router


def run_validation_harness():
    model_weight = "runs/semantic/runs/semantic/Automated_Car_Defect_Stage1_SOD/Stage1_SOD_FocalLoss_Full/weights/best.pt"

    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh_high=0.47,
        pixel_thresh_low=0.35,
        min_cc_area=20,
        max_cc_area_reject=5000,
    )

    # 10 Validation images containing confirmed hairline cracks
    calibration_files = [
        "data/processed/sod/val/images/000552.jpg",
        "data/processed/sod/val/images/000146.jpg",
        "data/processed/sod/val/images/001728.jpg",
        "data/processed/sod/val/images/003521.jpg",
        "data/processed/sod/val/images/003510.jpg",
        "data/processed/sod/val/images/003710.jpg",
        "data/processed/sod/val/images/001712.jpg",
        "data/processed/sod/val/images/003382.jpg",
        "data/processed/sod/val/images/002553.jpg",
        "data/processed/sod/val/images/001109.jpg",
        "data/processed/sod/val/images/003996.jpg",
        "data/processed/sod/val/images/003711.jpg",
        "data/processed/sod/val/images/000157.jpg",
        "data/processed/sod/val/images/000832.jpg",
        "data/processed/sod/val/images/002203.jpg",
        "data/processed/sod/val/images/000576.jpg",
    ]

    held_out_defect_files = [
        "data/processed/sod/val/images/002325.jpg",
        "data/processed/sod/val/images/002199.jpg",
        "data/processed/sod/val/images/003543.jpg",
        "data/processed/sod/val/images/002297.jpg",
        "data/processed/sod/val/images/002427.jpg",
        "data/processed/sod/val/images/001844.jpg",
        "data/processed/sod/val/images/001722.jpg",
        "data/processed/sod/val/images/000929.jpg",
        "data/processed/sod/val/images/003963.jpg",
        "data/processed/sod/val/images/002817.jpg",
        "data/processed/sod/val/images/002182.jpg",
        "data/processed/sod/val/images/001191.jpg",
        "data/processed/sod/val/images/002442.jpg",
        "data/processed/sod/val/images/002066.jpg",
        "data/processed/sod/val/images/000544.jpg",
        "data/processed/sod/val/images/000084.jpg",
        "data/processed/sod/val/images/002573.jpg",
        "data/processed/sod/val/images/001727.jpg",
        "data/processed/sod/val/images/002382.jpg",
        "data/processed/sod/val/images/002088.jpg",
        "data/processed/sod/val/images/003714.jpg",
    ]

    clean_files = [
        "data/processed/sod_tiled/images/val/000105_t0.png",
        "data/processed/sod_tiled/images/val/000157_t0.png",
        "data/processed/sod_tiled/images/val/000157_t2.png",
        "data/processed/sod_tiled/images/val/000552_t1.png",
        "data/processed/sod_tiled/images/val/000552_t3.png",
        "data/processed/sod_tiled/images/val/000707_t0.png",
        "data/processed/sod_tiled/images/val/000707_t2.png",
        "data/processed/sod_tiled/images/val/000784_t0.png",
        "data/processed/sod_tiled/images/val/000784_t2.png",
        "data/processed/sod_tiled/images/val/000832_t0.png",
        "data/processed/sod_tiled/images/val/000832_t2.png",
        "data/processed/sod_tiled/images/val/001848_t1.png",
        "data/processed/sod_tiled/images/val/001848_t3.png",
        "data/processed/sod_tiled/images/val/002086_t0.png",
        "data/processed/sod_tiled/images/val/002086_t1.png",
        "data/processed/sod_tiled/images/val/002126_t1.png",
        "data/processed/sod_tiled/images/val/002126_t3.png",
        "data/processed/sod_tiled/images/val/002176_t1.png",
        "data/processed/sod_tiled/images/val/002176_t3.png",
        "data/processed/sod_tiled/images/val/002203_t0.png",
    ]

    print("=" * 85)
    print(" 📊 MULTI-IMAGE STAGE 1 VALIDATION HARNESS (SOFTMAX ACTIVATED)")
    print("=" * 85)

    # Coordinate Mapping Documentation (Verification)
    print(
        "[i] Coordinate Mapping Policy: Local Y=379 is mapped to original 1000x665 canvas."
    )
    print(
        "    Formula: Global_Y = Y0 + (Y_local / 640) * (Y1 - Y0) "
        "[Correctly bound inside resizer]\n"
    )

    # Evaluate Calibration Set
    cal_tp, cal_evaluated = 0, 0
    print("[+] Evaluating Calibration Images (Check performance on known fits):")
    for f in calibration_files:
        path = Path(f)
        if not path.exists():
            print(f"  [!] Skipping missing file: {f}")
            continue
        cal_evaluated += 1
        _, _, _, detected = router.route_image(path, imgsz=640)
        if detected:
            cal_tp += 1
            print(f"  [✓] {path.name}: Defect Detected (True Positive)")
        else:
            print(f"  [✗] {path.name}: Blind / Missed (False Negative)")

    # Evaluate Held-Out Defect Files
    ho_tp, ho_fn = 0, 0
    print("\n[+] Evaluating Held-Out Defect Files (Generalization Check):")
    for f in held_out_defect_files:
        path = Path(f)
        if not path.exists():
            print(f"  [!] Skipping missing file: {f}")
            continue
        _, _, _, detected = router.route_image(path, imgsz=640)
        if detected:
            ho_tp += 1
            print(f"  [✓] {path.name}: Defect Detected (True Positive)")
        else:
            ho_fn += 1
            print(f"  [✗] {path.name}: Blind / Missed (False Negative)")

    # Evaluate Clean Files
    fp, tn = 0, 0
    print("\n[+] Evaluating Clean Background Files (FPR Check):")
    for f in clean_files:
        path = Path(f)
        if not path.exists():
            print(f"  [!] Skipping missing file: {f}")
            continue
        _, _, _, detected = router.route_image(path, imgsz=640)
        if detected:
            fp += 1
            print(f"  [✗] {path.name}: False Trigger (False Positive)")
        else:
            tn += 1
            print(f"  [✓] {path.name}: Clean / Ignored (True Negative)")

    cal_recall = (cal_tp / cal_evaluated) * 100 if cal_evaluated > 0 else 0.0
    held_out_recall = (ho_tp / (ho_tp + ho_fn)) * 100 if (ho_tp + ho_fn) > 0 else 0.0
    aggregate_recall = (
        ((cal_tp + ho_tp) / (cal_evaluated + ho_tp + ho_fn)) * 100
        if (cal_evaluated + ho_tp + ho_fn) > 0
        else 0.0
    )
    fpr = (fp / (fp + tn)) * 100 if (fp + tn) > 0 else 0.0

    print("\n" + "=" * 85)
    print(" STATISTICAL PERFORMANCE MATRIX")
    print("=" * 85)
    print(f"  Calibration Recall (n={cal_evaluated}):      {cal_recall:.2f}%")
    print(
        f"  Held-Out Recall (n={ho_tp + ho_fn}):          {held_out_recall:.2f}%  "
        "<-- REAL Performance"
    )
    print(
        f"  Aggregate Recall (n={cal_evaluated + ho_tp + ho_fn}):        "
        f"{aggregate_recall:.2f}%"
    )
    print(f"  False Positive Rate (n={fp + tn}):     {fpr:.2f}%")
    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_validation_harness()
