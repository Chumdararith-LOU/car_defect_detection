# src/train/train.py

import os
import argparse
import yaml
import mlflow
import subprocess
import time
from ultralytics import YOLO
from ultralytics import settings


def load_config(config_path):
    """Safely loads parameters from a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_git_commit():
    """Extracts the active short Git commit hash for metadata lineage."""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="AI Farm Car Defect Detection: Production Training Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the training YAML configuration file (e.g., configs/train/yolo26s-seg.yaml)",
    )
    args = parser.parse_args()

    print(f"Loading configuration from: {args.config}")
    cfg = load_config(args.config)

    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(mlflow_uri)

    os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "true"

    # Passive background logging initialization
    settings.update({"mlflow": False, "tensorboard": True})

    project_name = cfg.get("project", cfg.get("project_name", "car_defect_detection"))
    run_name = cfg.get("name", cfg.get("run_name", "experiment_run"))
    dataset_path = cfg.get("data", cfg.get("dataset_config"))
    batch_size = cfg.get("batch", cfg.get("batch_size", 16))

    aug = cfg.get("augmentations", cfg)

    print(f"Initializing architecture weights: {cfg['model_preset']}")
    model = YOLO(cfg["model_preset"])

    print(f"Launching experiment: project={project_name}, run={run_name}")

    mlflow.set_experiment(project_name)

    # Explicit MLflow block managing complete code/data lineage
    with mlflow.start_run(run_name=run_name):
        # Enforce data lineage tags
        git_hash = get_git_commit()
        mlflow.set_tag("git_commit", git_hash)
        mlflow.log_artifact(args.config, artifact_path="configs")

        # Track the configuration blueprint path
        mlflow.log_param("config_blueprint", args.config)

        model.train(
            # Task & Paths
            data=dataset_path,
            epochs=cfg["epochs"],
            imgsz=cfg["imgsz"],
            batch=batch_size,
            device=cfg["device"],
            workers=cfg.get("workers", 8),
            amp=cfg.get("amp", True),
            seed=42,  # Lock shuffle distributions to guarantee fair comparisons (PTQ vs QAT)
            # Environmental Defense Augmentations
            hsv_h=aug.get("hsv_h", 0.015),
            hsv_s=aug.get("hsv_s", 0.7),
            hsv_v=aug.get("hsv_v", 0.4),
            degrees=aug.get("degrees", 0.0),
            scale=aug.get("scale", 0.5),
            perspective=aug.get("perspective", 0.0),
            fliplr=aug.get("fliplr", 0.5),
            mosaic=aug.get("mosaic", 1.0),
            mixup=aug.get("mixup", 0.0),
            erasing=aug.get("erasing", 0.4),
            close_mosaic=aug.get("close_mosaic", 0),
            val=True,
            save=True,
            project=project_name,
            name=run_name,
        )

        time.sleep(2)

        yolo_save_dir = f"{project_name}/{run_name}"
        if os.path.exists(yolo_save_dir):
            print(f"Uploading YOLO artifacts from {yolo_save_dir} to MLflow...")
            mlflow.log_artifacts(yolo_save_dir, artifact_path="yolo_evaluation_data")

    print(
        f"Model training run complete. Weights archived under {project_name}/{run_name}/"
    )


if __name__ == "__main__":
    main()
