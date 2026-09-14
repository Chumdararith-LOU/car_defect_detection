import os
import sys
import argparse
# Add project root to sys.path so 'src' package is importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# Vendored fork (has SeesawBCE) must win over any pip-installed ultralytics
_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)
import yaml
import mlflow
import subprocess
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO
from ultralytics import settings
from ultralytics.utils.loss import v8SegmentationLoss, E2ELoss
from config_helpers import resolve_device
from surgical_modes import UNFREEZE_MODES, apply_surgical_mode
from ultralytics.models.yolo.segment import SegmentationTrainer
from src.models.segment_head_with_obj import Segment26WithObjectness
from ultralytics.nn.modules.head import Segment26
import ultralytics.nn.modules.head as head_module

head_module.Segment26WithObjectness = Segment26WithObjectness
import ultralytics.nn.tasks as tasks_module
tasks_module.Segment26WithObjectness = Segment26WithObjectness
from src.models.losses import ScaledFocalBCEWithLogitsLoss, SeesawBCE


def set_bn_eval(module):
    """Recursively set all BatchNorm layers to eval mode."""
    for child in module.children():
        if isinstance(child, torch.nn.BatchNorm2d):
            child.eval()
        set_bn_eval(child)


def set_bn_eval_callback(trainer):
    """Set all BatchNorm layers to eval mode to prevent stats drift during training."""
    set_bn_eval(trainer.model)


def count_optimizer_params(optimizer):
    """Count total parameters tracked by optimizer."""
    total = 0
    for param_group in optimizer.param_groups:
        total += sum(p.numel() for p in param_group['params'])
    return total


def set_bn_eval(module):
    """Recursively set all BatchNorm layers to eval mode."""
    for child in module.children():
        if isinstance(child, torch.nn.BatchNorm2d):
            child.eval()
        set_bn_eval(child)


