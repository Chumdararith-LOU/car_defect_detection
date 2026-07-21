import os
import argparse
import yaml
import mlflow
import subprocess
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO
from ultralytics import settings
from stage1.utils.config_helpers import resolve_device

OriginalCrossEntropyLoss = nn.CrossEntropyLoss


class FocalCrossEntropyLoss(OriginalCrossEntropyLoss):
    """
    A custom Focal Loss that disguises itself as standard CrossEntropyLoss
    so the Ultralytics backend consumes it natively.
    """

    gamma = 2.0

    def __init__(
        self,
        weight=None,
        size_average=None,
        ignore_index=-100,
        reduce=None,
        reduction="mean",
        label_smoothing=0.0,
    ):
        super().__init__(
            weight, size_average, ignore_index, reduce, reduction, label_smoothing
        )
        self.call_count = 0
        print(
            f"\n[🔥] FOCAL LOSS INJECTED: Overriding PyTorch CE Loss with gamma={self.gamma}\n"
        )

    def forward(self, input, target):
        ce_loss = F.cross_entropy(
            input,
            target,
            weight=self.weight,
            ignore_index=self.ignore_index,
            reduction="none",
            label_smoothing=self.label_smoothing,
        )
        pt = torch.exp(-ce_loss)
        modulation = (1 - pt) ** self.gamma
        focal_loss = modulation * ce_loss

        if self.call_count < 5:
            print(
                f"[ PATCH VERIFICATION] Step {self.call_count} | "
                f"Mean Modulation Weight: {modulation.mean().item():.4f} | "
                f"Mean Raw CE: {ce_loss.mean().item():.4f} | "
                f"Mean Focal: {focal_loss.mean().item():.4f}"
            )
            self.call_count += 1

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


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
        help="Path to the training YAML configuration file (like configs/train/yolo26s-seg.yaml)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Override dataset config path (defaults to dataset_config in yaml or derived from processed_dir)",
    )
    args = parser.parse_args()

    print(f"Loading configuration from: {args.config}")
    cfg = load_config(args.config)

    if torch.backends.mps.is_available():
        os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
        mlflow_uri = "file:./mlruns"
        print(
            "[ℹ] MacBook environment detected: Routing MLflow tracking locally to ./mlruns"
        )
    else:
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")

    mlflow.set_tracking_uri(mlflow_uri)

    os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "true"

    settings.update({"mlflow": False, "tensorboard": True})

    project_name = cfg.get("project", {}).get("name", "car_defect_detection")
    run_name = cfg.get("project", {}).get("run_name", "experiment_run")

    model_preset = cfg.get("model", {}).get("preset", "yolo26n-sem.pt")
    epochs = cfg.get("model", {}).get("epochs", 50)
    batch_size = cfg.get("dataset", {}).get("batch_size", 16)
    imgsz = cfg.get("dataset", {}).get("imgsz", 640)

    loss_type = cfg.get("pipeline", {}).get("loss_type", "ce")
    fl_gamma = cfg.get("pipeline", {}).get("fl_gamma", 2.0)
    task = cfg.get("pipeline", {}).get("task", "semantic")

    if args.data:
        dataset_path = args.data
    else:
        dataset_path = cfg.get("dataset", {}).get(
            "train_config", "data/processed/sod_tiled/sod_data_tiled.yaml"
        )

    device_obj = resolve_device(cfg)
    resolved_device = str(device_obj)
    print(f"[*] Ultralytics execution backend assigned to: {resolved_device}")

    if loss_type == "focal":
        FocalCrossEntropyLoss.gamma = fl_gamma
        nn.CrossEntropyLoss = FocalCrossEntropyLoss
        print(
            f"[🔥] Successfully patched nn.CrossEntropyLoss to FocalCrossEntropyLoss (gamma={FocalCrossEntropyLoss.gamma})"
        )
    else:
        nn.CrossEntropyLoss = OriginalCrossEntropyLoss
        print("[ℹ] Using standard CrossEntropyLoss")

    aug = cfg.get("augmentations", cfg)

    print(f"Initializing architecture weights: {model_preset}")
    model = YOLO(model_preset)

    print(f"Launching experiment: project={project_name}, run={run_name}")

    mlflow.set_experiment(project_name)

    os.environ["MLFLOW_KEEP_RUN_ACTIVE"] = "True"

    with mlflow.start_run(run_name=run_name):
        git_hash = get_git_commit()
        mlflow.set_tag("git_commit", git_hash)
        mlflow.log_artifact(args.config, artifact_path="configs")

        mlflow.log_param("config_blueprint", args.config)
        mlflow.log_param("model_preset", model_preset)

        model.train(
            task=task,
            data=dataset_path,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            device=resolved_device,
            workers=cfg.get("hardware", {}).get("workers", 8),
            amp=cfg.get("hardware", {}).get("amp", True),
            seed=42,
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

        actual_save_dir = str(model.trainer.save_dir)

        if os.path.exists(actual_save_dir):
            print(f"Uploading YOLO artifacts from {actual_save_dir} to MLflow...")
            mlflow.log_artifacts(actual_save_dir, artifact_path="yolo_evaluation_data")
        else:
            print(f"Warning: Could not locate YOLO save directory at {actual_save_dir}")

    print(
        f"Model training run complete. Weights archived under {project_name}/{run_name}/"
    )


if __name__ == "__main__":
    main()
