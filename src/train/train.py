# src/train/train.py

import os
import argparse
import yaml
from ultralytics import YOLO

def load_config(config_path):
    """Safely loads parameters from a YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    # 1. Set up CLI argument parsing to accept custom YAML configurations
    parser = argparse.ArgumentParser(description="AI Farm Car Defect Detection: Production Training Pipeline")
    parser.add_argument(
        "--config", 
        type=str, 
        required=True, 
        help="Path to the training YAML configuration file (e.g., configs/train/yolo26n-seg.yaml)"
    )
    args = parser.parse_args()

    # 2. Ingest parameters from the designated config file
    print(f"Loading configuration from: {args.config}")
    cfg = load_config(args.config)
    
    # Extract structural sub-blocks from the YAML dictionary
    aug = cfg.get("augmentations", {})

    # 3. Initialize the model preset targeting your specific task
    print(f"Initializing architecture weights: {cfg['model_preset']}")
    model = YOLO(cfg["model_preset"])

    # 4. Map the decoupled parameters seamlessly into the Ultralytics execution loop
    print(f"Launching experiment: project={cfg['project_name']}, run={cfg['run_name']}")
    results = model.train(
        # Task & Paths
        data=cfg["dataset_config"],
        epochs=cfg["epochs"],
        imgsz=cfg["imgsz"],
        batch=cfg["batch_size"],
        device=cfg["device"],
        workers=cfg["workers"],
        amp=cfg["amp"],
        
        # Environmental Defense Augmentations (Passed dynamically from config sub-dictionary)
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
        
        # Logging & Model Archival Anchors
        val=True,
        save=True,
        project=cfg["project_name"],
        name=cfg["run_name"],
    )

    print(f"🎉 Model training run complete. Weights archived under runs/segment/{cfg['run_name']}/")

if __name__ == "__main__":
    main()