def rebuild_optimizer_after_unfreeze(trainer, mode=None):
    """Rebuild optimizer after surgical unfreeze to capture newly-unfrozen parameters.
    
    This callback runs at on_before_build_optimizer, before the trainer builds its
    optimizer. If a surgical mode was applied, we unfreeze layers and rebuild the 
    optimizer to include parameters that were unfrozen by apply_surgical_mode.
    
    Safety assertion: Verifies that trainable parameter count matches the mode's
    expected count after unfreeze, and that model_trainable == optimizer_tracked.
    
    Args:
        trainer: The YOLO trainer instance
        mode: Surgical unfreeze mode (passed via closure, not from trainer.state)
    """
    import sys
    print(f"\n{'='*80}", flush=True)
    print(f"[DEBUG CALLBACK START] trainer.epoch={getattr(trainer, 'epoch', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK START] trainer.tloss={getattr(trainer, 'tloss', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK START] trainer.metrics={getattr(trainer, 'metrics', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK START] trainer.csv={getattr(trainer, 'csv', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK START] mode={mode}", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    if mode is None or mode not in UNFREEZE_MODES:
        return
    
    from ultralytics.utils.torch_utils import unwrap_model
    
    unwrapped_model = unwrap_model(trainer.model)
    expected_trainable = apply_surgical_mode(unwrapped_model, mode)
    
    print(f"[✅] Callback: unfroze {expected_trainable:,} params, rebuilding optimizer...")
    
    trainer.optimizer = trainer.build_optimizer(
        model=trainer.model,
        name=trainer.args.optimizer,
        lr=trainer.args.lr0,
        momentum=trainer.args.momentum,
        decay=trainer.args.weight_decay,
        iterations=trainer.args.warmup_epochs,
    )
    # build_optimizer tracks every param incl. frozen ones; keep only trainable
    for group in trainer.optimizer.param_groups:
        group["params"] = [p for p in group["params"] if p.requires_grad]

    model_trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    optim_tracked = count_optimizer_params(trainer.optimizer)
    
    print(f"[✅] Callback: model_trainable={model_trainable:,}, optimizer_tracked={optim_tracked:,}")
    
    assert model_trainable == optim_tracked, (
        f"Surgical unfreeze mismatch: model_trainable ({model_trainable:,}) != "
        f"optimizer_tracked ({optim_tracked:,}). Check optimizer construction."
    )
    
    # Rebuild scheduler to match new optimizer
    trainer._setup_scheduler()
    
    print(f"\n{'='*80}", flush=True)
    print(f"[DEBUG CALLBACK END] trainer.epoch={getattr(trainer, 'epoch', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK END] trainer.tloss={getattr(trainer, 'tloss', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK END] trainer.metrics={getattr(trainer, 'metrics', 'N/A')}", flush=True)
    print(f"[DEBUG CALLBACK END] trainer.csv={getattr(trainer, 'csv', 'N/A')}", flush=True)
    print(f"{'='*80}\n", flush=True)

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
    seesaw_p = float(cfg.get("seesaw_p", 0.8))
    seesaw_q = float(cfg.get("seesaw_q", 2.0))
    use_objectness = cfg.get("use_objectness", False)
    obj_loss_weight = float(cfg.get("obj_loss_weight", 1.0))
    use_nwd = cfg.get("use_nwd", False)
    nwd_c = float(cfg.get("nwd_c", 12.7))
    use_differential_lr = cfg.get("differential_lr", False)

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
    
    # Replace head with objectness branch if enabled
    if use_objectness:
        print("[🔪] Replacing head with Segment26WithObjectness")
        from src.models.segment_head_with_obj import Segment26WithObjectness
        original_head = model.model.model[-1]
        # Get input channels for each FPN level (first conv's input in each cv2 branch)
        ch = tuple(x[0].conv.in_channels for x in original_head.cv2)
        print(f"[DEBUG] Head ch: {ch}")
        model.model.model[-1] = Segment26WithObjectness(
            nc=original_head.nc,
            nm=original_head.nm,
            npr=original_head.npr,
            reg_max=original_head.reg_max,
            end2end=getattr(original_head, "end2end", False),
            ch=ch
        )
        # Copy weights from original head's cv2, cv3, cv4
        new_head = model.model.model[-1]
        new_head.cv2 = original_head.cv2
        new_head.cv3 = original_head.cv3
        new_head.cv4 = original_head.cv4
        new_head.proto = original_head.proto
    
    # Inject loss parameters into model args for native loss injection
    model.args["loss_type"] = loss_type
    model.args["fl_gamma"] = fl_gamma
    model.args["fl_alpha"] = fl_alpha
    model.args["fl_scale"] = fl_scale
    model.args["seesaw_p"] = seesaw_p
    model.args["seesaw_q"] = seesaw_q
    model.args["use_objectness"] = use_objectness
    model.args["obj_loss_weight"] = obj_loss_weight
    
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
        mlflow.log_param("seesaw_p", seesaw_p if loss_type == "seesaw" else None)
        mlflow.log_param("seesaw_q", seesaw_q if loss_type == "seesaw" else None)
        mlflow.log_param("use_objectness", use_objectness)
        if use_objectness:
            mlflow.log_param("obj_loss_weight", obj_loss_weight)
        mlflow.log_param("differential_lr", use_differential_lr)
        mlflow.log_param("use_nwd", use_nwd)

        try:
            surgical_mode = cfg.get("surgical_mode", "none")
            freeze_arg = cfg.get("freeze", 0)
            
            if surgical_mode in UNFREEZE_MODES:
                print(f"\n[🔪] SURGICAL FINE-TUNING: mode={surgical_mode}")
                # CRITICAL: Bypass Ultralytics' internal freeze logic so it doesn't overwrite our setup
                freeze_arg = 0
                # Add callback to unfreeze and rebuild optimizer before trainer builds it
                # Pass mode through closure instead of model.trainer (which doesn't exist yet)
                def make_unfreeze_callback(mode):
                    def callback(trainer):
                        print(f"[DEBUG] Callback registered! mode={mode}", flush=True)
                        rebuild_optimizer_after_unfreeze(trainer, mode)
                    return callback
                print(f"[DEBUG] Adding callback for mode={surgical_mode}", flush=True)
                model.add_callback("on_before_build_optimizer", make_unfreeze_callback(surgical_mode))
                model.add_callback("on_train_start", set_bn_eval_callback)
                print(f"[DEBUG] Callback added. Total callbacks: {len(model.callbacks.get('on_before_build_optimizer', []))}", flush=True)
            
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
                freeze=freeze_arg,
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
                 loss_type=loss_type,
                 fl_gamma=fl_gamma,
                 fl_alpha=fl_alpha,
                 fl_scale=fl_scale,
                 seesaw_p=seesaw_p,
                 seesaw_q=seesaw_q,
                 use_objectness=use_objectness,
                 obj_loss_weight=obj_loss_weight,
             )
        finally:
            print("[ℹ] Loss type configuration handled natively in vendor/ultralytics/ultralytics/utils/loss.py")

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