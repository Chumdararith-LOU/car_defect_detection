import torch
import torch.nn as nn
import torch.nn.functional as F
import subprocess
import sys

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


nn.CrossEntropyLoss = FocalCrossEntropyLoss


def run_focal_smoke_test():
    print(
        "[+] Testing unified training pipeline with Focal Loss integration via fast 2-epoch run..."
    )

    cmd = [
        sys.executable,
        "src/train/train.py",
        "--config",
        "configs/train/stage1-sod.yaml",
    ]

    print(f"Executing validation trace command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode == 0:
        print("\n[✓] Smoke test complete. Pipeline verified successfully!")
    else:
        print("\n[❌] Pipeline Smoke Test Failed! Review loss patch traces.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run_focal_smoke_test()
