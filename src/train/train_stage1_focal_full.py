import os
import argparse
import yaml
import subprocess
import time
import mlflow
import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO, settings

OriginalCrossEntropyLoss = nn.CrossEntropyLoss


class FocalCrossEntropyLoss(OriginalCrossEntropyLoss):
    """
    A custom Focal Loss that disguises itself as standard CrossEntropyLoss
    so the Ultralytics backend consumes it natively.
    """

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
        self.gamma = 2.0
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


nn.CrossEntropyLoss = FocalCrossEntropyLoss


def load_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
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


# ---------------------------------------------------------
# 3. RUNNING THE FULL 50-EPOCH TRAINING WITH MLFLOW
# ---------------------------------------------------------
def run_full_focal_training():
    parser = argparse.ArgumentParser(
        description="Phase 4: Focal Loss Retraining for Stage 1 SOD"
    )
    parser.add_argument(
        "--train_config", type=str, default="configs/train/stage1-sod.yaml"
    )
    parser.add_argument(
        "--data_config",
        type=str,
        default="data/processed/sod_tiled/sod_data_tiled.yaml",
    )
    args = parser.parse_args()

    train_cfg = load_yaml(args.train_config)
    training_params = train_cfg.get("training", {})
    dataset_params = train_cfg.get("dataset", {})

    # Re-enable MLflow and point it to the correct custom port (5001)
    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5001"
    os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "true"
    mlflow.set_tracking_uri("http://127.0.0.1:5001")

    logging_params = train_cfg.get("logging", {})
    experiment_name = logging_params.get(
        "experiment_name", "Automated_Car_Defect_Stage1_SOD"
    )
    run_name = logging_params.get("run_name", "Stage1_SOD_FocalLoss_Full")

    mlflow.set_experiment(experiment_name)
    settings.update({"mlflow": True, "tensorboard": True})
    os.environ["MLFLOW_KEEP_RUN_ACTIVE"] = "True"

    with mlflow.start_run(run_name=run_name) as run:
        print(
            f"[ℹ] MLflow Run Initialized for Focal Loss Retraining. Run ID: {run.info.run_id}"
        )

        # Log Metadata
        git_hash = get_git_commit()
        mlflow.set_tag("git_commit", git_hash)
        mlflow.log_artifact(args.train_config, artifact_path="configs")

        mlflow.log_params(
            {
                "config_blueprint": args.train_config,
                "model_backbone": training_params.get("backbone", "yolo26m-sem.pt"),
                "epochs": training_params.get("epochs", 50),
                "batch_size": training_params.get("batch_size", 16),
                "input_img_size": dataset_params.get("imgsz", 1024),
                "lr0": training_params.get("lr0", 0.001),
                "weight_decay": training_params.get("weight_decay", 0.0005),
                "loss_function": training_params.get(
                    "loss_function", "FocalCrossEntropyLoss"
                ),
                "fl_gamma": training_params.get("fl_gamma", 2.0),
            }
        )

        print(
            f"[+] Initializing YOLO Semantic Engine with backbone: {training_params.get('backbone', 'yolo26m-sem.pt')}"
        )
        model = YOLO(training_params.get("backbone", "yolo26m-sem.pt"))

        # Execute Training Trace dynamically pulling from YAML
        with mlflow.start_span(name="focal_loss_semantic_training") as span:
            results = model.train(
                data=args.data_config,
                task="semantic",
                epochs=training_params.get("epochs", 50),
                batch=training_params.get("batch_size", 16),
                imgsz=dataset_params.get("imgsz", 1024),
                lr0=training_params.get("lr0", 0.001),
                weight_decay=training_params.get("weight_decay", 0.0005),
                project="runs/semantic/Automated_Car_Defect_Stage1_SOD",
                name=run_name,
                exist_ok=True,
                plots=True,
            )
            span.set_attribute("status", "SUCCESS")

        print("[+] Archiving Focal Loss Phase 4 metrics and weights to MLflow...")
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

        time.sleep(2)
        actual_save_dir = str(model.trainer.save_dir)

        if os.path.exists(actual_save_dir):
            print(f"Uploading YOLO artifacts from {actual_save_dir} to MLflow...")
            mlflow.log_artifacts(actual_save_dir, artifact_path="yolo_evaluation_data")
        else:
            print(
                f"[!] Warning: Could not locate YOLO save directory at {actual_save_dir}"
            )

        print("[✓] Phase 4 Focal Loss Retraining and MLflow registration complete.")


if __name__ == "__main__":
    run_full_focal_training()
