import os
import sys
import argparse
# Add project root to sys.path so 'src' package is importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
import yaml
import mlflow
import subprocess
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from ultralytics import YOLO
from ultralytics import settings
from ultralytics.utils.loss import v8SegmentationLoss, E2ELoss, SeesawBCE
from config_helpers import resolve_device
from ultralytics.models.yolo.segment import SegmentationTrainer
import ultralytics.utils.metrics as metrics_module 
from src.models.segment_head_with_obj import Segment26WithObjectness
from ultralytics.nn.modules.head import Segment26
import ultralytics.nn.modules.head as head_module

head_module.Segment26WithObjectness = Segment26WithObjectness
import ultralytics.nn.tasks as tasks_module
tasks_module.Segment26WithObjectness = Segment26WithObjectness

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
    seesaw_p = float(cfg.get("seesaw_p", 0.8))
    seesaw_q = float(cfg.get("seesaw_q", 2.0))
    use_objectness = cfg.get("use_objectness", False)
    obj_loss_weight = float(cfg.get("obj_loss_weight", 1.0))
    use_nwd = cfg.get("use_nwd", False)
    nwd_c = float(cfg.get("nwd_c", 12.7))
    use_differential_lr = cfg.get("differential_lr", False)
    split_layer_idx = int(cfg.get("split_layer_idx", 15))
    backbone_lr_mult = float(cfg.get("backbone_lr_mult", 0.1))
    orig_build_optimizer = None

    orig_init = v8SegmentationLoss.__init__

    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        if loss_type == "focal":
            self.bce = ScaledFocalBCEWithLogitsLoss(
                alpha=fl_alpha, gamma=fl_gamma, scale=fl_scale, reduction="none"
            )
            print(f"\n[🔥] SCALED FOCAL LOSS INJECTED (alpha={fl_alpha}, gamma={fl_gamma}, scale={fl_scale})\n")
        elif loss_type == "seesaw":
            self.bce = SeesawBCE(p=seesaw_p, q=seesaw_q)
            print(f"\n[🔥] SEESAW LOSS (fork SeesawBCE) INJECTED (p={seesaw_p}, q={seesaw_q})\n")
        else:
            print("[ℹ] Using standard BCE loss (no patch applied)")

    orig_call = v8SegmentationLoss.__call__ if use_objectness else None
    orig_e2e_call = E2ELoss.__call__ if use_objectness else None

    if use_objectness:
        def _compute_obj_loss(preds_top, assigner_owner, batch):
            """Shared helper: BCE objectness loss against the assigner's foreground mask.

            preds_top    : the dict that actually has the "obj" key on it
                           (top-level dict for end2end models; the flat dict otherwise).
            assigner_owner: the v8SegmentationLoss instance whose .assigner /
                           .get_assigned_targets_and_loss should be used (self.one2many
                           for the end2end path, so obj gets the denser topk=10 positive set).
            """
            obj_pred = preds_top["obj"]  # (bs, 1, N)
            if obj_pred.dim() == 3:
                obj_pred = obj_pred.squeeze(1)  # -> (bs, N)

            # preds_top is either {"one2many":..., "one2one":..., "obj":...} (end2end)
            # or the flat dict itself (non-end2end) — .get() handles both uniformly.
            assign_preds = preds_top.get("one2many", preds_top)
            fg_mask = assigner_owner.get_assigned_targets_and_loss(assign_preds, batch)[0][0]
            obj_target = fg_mask.float()

            assert obj_pred.shape == obj_target.shape, (
                f"Objectness shape mismatch! Pred: {obj_pred.shape} vs Target: {obj_target.shape}."
            )
            return F.binary_cross_entropy_with_logits(obj_pred, obj_target)

        def patched_e2e_call(self, preds, batch):
            # This is the path that ACTUALLY runs when end2end=True: SegmentationModel.init_criterion()
            # wraps v8SegmentationLoss in E2ELoss, and E2ELoss.__call__ invokes .loss() directly on its
            # internal one2many/one2one v8SegmentationLoss instances — it never calls __call__, which is
            # why the objectness branch never trained despite the earlier patch "succeeding" with no error.
            preds_top = self.one2many.parse_output(preds)
            loss, loss_items = orig_e2e_call(self, preds, batch)

            if isinstance(preds_top, dict) and "obj" in preds_top:
                obj_loss = _compute_obj_loss(preds_top, self.one2many, batch)
                loss = loss + (obj_loss * obj_loss_weight)
                loss_items = torch.cat([loss_items, (obj_loss * obj_loss_weight).detach().view(1)])

            return loss, loss_items

        def patched_call(self, preds, batch):
            # Fallback path, only actually exercised if you ever train with end2end=False.
            preds_top = self.parse_output(preds)
            loss, loss_items = orig_call(self, preds, batch)

            if isinstance(preds_top, dict) and "obj" in preds_top:
                obj_loss = _compute_obj_loss(preds_top, self, batch)
                loss = loss + (obj_loss * obj_loss_weight)
                loss_items = torch.cat([loss_items, (obj_loss * obj_loss_weight).detach().view(1)])

            return loss, loss_items

        E2ELoss.__call__ = patched_e2e_call
        v8SegmentationLoss.__call__ = patched_call
        print(f"\n[🎯] OBJECTNESS LOSS INJECTED via E2ELoss.__call__ (end2end path) "
              f"+ v8SegmentationLoss.__call__ (non-end2end fallback), weight={obj_loss_weight}\n")

    if loss_type in ("focal", "seesaw"):
        v8SegmentationLoss.__init__ = patched_init

    if use_differential_lr:
        orig_build_optimizer = SegmentationTrainer.build_optimizer

        def patched_build_optimizer(
            self,
            model,
            name="auto",
            lr=0.001,
            momentum=0.937,
            decay=0.0005,
            iterations=1e5,
        ):
            # 6 groups: bb_w, bb_b, bb_bn, head_w, head_b, head_bn
            bb_w, bb_b, bb_bn = [], [], []
            head_w, head_b, head_bn = [], [], []

            # Map every parameter tensor to its parent module
            param_to_module = {}
            for m in model.modules():
                for p in m.parameters(recurse=False):
                    param_to_module[p] = m

            for n, p in model.named_parameters():
                if not p.requires_grad:
                    continue

                # Parse layer index from parameter name (e.g., "model.23.cv3..." -> 23)
                parts = n.split(".")
                idx = 999
                for part in parts:
                    if part.isdigit():
                        idx = int(part)
                        break

                is_head = idx >= split_layer_idx

                m = param_to_module.get(p)
                if m is None:
                    (head_w if is_head else bb_w).append(p)
                    continue

                is_bias = (
                    hasattr(m, "bias")
                    and isinstance(m, (nn.Conv2d, nn.Conv1d, nn.Conv3d, nn.Linear))
                    and p is m.bias
                )
                is_norm = isinstance(
                    m, (nn.BatchNorm2d, nn.BatchNorm1d, nn.GroupNorm, nn.LayerNorm)
                )

                if is_bias:
                    (head_b if is_head else bb_b).append(p)
                elif is_norm:
                    (head_bn if is_head else bb_bn).append(p)
                else:
                    (head_w if is_head else bb_w).append(p)

            # Create optimizer with backbone weights first
            optimizer = torch.optim.SGD(
                bb_w, lr=lr * backbone_lr_mult, momentum=momentum, nesterov=True
            )

            # Add the rest of the groups. Explicitly set weight_decay=0.0 for biases and norms!
            if bb_b:
                optimizer.add_param_group(
                    {"params": bb_b, "lr": lr * backbone_lr_mult, "weight_decay": 0.0}
                )
            if bb_bn:
                optimizer.add_param_group(
                    {"params": bb_bn, "lr": lr * backbone_lr_mult, "weight_decay": 0.0}
                )
            if head_w:
                optimizer.add_param_group(
                    {"params": head_w, "lr": lr, "weight_decay": decay}
                )
            if head_b:
                optimizer.add_param_group(
                    {"params": head_b, "lr": lr, "weight_decay": 0.0}
                )
            if head_bn:
                optimizer.add_param_group(
                    {"params": head_bn, "lr": lr, "weight_decay": 0.0}
                )

            print(
                f"[DIFF-LR] Optimizer configured successfully (split_idx={split_layer_idx}):"
            )
            print(
                f"  Backbone Weights: {len(bb_w)} @ lr={lr * backbone_lr_mult:.6f} | decay={decay}"
            )
            print(
                f"  Backbone Biases:  {len(bb_b)} @ lr={lr * backbone_lr_mult:.6f} | decay=0.0"
            )
            print(
                f"  Backbone Norms:   {len(bb_bn)} @ lr={lr * backbone_lr_mult:.6f} | decay=0.0"
            )
            print(f"  Head Weights:     {len(head_w)} @ lr={lr:.6f} | decay={decay}")
            print(f"  Head Biases:      {len(head_b)} @ lr={lr:.6f} | decay=0.0")
            print(f"  Head Norms:       {len(head_bn)} @ lr={lr:.6f} | decay=0.0")

            return optimizer

        SegmentationTrainer.build_optimizer = patched_build_optimizer
        print("[+] Differential LR enabled for this run")

        # ------------------------------------
    # NWD Monkey-Patch for Tiny Object Loss & Assignment
    orig_loss_bbox_iou = None
    orig_tal_bbox_iou = None
    if use_nwd:
        import ultralytics.utils.loss as loss_module
        import ultralytics.utils.tal as tal_module
        import ultralytics.utils.metrics as metrics_module
        
        def make_nwd(C):
            def nwd_metric(box1, box2, xywh=True, **kwargs):
                if not xywh:
                    b1, b2 = box1.clone(), box2.clone()
                    b1[..., 2:] = b1[..., 2:] - b1[..., :2]
                    b1[..., :2] = b1[..., :2] + b1[..., 2:] / 2
                    b2[..., 2:] = b2[..., 2:] - b2[..., :2]
                    b2[..., :2] = b2[..., :2] + b2[..., 2:] / 2
                else:
                    b1, b2 = box1, box2
                    
                # Safely handle Pairwise (N, 4) vs (M, 4) calls from TaskAlignedAssigner
                is_pairwise = (b1.dim() == 2 and b2.dim() == 2 and b1.shape[0] != b2.shape[0])
                if is_pairwise:
                    b1 = b1.unsqueeze(1)  # (N, 1, 4)
                    b2 = b2.unsqueeze(0)  # (1, M, 4)
                    
                cx1, cy1, w1, h1 = b1.unbind(-1)
                cx2, cy2, w2, h2 = b2.unbind(-1)
                
                w1, h1 = torch.clamp(w1, min=1e-7), torch.clamp(h1, min=1e-7)
                w2, h2 = torch.clamp(w2, min=1e-7), torch.clamp(h2, min=1e-7)
                
                w2_dist = (cx1 - cx2)**2 + (cy1 - cy2)**2 + ((w1 - w2)/2)**2 + ((h1 - h2)/2)**2
                nwd = torch.exp(-torch.sqrt(torch.clamp(w2_dist, min=1e-7)) / C)
                
                # Return (N,) for element-wise or (N, M) for pairwise (NO unsqueeze)
                return nwd 
            return nwd_metric

        nwd_func = make_nwd(nwd_c)
        _nwd_inner = nwd_func
        _nwd_dbg = {"calls": 0}
        def _nwd_debug(box1, box2, xywh=True, **kwargs):
            if _nwd_dbg["calls"] < 3:
                print(f"[NWD DEBUG] call={_nwd_dbg['calls']} xywh={xywh} "
                    f"box1.shape={tuple(box1.shape)} box2.shape={tuple(box2.shape)}")
                _nwd_dbg["calls"] += 1
            out = _nwd_inner(box1, box2, xywh, **kwargs)
            if _nwd_dbg["calls"] <= 3:
                print(f"[NWD DEBUG]   out.shape={tuple(out.shape)} "
                    f"out.mean={out.mean().item():.4f}")
            return out
        nwd_func = _nwd_debug
        
        # Save originals
        orig_metrics_bbox_iou = metrics_module.bbox_iou
        orig_loss_bbox_iou = loss_module.bbox_iou
        orig_tal_bbox_iou = tal_module.bbox_iou
        
        # Inject EVERYWHERE
        metrics_module.bbox_iou = nwd_func
        loss_module.bbox_iou = nwd_func
        tal_module.bbox_iou = nwd_func
        print(f"\n[📏] NWD INJECTED (C={nwd_c}) into BboxLoss and TaskAlignedAssigner\n")

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
    
    if use_objectness:
        from ultralytics.nn.modules.head import Segment, Segment26
        old_head = model.model.model[-1]
        is_valid_head = isinstance(old_head, (Segment, Segment26)) and not isinstance(old_head, Segment26WithObjectness)

        if is_valid_head:
            try:
                ch = []
                for i in range(old_head.nl):
                    layer = old_head.cv2[i][0]
                    if hasattr(layer, 'conv'):
                        ch.append(layer.conv.in_channels)
                    elif hasattr(layer, 'in_channels'):
                        ch.append(layer.in_channels)
                    else:
                        raise AttributeError(f"Cannot parse in_channels for cv2[{i}]")
                ch = tuple(ch)

                new_head = Segment26WithObjectness(
                    nc=old_head.nc, nm=old_head.nm, npr=old_head.npr,
                    reg_max=old_head.reg_max, end2end=getattr(old_head, 'end2end', False), ch=ch
                )

                old_state = old_head.state_dict()
                new_state = new_head.state_dict()
                for k, v in old_state.items():
                    if k in new_state and new_state[k].shape == v.shape:
                        new_state[k] = v
                new_head.load_state_dict(new_state, strict=False)
                print("[✅] Head weights loaded (strict=False to allow new cv_obj branch initialization).")
                new_head.stride = old_head.stride
                # Copy routing metadata from old head so Ultralytics' _predict_once works
                new_head.f = getattr(old_head, 'f', None)
                if new_head.f is None:
                    new_head.f = [16, 19, 22]
                    print("[⚠️] old_head.f was None! Hardcoded fallback [16, 19, 22] applied.")
                new_head.i = getattr(old_head, 'i', 23)
                if hasattr(old_head, 'type'):
                    new_head.type = old_head.type
                else:
                    new_head.type = 'ultralytics.nn.modules.head.Segment26'
                if hasattr(old_head, 'args'):
                    new_head.args = old_head.args
                else:
                    new_head.args = (7, 32, 256, 1, True, [256, 512, 512])

                model.model.model[-1] = new_head

                print(f"[🎯] Head replaced with Segment26WithObjectness")
                # Ensure the model's internal args reference the custom head
                # so Ultralytics' save mechanism preserves it
                if hasattr(model.model, 'args') and hasattr(model.model.args, 'model'):
                    pass  # YAML-based models update automatically
                # Force the model to recognize the new head for serialization
                model.model.model[-1].__class__.__module__ = 'ultralytics.nn.modules.head'
                print(f"     cv_obj params: {sum(p.numel() for p in new_head.cv_obj.parameters())}")

                # Preserve custom head through Trainer's model rebuild
                if use_objectness:
                    orig_get_model = SegmentationTrainer.get_model

                    def patched_get_model(self, weights=None, cfg=None, verbose=True):
                        rebuilt = orig_get_model(self, weights=weights, cfg=cfg, verbose=verbose)
                        old_head = rebuilt.model[-1]
                        if isinstance(old_head, Segment26) and not isinstance(old_head, Segment26WithObjectness):
                            ch = tuple(
                                (old_head.cv2[i][0].conv.in_channels if hasattr(old_head.cv2[i][0], 'conv')
                                 else old_head.cv2[i][0].in_channels)
                                for i in range(old_head.nl)
                            )
                            custom_head = Segment26WithObjectness(
                                nc=old_head.nc, nm=old_head.nm, npr=old_head.npr,
                                reg_max=old_head.reg_max, end2end=getattr(old_head, 'end2end', False), ch=ch
                            )
                            old_sd = old_head.state_dict()
                            new_sd = custom_head.state_dict()
                            for k, v in old_sd.items():
                                if k in new_sd and new_sd[k].shape == v.shape:
                                    new_sd[k] = v
                            custom_head.load_state_dict(new_sd, strict=False)
                            custom_head.stride = old_head.stride
                            custom_head.f = getattr(old_head, 'f', None)
                            if custom_head.f is None:
                                custom_head.f = [16, 19, 22]
                                print("[⚠️] old_head.f was None! Hardcoded fallback [16, 19, 22] applied.")
                            custom_head.i = getattr(old_head, 'i', 23)
                            if hasattr(old_head, 'type'):
                                custom_head.type = old_head.type
                            else:
                                custom_head.type = 'ultralytics.nn.modules.head.Segment26'
                            if hasattr(old_head, 'args'):
                                custom_head.args = old_head.args
                            else:
                                custom_head.args = (7, 32, 256, 1, True, [256, 512, 512])
                            rebuilt.model[-1] = custom_head
                            print("[🎯] Custom head preserved through Trainer rebuild")
                        return rebuilt

                    SegmentationTrainer.get_model = patched_get_model
            except Exception as e:
                print(f"❌ Head replacement FAILED: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ cv_obj branch NOT FOUND — head replacement failed.")
            print(f"   Expected Segment or Segment26, but got: {type(old_head).__name__}")
            
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

        if use_differential_lr:
            mlflow.log_param("split_layer_idx", split_layer_idx)
            mlflow.log_param("backbone_lr_mult", backbone_lr_mult)
            mlflow.log_param("use_nwd", use_nwd)
            if use_nwd:
                mlflow.log_param("nwd_c", nwd_c)
                
        mlflow.log_param("use_nwd", use_nwd)
        if use_nwd:
            mlflow.log_param("nwd_c", nwd_c)

        
        try:
            surgical_mode = cfg.get("surgical_mode", "none")
            freeze_arg = cfg.get("freeze", 0)
            
            if surgical_mode == "early_texture":
                head_idx = len(model.model.model) - 1
                print(f"\n[🔪] SURGICAL FINE-TUNING: Configuring early backbone (layers 0-4) + Head (layer {head_idx})")
                # CRITICAL: Bypass Ultralytics' internal freeze logic so it doesn't overwrite our setup
                freeze_arg = 0 
                
                # Manually freeze layers 5 through head_idx-1 (late backbone + neck)
                for i in range(5, head_idx):
                    for param in model.model.model[i].parameters():
                        param.requires_grad = False
                        
                # Ensure layers 0-4 (early texture) and head are trainable
                for i in list(range(5)) + [head_idx]:
                    for param in model.model.model[i].parameters():
                        param.requires_grad = True
                
                trainable = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
                total = sum(p.numel() for p in model.model.parameters())
                print(f"[🔪] Trainable params: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)\n")
            # ------------------------------------
            if use_objectness:
                # NOTE: self.loss_names is a plain list (["Loss"]) at __init__ time, so appending
                # there doesn't error — but SegmentationTrainer.get_validator() runs later (during
                # _setup_train, right before training starts) and unconditionally does
                # self.loss_names = "box_loss", "seg_loss", "cls_loss", "dfl_loss", "sem_loss"
                # which silently overwrites/discards anything appended in __init__. That's why
                # 'obj_loss' never showed up as its own column/curve even though the print fired.
                # Patch get_validator instead, appending AFTER the original call.
                orig_get_validator = SegmentationTrainer.get_validator

                def patched_get_validator(self):
                    validator = orig_get_validator(self)
                    if "obj_loss" not in self.loss_names:
                        self.loss_names = tuple(self.loss_names) + ("obj_loss",)
                        print("[🎯] Registered 'obj_loss' in trainer loss_names")
                    return validator

                SegmentationTrainer.get_validator = patched_get_validator
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
            )
        finally:
            if loss_type in ("focal", "seesaw"):
                v8SegmentationLoss.__init__ = orig_init
                print("[ℹ] Restored v8SegmentationLoss.__init__ to original")

            if use_objectness and orig_call is not None:
                v8SegmentationLoss.__call__ = orig_call
                print("[ℹ] Restored v8SegmentationLoss.__call__ to original")

            if use_objectness and orig_e2e_call is not None:
                E2ELoss.__call__ = orig_e2e_call
                print("[ℹ] Restored E2ELoss.__call__ to original")
            
            if use_differential_lr and orig_build_optimizer is not None:
                SegmentationTrainer.build_optimizer = orig_build_optimizer
                print("[ℹ] Restored SegmentationTrainer.build_optimizer to original")
            
            if use_nwd and orig_tal_bbox_iou is not None:
                import ultralytics.utils.loss as loss_module
                import ultralytics.utils.tal as tal_module
                import ultralytics.utils.metrics as metrics_module
                metrics_module.bbox_iou = orig_metrics_bbox_iou
                loss_module.bbox_iou = orig_loss_bbox_iou
                tal_module.bbox_iou = orig_tal_bbox_iou
                print("[ℹ] Restored bbox_iou to original in loss, tal, and metrics modules")

            if use_objectness and 'orig_get_model' in dir():
                SegmentationTrainer.get_model = orig_get_model
                print("[ℹ] Restored SegmentationTrainer.get_model to original")

            if use_objectness and 'orig_get_validator' in dir():
                SegmentationTrainer.get_validator = orig_get_validator
                print("[ℹ] Restored SegmentationTrainer.get_validator to original")

        # --- Preserve custom head in saved checkpoint ---
        if use_objectness:
            import copy
            save_dir = getattr(model, 'trainer', None)
            if save_dir and hasattr(save_dir, 'save_dir'):
                best_path = os.path.join(str(save_dir.save_dir), 'weights', 'best.pt')
                last_path = os.path.join(str(save_dir.save_dir), 'weights', 'last.pt')
                for p in [best_path, last_path]:
                    if os.path.exists(p):
                        ckpt = torch.load(p, map_location='cpu')
                        # Inject the custom head class reference so it survives reload
                        if 'model' in ckpt and hasattr(ckpt['model'], 'model'):
                            head = ckpt['model'].model[-1]
                            if not hasattr(head, 'cv_obj'):
                                print(f"[⚠️] {os.path.basename(p)}: head is {type(head).__name__}, attempting head swap...")
                                # Rebuild head with cv_obj and copy weights
                                ch = tuple(
                                    (head.cv2[i][0].conv.in_channels if hasattr(head.cv2[i][0], 'conv') else head.cv2[i][0].in_channels)
                                    for i in range(head.nl)
                                )
                                new_head = Segment26WithObjectness(
                                    nc=head.nc, nm=head.nm, npr=head.npr,
                                    reg_max=head.reg_max, end2end=getattr(head, 'end2end', False), ch=ch
                                )
                                # Copy all matching weights from old head
                                old_sd = head.state_dict()
                                new_sd = new_head.state_dict()
                                for k, v in old_sd.items():
                                    if k in new_sd and new_sd[k].shape == v.shape:
                                        new_sd[k] = v
                                # Copy cv_obj weights from the full model state_dict
                                full_sd = ckpt['model'].state_dict()
                                prefix = f"model.{len(ckpt['model'].model)-1}."
                                for k, v in full_sd.items():
                                    if k.startswith(prefix) and 'cv_obj' in k:
                                        local_key = k[len(prefix):]
                                        if local_key in new_sd:
                                            new_sd[local_key] = v
                                new_head.load_state_dict(new_sd)
                                new_head.stride = head.stride
                                ckpt['model'].model[-1] = new_head
                                torch.save(ckpt, p)
                                print(f"[✅] {os.path.basename(p)}: head swapped to Segment26WithObjectness")

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