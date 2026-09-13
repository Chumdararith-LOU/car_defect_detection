"""Main training script for defect detection."""
import os
import sys
import torch
import yaml
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ultralytics import YOLO
from src.models.heads import Segment26WithObjectness
from src.training.callbacks import SurgicalFineTuneCallback, LPFTCallback
from src.training.patches import patch_yolo_class

def main():
    print("Loading base model...")
    # Use the custom head
    model = YOLO('yolo26m-seg.pt')  # Load pretrained weights
    model.add_callback('on_pretrain_routine_start', SurgicalFineTuneCallback(mode="et_backbone"))
    model.add_callback('on_train_epoch_start', LPFTCallback())

    # Patch the model's head with our custom one
    patch_yolo_class(model, Segment26WithObjectness)

    print("Starting training...")
    model.train(
        task='segment',
        data='/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/car_defect_detection/data/processed/stage2/car_damages_extended.yaml',
        epochs=300,
        imgsz=1024,
        batch=8,
        patience=50,
        device=[0, 1],
        workers=8,
        amp=True,
        freeze=0,
        lr0=0.01,
        lrf=0.01,
        optimizer='SGD',
        multi_scale=False,
        differential_lr=False,
        augmentations={
            'mosaic': 0.0,
            'scale': 0.3,
            'degrees': 15.0,
            'fliplr': 0.5,
            'perspective': 0.0005
        }
    )


if __name__ == "__main__":
    main()