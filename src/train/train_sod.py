import os
import argparse
import yaml
from pathlib import Path
import mlflow
import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO


def load_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class HybridSODLoss(nn.Module):
    """
    Multi-loss optimization for Salient Object Detection (SOD).
    Combines BCE (Pixel alignment), IoU (Area alignment), and SSIM (Boundary sharpness).
    """

    def __init__(self, alpha=1.0, beta=1.0, gamma=1.0):
        super(HybridSODLoss, self).__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def forward(self, preds, targets):
        # 1. Binary Cross-Entropy Loss (Expects raw logits)
        bce_loss = F.binary_cross_entropy_with_logits(preds, targets)

        # Apply sigmoid to convert logits to probabilities for IoU/SSIM
        preds_sig = torch.sigmoid(preds)

        # 2. IoU Loss
        intersection = torch.sum(preds_sig * targets)
        union = torch.sum(preds_sig + targets - preds_sig * targets)
        iou_loss = 1.0 - (intersection / (union + 1e-6))

        # 3. Structural Similarity (SSIM) Loss (Patch-level variance approximation)
        mu_x = preds_sig.mean(dim=[2, 3], keepdim=True)
        mu_y = targets.mean(dim=[2, 3], keepdim=True)
        var_x = ((preds_sig - mu_x) ** 2).mean(dim=[2, 3], keepdim=True)
        var_y = ((targets - mu_y) ** 2).mean(dim=[2, 3], keepdim=True)
        cov_xy = ((preds_sig - mu_x) * (targets - mu_y)).mean(dim=[2, 3], keepdim=True)

        c1, c2 = 1e-4, 9e-4
        ssim = ((2 * mu_x * mu_y + c1) * (2 * cov_xy + c2)) / (
            (mu_x**2 + mu_y**2 + c1) * (var_x + var_y + c2)
        )
        ssim_loss = 1.0 - ssim.mean()

        # Weighted Hybrid Loss
        return (
            (self.alpha * bce_loss) + (self.beta * iou_loss) + (self.gamma * ssim_loss)
        )


def run_sod_training():
    parser = argparse.ArgumentParser(
        description="Stage 1: Binary Pre-Screening (SOD) Training"
    )
    parser.add_argument(
        "--train_config", type=str, default="configs/train/stage1-sod.yaml"
    )
    parser.add_argument(
        "--data_config", type=str, default="data/processed/sod/sod_data.yaml"
    )
    args = parser.parse_args()

    train_cfg = load_yaml(args.train_config)

    os.environ["MLFLOW_TRACKING_URI"] = "http://127.0.0.1:5001"
    mlflow.set_tracking_uri("http://127.0.0.1:5001")
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
