import cv2
import numpy as np
import os
from pathlib import Path
from src.inference.router import RawStage1Router


def run_automated_harness(
    model_weight,
    images_dir,
    masks_dir,
    pixel_thresh_high=0.28,
    pixel_thresh_low=0.18,
    min_cc_area=20,
    max_eval=52,
):
    images_dir = Path(images_dir)
    masks_dir = Path(masks_dir)

    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh_high=pixel_thresh_high,
        pixel_thresh_low=pixel_thresh_low,
        min_cc_area=min_cc_area,
    )

    calibration_images = ["000552.jpg", "000146.jpg"]

    all_images = sorted(os.listdir(images_dir))

    cal_tp, cal_fn = 0, 0
    ho_tp, ho_fn, ho_fp = 0, 0, 0
    evaluated_count = 0

    print("=" * 85)
    print(" 📊 AUTOMATED HELD-OUT VALIDATION HARNESS (SOFTMAX EVALUATION)")
    print("=" * 85)

    for img_file in all_images:
        if evaluated_count >= max_eval:
            break

        img_path = images_dir / img_file
        mask_path = masks_dir / (img_path.stem + ".png")

        if not mask_path.exists():
            continue

        img = cv2.imread(str(img_path))
        gt_mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if img is None or gt_mask is None:
            continue

        evaluated_count += 1
        predicted_mask = router.route_image(img_path, imgsz=args.imgsz)[2]
        has_prediction = np.any(predicted_mask > 0)

        # Calculate IoU of predicted mask vs ground truth mask
        intersection = np.logical_and(predicted_mask, gt_mask > 0).sum()
        union = np.logical_or(predicted_mask, gt_mask > 0).sum()
        iou = intersection / union if union > 0 else 0.0

        is_calibration = img_file in calibration_images

        if is_calibration:
            if has_prediction and iou > 0.01:
                cal_tp += 1
            else:
                cal_fn += 1
        else:
            if has_prediction:
                if iou > 0.01:
                    ho_tp += 1  # True Positive (found real defect)
                else:
                    ho_fp += 1  # False Positive / Spurious Trigger (masked pure shadow/noise)
            else:
                ho_fn += 1  # False Negative (missed the defect completely)

    # Compute Statistics
    cal_recall = (cal_tp / len(calibration_images)) * 100
    held_out_recall = (ho_tp / (ho_tp + ho_fn)) * 100 if (ho_tp + ho_fn) > 0 else 0.0
    spurious_trigger_rate = (
        (ho_fp / (ho_tp + ho_fp)) * 100 if (ho_tp + ho_fp) > 0 else 0.0
    )

    print("\n" + "=" * 85)
    print(" 📈 STATISTICAL PERFORMANCE MATRIX (IoU BASED)")
    print("=" * 85)
    print(
        f"  Calibration Recall (n={len(calibration_images)}):               {cal_recall:.2f}%"
    )
    print(
        f"  Held-Out Defect Recall (n={ho_tp + ho_fn}):           {held_out_recall:.2f}%"
    )
    print(
        f"  Spurious Trigger / False Alarm Rate (n={ho_tp + ho_fp}):   {spurious_trigger_rate:.2f}%"
    )
    print("=" * 85 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated Dataset-Wide Hysteresis IoU Validation Harness"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to target model evaluation weights",
    )
    parser.add_argument(
        "--images_dir",
        type=str,
        default="data/processed/sod/val/images",
        help="Target validation image folder",
    )
    parser.add_argument(
        "--masks_dir",
        type=str,
        default="data/processed/sod/val/masks",
        help="Target validation mask folder",
    )
    parser.add_argument(
        "--pixel_thresh_high", type=float, default=0.28, help="High core seed threshold"
    )
    parser.add_argument(
        "--pixel_thresh_low",
        type=float,
        default=0.18,
        help="Low boundary trail tracing threshold",
    )
    parser.add_argument(
        "--min_cc_area",
        type=int,
        default=20,
        help="Minimum pixel cluster component area size",
    )
    parser.add_argument(
        "--max_eval", type=int, default=52, help="Cap validation loop total item counts"
    )
    args = parser.parse_args()

    run_automated_harness(
        model_weight=args.model,
        images_dir=args.images_dir,
        masks_dir=args.masks_dir,
        pixel_thresh_high=args.pixel_thresh_high,
        pixel_thresh_low=args.pixel_thresh_low,
        min_cc_area=args.min_cc_area,
        max_eval=args.max_eval,
    )
