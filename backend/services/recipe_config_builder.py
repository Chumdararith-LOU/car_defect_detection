"""Pure recipe-to-config builder (Stage 2 Training Platform, Phase E prep).

Turns a recipe dict into the EXACT config dict each stage's trainer consumes:

- Stage 2 / Stage 3 -> FLAT schema (matches ``src/stage2/train/train.py`` and
  ``src/stage3/train/train.py``). The base-weights key is ``model_preset``
  because the trainer reads ``cfg.get("model_preset", ...)``
  (src/stage2/train/train.py:249) — NOT ``model``.
- Stage 1 -> NESTED schema (matches ``src/stage1/train/train_sod.py``):
  ``project.* / model.* / dataset.* / training.* / pipeline.*``. The trainer
  loads base weights via ``training.backbone`` (train_sod.py:133), so both
  ``model.preset`` and ``training.backbone`` are set to the checkpoint path.

This is a pure function: no file IO, no subprocess. Returns a plain dict.
"""

from typing import Any


def _freeze_value(recipe: dict) -> int:
    if recipe.get("freeze_mode", "none") == "none":
        return 0
    return int(recipe.get("freeze_layers") or 0)


def _flat_config(
    recipe: dict, dataset_yaml: str, checkpoint_path: str, run_name: str
) -> dict:
    cfg: dict[str, Any] = {
        "task": "segment",
        "model_preset": checkpoint_path,
        "project_name": recipe.get("name") or run_name,
        "run_name": run_name,
        "dataset_config": dataset_yaml,
        "data": dataset_yaml,
        "imgsz": recipe.get("imgsz", 640),
        "epochs": recipe.get("epochs", 100),
        "batch_size": recipe.get("batch_size", 8),
        "optimizer": recipe.get("optimizer", "auto"),
        "lr0": recipe.get("lr0", 0.01),
        "lrf": recipe.get("lrf", 0.01),
        "patience": recipe.get("patience", 20),
        "multi_scale": False,
        "seed": 42,
        "freeze": _freeze_value(recipe),
        "loss_type": recipe.get("loss_type", "bce"),
    }

    if recipe.get("lr_mode") == "differential":
        cfg["differential_lr"] = True
        cfg["split_layer_idx"] = recipe.get("split_layer_idx")
        cfg["backbone_lr_mult"] = recipe.get("backbone_lr_mult")
    else:
        cfg["differential_lr"] = False

    if recipe.get("loss_type") == "focal":
        cfg["fl_gamma"] = recipe.get("fl_gamma", 2.0)
        cfg["fl_alpha"] = recipe.get("fl_alpha", 0.5)
        cfg["fl_scale"] = recipe.get("fl_scale", 1.0)

    augmentations = recipe.get("augmentations")
    if augmentations:
        # Trainer reads aug = cfg.get("augmentations", cfg) then aug.get(...).
        cfg["augmentations"] = dict(augmentations)

    return cfg


def _nested_config(
    recipe: dict, dataset_yaml: str, checkpoint_path: str, run_name: str
) -> dict:
    loss_type = recipe.get("loss_type", "bce")
    cfg: dict[str, Any] = {
        "project": {"name": run_name},
        "model": {"preset": checkpoint_path},
        "dataset": {
            "data": dataset_yaml,
            "processed_dir": dataset_yaml,
            "imgsz": recipe.get("imgsz", 640),
        },
        "logging": {
            "experiment_name": recipe.get("name") or run_name,
            "run_name": run_name,
        },
        "training": {
            "backbone": checkpoint_path,
            "epochs": recipe.get("epochs", 50),
            "batch_size": recipe.get("batch_size", 32),
            "lr0": recipe.get("lr0", 0.001),
            "lrf": recipe.get("lrf", 0.01),
            "optimizer": recipe.get("optimizer", "auto"),
            "patience": recipe.get("patience", 100),
            "weight_decay": 0.0005,
            "multi_scale": False,
            "seed": 42,
            "loss_function": (
                "FocalCrossEntropyLoss" if loss_type == "focal" else "BCEWithLogitsLoss"
            ),
            "fl_gamma": recipe.get("fl_gamma", 2.0),
        },
        "pipeline": {
            "loss_type": loss_type,
            "fl_gamma": recipe.get("fl_gamma", 2.0),
            "fl_alpha": recipe.get("fl_alpha", 0.5),
            "fl_scale": recipe.get("fl_scale", 1.0),
        },
    }

    augmentations = recipe.get("augmentations")
    if augmentations:
        cfg["training"]["augmentations"] = dict(augmentations)

    return cfg


def build_config_from_recipe(
    recipe: dict, dataset_yaml: str, checkpoint_path: str, run_name: str
) -> dict:
    """Build the trainer config dict for a recipe. Pure; returns dict only."""
    stage = (recipe.get("stage") or "stage2").lower()
    if stage == "stage1":
        return _nested_config(recipe, dataset_yaml, checkpoint_path, run_name)
    return _flat_config(recipe, dataset_yaml, checkpoint_path, run_name)
