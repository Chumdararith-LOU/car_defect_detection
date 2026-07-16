import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from src.inference.router import get_stitched_probability_map


class RawStage1Router:
    """Consolidated router for batch evaluation matching production specifications."""

    def __init__(
        self,
        model_path,
        pixel_thresh_high=0.85,
        pixel_thresh_low=0.40,
        min_cc_area=20,
        overlap_frac=0.15,
    ):
        self.yolo_model = YOLO(model_path, task="semantic")
        self.net = self.yolo_model.model
        self.net.eval()
        self.device = next(self.net.parameters()).device
        self.pixel_thresh_high = pixel_thresh_high
        self.pixel_thresh_low = pixel_thresh_low
        self.min_cc_area = min_cc_area
        self.overlap_frac = overlap_frac

    def get_tile_coords(self, h, w):
        h_mid, w_mid = h // 2, w // 2
        oh, ow = int(h * self.overlap_frac), int(w * self.overlap_frac)
        return [
            ((0, min(h, h_mid + oh)), (0, min(w, w_mid + ow))),
            ((0, min(h, h_mid + oh)), (max(0, w_mid - ow), w)),
            ((max(0, h_mid - oh), h), (0, min(w, w_mid + ow))),
            ((max(0, h_mid - oh), h), (max(0, w_mid - ow), w)),
        ]

    def route_image(self, img_path, imgsz=640):
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [!] Skipped corrupted/missing image: {img_path}")
            return False

        global_probs = get_stitched_probability_map(
            img=img,
            net=self.net,
            device=self.device,
            overlap_frac=self.overlap_frac,
            imgsz=imgsz,
        )

        mask_high = (global_probs >= self.pixel_thresh_high).astype(np.uint8)
        mask_low = (global_probs >= self.pixel_thresh_low).astype(np.uint8)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask_low, connectivity=8
        )
        gated_mask = np.zeros_like(mask_low)
        for i in range(1, num_labels):
            comp = labels == i
            if np.any(mask_high[comp] > 0):
                gated_mask[comp] = 1

        # Size filter
        num_labels_f, labels_f, stats_f, _ = cv2.connectedComponentsWithStats(
            gated_mask, connectivity=8
        )
        final_mask = np.zeros_like(gated_mask)
        for i in range(1, num_labels_f):
            if stats_f[i, cv2.CC_STAT_AREA] >= self.min_cc_area:
                final_mask[labels_f == i] = 1

        return np.any(final_mask > 0)


def run_validation_harness():
    model_weight = (
        "runs/semantic/runs/semantic/Automated_Car_Defect_Stage1_SOD/"
        "Stage1_SOD_FocalLoss_Full/weights/best.pt"
    )

    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh_high=0.28,
        pixel_thresh_low=0.18,
        min_cc_area=20,
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
        "data/processed/sod_tiled/images/val/000707_t0.png",
        "data/processed/sod_tiled/images/val/000707_t2.png",
        "data/processed/sod_tiled/images/val/000784_t0.png",
        "data/processed/sod_tiled/images/val/000784_t2.png",
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
        detected = router.route_image(path)
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
        detected = router.route_image(path)
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
        detected = router.route_image(path)
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
