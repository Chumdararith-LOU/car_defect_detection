import os
import cv2
import numpy as np
import mlflow
from pathlib import Path
from ultralytics import YOLO


def diagnostic_downscale_survival(mask_dir, target_size=(256, 256), threshold=0.70):
    """
    Measures how many defect pixels survive aggressive downscaling.
    Crucial empirical test to validate the 'Tiny Defect Problem' architecture pivot.
    """
    mask_path_obj = Path(mask_dir)

    # Grab the first available mask for the diagnostic
    try:
        sample_mask_path = next(mask_path_obj.glob("*.png"))
    except StopIteration:
        print(f"[!] No masks found in {mask_dir}. Please verify dataset path.")
        return

    # Load original mask
    mask = cv2.imread(str(sample_mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"[!] Error loading mask at {sample_mask_path}")
        return

    h, w = mask.shape

    # Convert original to [0, 1] scale and count true defect pixels
    mask_norm = mask / 255.0
    original_active_pixels = np.sum(mask_norm > 0.1)

    if original_active_pixels == 0:
        print(f"[!] Mask {sample_mask_path.name} contains no defects. Try another.")
        return

    # Simulate pipeline downscaling using AREA interpolation (most accurate for shrinking)
    mask_resized = cv2.resize(mask_norm, target_size, interpolation=cv2.INTER_AREA)

    # Apply the strict gating threshold
    surviving_pixels = np.sum(mask_resized >= threshold)
    survival_rate = (surviving_pixels / original_active_pixels) * 100

    print("\n=====================================================")
    print("      🔍 DOWNSCALE SURVIVAL DIAGNOSTIC TEST")
    print("=====================================================")
    print(f"Sample Mask:     {sample_mask_path.name}")
    print(f"Original Canvas: {w}x{h}")
    print(f"Target Canvas:   {target_size[0]}x{target_size[1]}")
    print(f"Original Defect: {original_active_pixels} pixels")
    print(f"Surviving Defect:{surviving_pixels} pixels (Threshold >= {threshold})")
    print(f"Survival Rate:   {survival_rate:.2f}%\n")

    if survival_rate == 0:
        print("[!] FATAL: Defect completely erased by downscaling.")
        print("[!] ACTION: Coarse tiling (Action B) is mathematically required.")
    elif survival_rate < 10:
        print("[!] WARNING: Massive spatial feature loss detected.")
    else:
        print("[✓] Feature survival is stable.")
    print("=====================================================\n")


def evaluate_test_set():
    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5000"
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("Automated_Car_Defect_Stage1_SOD")

    model_path = "runs/semantic/artifacts/models/stage1_sod/weights/best.pt"
    data_yaml = "data/processed/sod/sod_data.yaml"

    if not Path(model_path).exists():
        print(
            f"[!] Skipping MLflow evaluation: Model weights not found at {model_path}"
        )
        return

    print(f"[+] Loading best Stage 1 model from: {model_path}")
    model = YOLO(model_path, task="semantic")

    with mlflow.start_run(run_name="Final_Test_Evaluation"):
        print("[+] Running evaluation on the unseen TEST split...")

        metrics = model.val(data=data_yaml, split="test")

        test_mIoU = metrics.miou
        test_pixel_acc = metrics.pixel_accuracy

        print("\n[✓] Test Evaluation Complete:")
        print(f"    - Test mIoU: {test_mIoU:.4f}")
        print(f"    - Test Pixel Accuracy: {test_pixel_acc:.4f}")

        mlflow.log_metrics(
            {"test_mIoU": test_mIoU, "test_pixel_accuracy": test_pixel_acc}
        )
        print("[+] Test metrics successfully saved to MLflow dashboard.")


if __name__ == "__main__":

    mask_directory = "data/processed/sod/train/masks"
    if Path(mask_directory).exists():
        diagnostic_downscale_survival(mask_directory)
    else:
        print(f"[!] Diagnostic skipped: Directory {mask_directory} not found.")

    evaluate_test_set()
