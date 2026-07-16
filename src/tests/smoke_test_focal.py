import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO, settings

OriginalCrossEntropyLoss = nn.CrossEntropyLoss


class FocalCrossEntropyLoss(OriginalCrossEntropyLoss):
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
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


# Apply the patch globally
nn.CrossEntropyLoss = FocalCrossEntropyLoss


def run_focal_smoke_test():
    print("[+] Disabling MLflow to prevent localhost:5000 connection timeouts...")
    settings.update({"mlflow": False})

    print("[+] Loading model for Focal Loss Smoke Test...")
    model = YOLO("yolo26m-sem.pt", task="semantic")

    print("[+] Commencing 2-Epoch Smoke Test...")
    _ = model.train(
        data="data/processed/sod_tiled/sod_data_tiled.yaml",
        epochs=2,
        batch=32,
        imgsz=640,
        project="Automated_Car_Defect_Stage1_SOD",
        name="SmokeTest_FocalLoss_Patch",
    )

    print(
        "\n[✓] Smoke test complete. Training loss successfully computed using Focal Loss!"
    )


if __name__ == "__main__":
    run_focal_smoke_test()
