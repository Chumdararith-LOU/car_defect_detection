import os
import mlflow
from pathlib import Path
from ultralytics import YOLO


def evaluate_test_set(
    model_path,
    data_yaml,
    project_name="Automated_Car_Defect_Stage1_SOD",
    run_name="Final_Test_Evaluation",
):
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
    os.environ["MLFLOW_TRACKING_URI"] = mlflow_uri
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(project_name)

    if not Path(model_path).exists():
        print(
            f"[!] Skipping MLflow evaluation: Model weights not found at {model_path}"
        )
        return

    print(f"[+] Loading best Stage 1 model from: {model_path}")
    model = YOLO(model_path, task="semantic")

    with mlflow.start_run(run_name=run_name):
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
    import argparse

    parser = argparse.ArgumentParser(
        description="Evaluate Production Model Weights on Unseen Test Split"
    )
    parser.add_argument(
        "--model", type=str, required=True, help="Path to best.pt weights"
    )
    parser.add_argument(
        "--data", type=str, required=True, help="Path to data.yaml file mapping splits"
    )
    parser.add_argument(
        "--project",
        type=str,
        default="Automated_Car_Defect_Stage1_SOD",
        help="MLflow project name",
    )
    parser.add_argument(
        "--run_name",
        type=str,
        default="Final_Test_Evaluation",
        help="MLflow run execution tag",
    )
    args = parser.parse_args()

    evaluate_test_set(
        model_path=args.model,
        data_yaml=args.data,
        project_name=args.project,
        run_name=args.run_name,
    )
