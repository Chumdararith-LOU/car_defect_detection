import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO


def evaluate_size_buckets(model_path, val_img_dir, val_mask_dir, threshold=0.70):
    print("[+] Loading model and scanning validation set...")
    model = YOLO(model_path, task="semantic")

    img_paths = sorted(list(Path(val_img_dir).glob("*.jpg")))
    mask_paths = sorted(list(Path(val_mask_dir).glob("*.png")))

    results = []

    for img_p, mask_p in zip(img_paths, mask_paths):
        # Load Ground Truth
        gt_mask = cv2.imread(str(mask_p), cv2.IMREAD_GRAYSCALE)
        gt_bin = (gt_mask > 0).astype(np.uint8)
        gt_pixels = np.sum(gt_bin)

        if gt_pixels == 0:
            continue  # Skip empty masks

        # Run Inference
        preds = model.predict(str(img_p), imgsz=320, verbose=False)
        # Extract raw probabilities and apply threshold
        raw_probs = preds[0].masks.data[0].cpu().numpy()
        pred_bin = (raw_probs >= threshold).astype(np.uint8)

        # Resize prediction back to original canvas size to compare fairly
        pred_bin_resized = cv2.resize(
            pred_bin,
            (gt_mask.shape[1], gt_mask.shape[0]),
            interpolation=cv2.INTER_NEAREST,
        )

        # Calculate Recall (How many true defect pixels did we successfully predict?)
        true_positives = np.sum(np.logical_and(pred_bin_resized == 1, gt_bin == 1))
        recall = true_positives / gt_pixels

        results.append({"file": img_p.name, "gt_size": gt_pixels, "recall": recall})

    # Sort by Ground Truth Size
    results.sort(key=lambda x: x["gt_size"])

    # Define Buckets
    bottom_10_idx = max(1, int(len(results) * 0.10))
    bottom_10 = results[:bottom_10_idx]
    top_90 = results[bottom_10_idx:]

    print("\n" + "=" * 60)
    print(" 📊 SIZE-BUCKETED RECALL EVALUATION")
    print("=" * 60)

    b10_recall = np.mean([x["recall"] for x in bottom_10]) * 100
    print(f"Bottom 10% (Micro Defects - {len(bottom_10)} samples):")
    print(f"  -> Average Recall: {b10_recall:.2f}%")

    t90_recall = np.mean([x["recall"] for x in top_90]) * 100
    print(f"\nTop 90% (Large Defects - {len(top_90)} samples):")
    print(f"  -> Average Recall: {t90_recall:.2f}%")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    # Update these paths to match your local setup
    model_weight = "runs/semantic/stage1_sod/weights/best.pt"
    img_dir = "data/processed/sod/val/images"
    mask_dir = "data/processed/sod/val/masks"

    evaluate_size_buckets(model_weight, img_dir, mask_dir)
