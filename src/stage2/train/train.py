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
from ultralytics.utils.loss import v8SegmentationLoss
from stage1.utils.config_helpers import resolve_device


class ScaledFocalBCEWithLogitsLoss(nn.Module):
    """
    Alpha-balanced & Scaled Focal Loss operating on BCEWithLogits.
    - alpha=0.50: Equal balance between defect targets and background
    - gamma=1.5: Modulates hard vs easy example loss
    - scale=1.0: No arbitrary scaling (reduction="none" feeds into Ultralytics' normalization)
    """

    def __init__(self, alpha=0.50, gamma=1.5, scale=1.0, reduction="none"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.scale = scale
        self.reduction = reduction
        self.call_count = 0

    def forward(self, inputs, targets):
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction="none")
        p_t = torch.exp(-bce_loss)

        alpha_factor = targets * self.alpha + (1 - targets) * (1 - self.alpha)
        focal_loss = alpha_factor * ((1 - p_t) ** self.gamma) * bce_loss * self.scale

        # Debug logging for first few steps
        if self.call_count < 5:
            print(
                f"[PATCH VERIFICATION] Step {self.call_count} | "
                f"Mean Modulation: {((1 - p_t) ** self.gamma).mean().item():.4f} | "
                f"Mean Raw BCE: {bce_loss.mean().item():.4f} | "
                f"Mean Focal: {focal_loss.mean().item():.4f} | "
                f"Scale: {self.scale}"
            )
            self.call_count += 1

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_git_commit():
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
        help="Path to the training YAML configuration file",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Override dataset config path",
    )
    args = parser.parse_args()

    print(f"Loading configuration from: {args.config}")
    cfg = load_config(args.config)

    # Read loss configuration from YAML
    loss_type = cfg.get("loss_type", "bce")
    fl_gamma = cfg.get("fl_gamma", 1.5)
    fl_alpha = cfg.get("fl_alpha", 0.50)
    fl_scale = cfg.get("fl_scale", 1.0)

    orig_init = v8SegmentationLoss.__init__

    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.bce = ScaledFocalBCEWithLogitsLoss(
            alpha=fl_alpha, gamma=fl_gamma, scale=fl_scale, reduction="none"
        )
        print(
            f"\n[🔥] SCALED FOCAL LOSS INJECTED into v8SegmentationLoss.bce (alpha={fl_alpha}, gamma={fl_gamma}, scale={fl_scale}, reduction=none)\n"
        )

    # Apply patch only if loss_type is "focal"
    if loss_type == "focal":
        v8SegmentationLoss.__init__ = patched_init
        print(
            f"[+] Focal loss enabled with gamma={fl_gamma}, alpha={fl_alpha}, scale={fl_scale}"
        )
    else:
        print("[ℹ] Using standard BCE loss (no focal patch applied)")

    # MLflow setup
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
    settings.update({"mlflow": True, "tensorboard": True})

    project_name = cfg.get("project_name", "car_defect_detection")
    run_name = cfg.get("run_name", "experiment_run")

    model_preset = cfg.get("model_preset", "yolo26m-seg.pt")
    epochs = cfg.get("epochs", 100)
    batch_size = cfg.get("batch_size", 8)
    imgsz = cfg.get("imgsz", 640)
    task = cfg.get("task", "segment")

    dataset_path = args.data or cfg.get("dataset_config")

    device_obj = resolve_device(cfg)
    resolved_device = str(device_obj)
    print(f"[*] Ultralytics execution backend assigned to: {resolved_device}")

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
        mlflow.log_param("loss_type", loss_type)
        mlflow.log_param("fl_gamma", fl_gamma)
        mlflow.log_param("fl_alpha", fl_alpha)
        mlflow.log_param("fl_scale", fl_scale)

        try:
            model.train(
                task=task,
                data=dataset_path,
                epochs=epochs,
                patience=cfg.get("patience", 15),
                imgsz=imgsz,
                batch=batch_size,
                device=resolved_device,
                workers=cfg.get("workers", 8),
                amp=cfg.get("amp", True),
                seed=42,
                freeze=cfg.get("freeze", 0),
                multi_scale=cfg.get("multi_scale", False),
                optimizer=cfg.get("optimizer", "auto"),
                lr0=cfg.get("lr0", 0.01),
                lrf=cfg.get("lrf", 0.01),
                hsv_h=aug.get("hsv_h", 0.03),
                hsv_s=aug.get("hsv_s", 0.4),
                hsv_v=aug.get("hsv_v", 0.5),
                degrees=aug.get("degrees", 15.0),
                scale=aug.get("scale", 0.2),
                perspective=aug.get("perspective", 0.0005),
                fliplr=aug.get("fliplr", 0.5),
                mosaic=aug.get("mosaic", 1.0),
                mixup=aug.get("mixup", 0.0),
                erasing=aug.get("erasing", 0.2),
                close_mosaic=aug.get("close_mosaic", 10),
                val=True,
                save=True,
                project=project_name,
                name=run_name,
            )
        finally:
            if loss_type == "focal":
                v8SegmentationLoss.__init__ = orig_init
                print("[ℹ] Restored v8SegmentationLoss.__init__ to original")

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
