import os
import mlflow
from ultralytics import YOLO


def evaluate_test_set():
    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5000"
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("Automated_Car_Defect_Stage1_SOD")

    model_path = "runs/semantic/artifacts/models/stage1_sod/weights/best.pt"
    data_yaml = "data/processed/sod/sod_data.yaml"

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
    evaluate_test_set()
