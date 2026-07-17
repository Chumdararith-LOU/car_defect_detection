# src/tests/val_harness_automated.py

import cv2
import numpy as np
import torch
import os
from pathlib import Path
from ultralytics import YOLO


class RawStage1Router:
    def __init__(
        self,
        model_path,
        pixel_thresh_high=0.28,
        pixel_thresh_low=0.18,
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

    def route_image(self, img):
        h_orig, w_orig = img.shape[:2]
        global_probs = np.zeros((h_orig, w_orig), dtype=np.float32)
        tile_bounds = self.get_tile_coords(h_orig, w_orig)

        for (y0, y1), (x0, x1) in tile_bounds:
            tile_crop = img[y0:y1, x0:x1]
            t_h, t_w = tile_crop.shape[:2]
            tile_resized = cv2.resize(tile_crop, (640, 640))
            img_tensor = (
                torch.from_numpy(tile_resized[:, :, ::-1].copy())
                .permute(2, 0, 1)
                .float()
                / 255.0
            )
            img_tensor = img_tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                raw_output = self.net(img_tensor)
            logits = raw_output[0] if isinstance(raw_output, tuple) else raw_output

            # SOFTMAX ACTIVATION
            if logits.shape[1] == 1:
                probs = torch.sigmoid(logits)
                raw_probs_map = probs[0, 0, :, :].cpu().numpy()
            else:
                probs = torch.softmax(logits, dim=1)
                raw_probs_map = probs[0, 1, :, :].cpu().numpy()

            tile_probs_resized = cv2.resize(
                raw_probs_map, (t_w, t_h), interpolation=cv2.INTER_LINEAR
            )
            global_probs[y0:y1, x0:x1] = np.maximum(
                global_probs[y0:y1, x0:x1], tile_probs_resized
            )

        # Hysteresis Gating (no erosion to protect the crack tail)
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

        num_labels_f, labels_f, stats_f, _ = cv2.connectedComponentsWithStats(
            gated_mask, connectivity=8
        )
        final_mask = np.zeros_like(gated_mask)
        for i in range(1, num_labels_f):
            if stats_f[i, cv2.CC_STAT_AREA] >= self.min_cc_area:
                final_mask[labels_f == i] = 1

        return final_mask


def run_automated_harness():
    model_weight = "mlruns/1/ba4046a349434a88a5dcade830554f65/artifacts/weights/best.pt"
    images_dir = Path("data/processed/sod/val/images")
    masks_dir = Path("data/processed/sod/val/masks")

    # Instantiate the router using our softmax-calibrated thresholds
    router = RawStage1Router(
        model_path=model_weight,
        pixel_thresh_high=0.28,
        pixel_thresh_low=0.18,
        min_cc_area=20,
    )

    calibration_images = ["000552.jpg", "000146.jpg"]
    all_images = sorted(os.listdir(images_dir))

    # Performance counters
    cal_tp, cal_fn = 0, 0
    ho_tp, ho_fn, ho_fp = 0, 0, 0
    evaluated_count = 0

    print("=" * 85)
    print(" 📊 AUTOMATED HELD-OUT VALIDATION HARNESS (SOFTMAX EVALUATION)")
    print("=" * 85)

    for img_file in all_images:
        if evaluated_count >= 52:  # Evaluate 50 held-out + 2 calibration images
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
        predicted_mask = router.route_image(img)
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
    run_automated_harness()
