import argparse
import yaml
from pathlib import Path
import mlflow
from ultralytics import YOLO
import os


def load_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_sod_training():
    parser = argparse.ArgumentParser(
        description="Stage 1: Binary Pre-Screening (SOD) Training"
    )
    parser.add_argument(
        "--train_config", type=str, default="configs/train/stage1-sod.yaml"
    )
    parser.add_argument("--data_config", type=str, default="configs/data/sod_data.yaml")
    args = parser.parse_args()

    train_cfg = load_yaml(args.train_config)

    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5000"
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("Automated_Car_Defect_Stage1_SOD")
    run_name = f"Run_SOD_{Path(args.train_config).stem}"

    with mlflow.start_run(run_name=run_name) as run:
        print(f"[ℹ] MLflow Run Initialized for Stage 1 SOD. Run ID: {run.info.run_id}")

        # Log Hyperparameters
        training_params = train_cfg.get("training", {})
        mlflow.log_params(
            {
                "model_backbone": training_params.get("backbone", "yolo26n-sem.pt"),
                "epochs": training_params.get("epochs", 100),
                "batch_size": training_params.get("batch_size", 32),
                "input_img_size": train_cfg.get("dataset", {}).get("imgsz", 256),
                "pixel_thresh": train_cfg.get("gating_thresholds", {}).get(
                    "pixel_thresh"
                ),
                "anomaly_thresh": train_cfg.get("gating_thresholds", {}).get(
                    "anomaly_thresh"
                ),
            }
        )

        # Initialize the Pure Semantic Model
        print(
            f"[+] Initializing YOLO Semantic Engine with: {training_params.get('backbone')}"
        )
        model = YOLO(training_params.get("backbone", "yolo26n-sem.pt"))

        # Execute Training Trace
        with mlflow.start_span(name="sod_semantic_training") as span:
            results = model.train(
                data=args.data_config,
                task="semantic",
                epochs=training_params.get("epochs", 100),
                batch=training_params.get("batch_size", 32),
                imgsz=train_cfg.get("dataset", {}).get("imgsz", 256),
                lr0=training_params.get("lr0", 0.001),
                weight_decay=training_params.get("weight_decay", 0.0005),
                project="artifacts/models",
                name="stage1_sod",
                exist_ok=True,
                plots=True,
            )
            span.set_attribute("status", "SUCCESS")

        print("[+] Archiving Stage 1 Semantic metrics and weights to MLflow...")
        if hasattr(results, "results_dict"):
            mlflow.log_metrics(
                {
                    "val_mIoU": results.results_dict.get("metrics/mIoU(M)", 0.0),
                    "val_pixel_accuracy": results.results_dict.get(
                        "metrics/pixel_accuracy(M)", 0.0
                    ),
                    "loss_seg": results.results_dict.get("val/seg_loss", 0.0),
                }
            )

        output_dir = Path("artifacts/models/stage1_sod")
        best_weights = output_dir / "weights" / "best.pt"
        if best_weights.exists():
            mlflow.log_artifact(str(best_weights), artifact_path="model_weights")

        for graph_file in output_dir.glob("*.png"):
            mlflow.log_artifact(str(graph_file), artifact_path="evaluation_plots")

        print("[✓] Stage 1 SOD Training and MLflow registration complete.")


if __name__ == "__main__":
    run_sod_training()
