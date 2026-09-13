"""Custom loss functions for car defect detection."""
import torch
import torch.nn as nn
import torch.nn.functional as F


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


class SeesawBCE(nn.Module):
    """Seesaw loss for class imbalance - binary version for mask segmentation."""

    def __init__(self, p=0.8, q=2.0, reduction="none"):
        super().__init__()
        self.p = p
        self.q = q
        self.reduction = reduction

    def forward(self, inputs, targets):
        """
        Seesaw loss: L = BCE + C * (p^x - q^x)
        where x is the confidence difference between positive and negative.
        """
        bce = F.binary_cross_entropy_with_logits(inputs, targets, reduction="none")
        
        # Calculate confidence difference
        probs = torch.sigmoid(inputs)
        diff = probs - targets  # positive: diff > 0, negative: diff < 0
        
        # Seesaw correction
        seesaw_term = (self.p ** torch.clamp(diff, min=0)) * (self.q ** torch.clamp(-diff, min=0))
        
        loss = bce * seesaw_term
        
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss
