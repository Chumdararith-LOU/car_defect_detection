#!/usr/bin/env python3
"""
Surgical Fine-Tuning Script: Early Texture Blocks Only
Isolates layers 0-4 (texture extraction) while freezing deep backbone (5-9) and neck (10-22).
Head (layer 23) remains trainable.

Target: Fix corrosion/crack detection by preserving input-level texture sensitivity.
"""

import os
import sys
import argparse

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

import yaml
import torch
from ultralytics import YOLO
from ultralytics.utils.torch_utils import unwrap_model


def apply_surgical_texture_freeze(model):
    """Freeze deep backbone (layers 5-22), keep early texture (0-4) and head (23) trainable."""
    # model.model is a torch.nn.Sequential from parse_model()
    layers = model.model
    
    NUM_LAYERS = 24
    HEAD_LAYER = 23
    
    frozen_count = 0
    trainable_count = 0
    
    for i in range(NUM_LAYERS):
        freeze_layer = i >= 5 and i <= 22
        
        for p in layers[i].parameters():
            p.requires_grad = not freeze_layer
        
        if freeze_layer:
            frozen_count += sum(p.numel() for p in layers[i].parameters())
        else:
            trainable_count += sum(p.numel() for p in layers[i].parameters())
    
    total = frozen_count + trainable_count
    
    print(f"\n{'='*80}")
    print("[Surgical Freeze] Early Texture Mode")
    print(f"{'='*80}")
    print(f"Frozen layers: 5-22 (deep backbone + neck)")
    print(f"Trainable layers: 0-4 (early texture) + {HEAD_LAYER} (head)")
    print(f"Trainable params: {trainable_count:,} / {total:,} ({100 * trainable_count / total:.2f}%)")
    print(f"Frozen params:    {frozen_count:,} / {total:,} ({100 * frozen_count / total:.2f}%)")
    print(f"{'='*80}\n")
    
    return trainable_count


def main():
    parser = argparse.ArgumentParser(description="Surgical Fine-Tuning: Early Texture Blocks")
    parser.add_argument("--weights", type=str, default="model5_resume_adapt/model1_remapped_7class_init.pt",
                        help="Path to warm-start weights")
    parser.add_argument("--data", type=str, default="data/processed/yolo_seg/data.yaml",
                        help="Path to dataset YAML")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--nbs", type=int, default=64)
    parser.add_argument("--lr0", type=float, default=0.0005)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--project", type=str, default="runs/segment/car_defect_detection")
    parser.add_argument("--name", type=str, default="surgical_texture_refined")
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--amp", action="store_true", default=True)
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print("[Surgical Fine-Tuning] Early Texture Blocks Only")
    print(f"{'='*80}")
    print(f"Weights: {args.weights}")
    print(f"Dataset: {args.data}")
    print(f"Resolution: {args.imgsz}x{args.imgsz}")
    print(f"Batch size: {args.batch} (effective nbs={args.nbs})")
    print(f"Learning rate: {args.lr0}")
    print(f"Epochs: {args.epochs}")
    print(f"Device: {args.device}")
    print(f"{'='*80}\n")
    
    print("[*] Loading model weights...")
    model = YOLO(args.weights)
    
    print("[*] Applying surgical freeze to deep backbone (layers 5-22)...")
    trainable_params = apply_surgical_texture_freeze(model.model)
    
    assert trainable_params == 9_200_000, (
        f"Expected ~9.2M trainable params, got {trainable_params:,}. "
        f"Check layer mapping: early_texture (0-4) + head (23)"
    )
    
    print("[*] Launching training with AdamW optimizer...")
    print(f"    Note: Grad accumulation will scale {args.batch} → {args.nbs} effective batch size\n")
    
    model.train(
        data=args.data,
        epochs=args.epochs,
        patience=args.patience,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        amp=args.amp,
        seed=42,
        optimizer="AdamW",
        lr0=args.lr0,
        lrf=0.01,
        weight_decay=0.01,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        multi_scale=False,
        mosaic=0.0,
        mixup=0.0,
        close_mosaic=10,
        project=args.project,
        name=args.name,
    )
    
    print(f"\n[✓] Training complete. Artifacts saved to {args.project}/{args.name}/")


if __name__ == "__main__":
    main()
