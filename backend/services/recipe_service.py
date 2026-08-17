"""CRUD service for training recipes (Stage 2 Training Platform, Phase D).

A recipe binds a training strategy (freeze/LR/loss/augmentations) to a
taxonomy. Stage is always derived from the taxonomy — never from the client.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from services import taxonomy_service
from services.platform_db import get_db

logger = logging.getLogger(__name__)

PRESET_IMMUTABLE_MSG = "preset is immutable - duplicate it"

STAGE2_TAXONOMY_NAME = "stage2_7class_defects"

UPDATABLE_FIELDS = (
    "name",
    "description",
    "base_strategy",
    "base_checkpoint_id",
    "freeze_mode",
    "freeze_layers",
    "lr_mode",
    "split_layer_idx",
    "backbone_lr_mult",
    "loss_type",
    "fl_gamma",
    "fl_alpha",
    "fl_scale",
    "imgsz",
    "batch_size",
    "epochs",
    "optimizer",
    "lr0",
    "lrf",
    "patience",
    "augmentations",
)


class RecipeNotFoundError(LookupError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_strategy(fields: dict) -> None:
    if fields.get("freeze_mode", "none") != "none":
        layers = fields.get("freeze_layers")
        if not isinstance(layers, int) or layers <= 0:
            raise ValueError(
                "freeze_layers must be an integer > 0 when freeze_mode != 'none'"
            )
    if fields.get("lr_mode", "uniform") == "differential":
        if (
            fields.get("split_layer_idx") is None
            or fields.get("backbone_lr_mult") is None
        ):
            raise ValueError(
                "lr_mode 'differential' requires split_layer_idx and backbone_lr_mult"
            )


def _checkpoint_exists(checkpoint_id: str) -> bool:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _row_to_recipe(row) -> dict:
    data = dict(row)
    if data.get("augmentations"):
        data["augmentations"] = json.loads(data["augmentations"])
    data["is_preset"] = bool(data["is_preset"])
    return data


def list_recipes(stage: Optional[str] = None, presets_only: bool = False) -> list[dict]:
    conn = get_db()
    try:
        sql = "SELECT * FROM recipes"
        clauses: list[str] = []
        params: list = []
        if stage:
            clauses.append("stage = ?")
            params.append(stage)
        if presets_only:
            clauses.append("is_preset = 1")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at"
        rows = conn.execute(sql, params).fetchall()
        return [_row_to_recipe(r) for r in rows]
    finally:
        conn.close()


def get_recipe(recipe_id: str) -> dict:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
        ).fetchone()
        if row is None:
            raise RecipeNotFoundError(recipe_id)
        return _row_to_recipe(row)
    finally:
        conn.close()


def create_recipe(data: dict, is_preset: bool = False) -> dict:
    # Stage is derived from the taxonomy; client-supplied stage is ignored.
    taxonomy = taxonomy_service.get_taxonomy(data["taxonomy_id"])
    _validate_strategy(data)
    if data.get("name"):
        data["name"] = data["name"].strip()
    if not data.get("name"):
        raise ValueError("name must not be blank")
    base_checkpoint_id = data.get("base_checkpoint_id")
    if base_checkpoint_id and not _checkpoint_exists(base_checkpoint_id):
        raise LookupError(f"checkpoint not found: {base_checkpoint_id}")

    recipe_id = str(uuid.uuid4())
    now = _now_iso()
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO recipes
                (id, name, stage, taxonomy_id, description, base_strategy,
                 base_checkpoint_id, freeze_mode, freeze_layers, lr_mode,
                 split_layer_idx, backbone_lr_mult, loss_type, fl_gamma,
                 fl_alpha, fl_scale, imgsz, batch_size, epochs, optimizer,
                 lr0, lrf, patience, augmentations, is_preset, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_id,
                data["name"],
                taxonomy["stage"],
                data["taxonomy_id"],
                data.get("description"),
                data.get("base_strategy", "from_checkpoint"),
                base_checkpoint_id,
                data.get("freeze_mode", "none"),
                data.get("freeze_layers"),
                data.get("lr_mode", "uniform"),
                data.get("split_layer_idx"),
                data.get("backbone_lr_mult"),
                data.get("loss_type", "bce"),
                data.get("fl_gamma", 2.0),
                data.get("fl_alpha", 0.5),
                data.get("fl_scale", 1.0),
                data.get("imgsz", 640),
                data.get("batch_size", 8),
                data.get("epochs", 100),
                data.get("optimizer", "SGD"),
                data.get("lr0", 0.01),
                data.get("lrf", 0.01),
                data.get("patience", 20),
                (
                    json.dumps(data["augmentations"])
                    if data.get("augmentations")
                    else None
                ),
                1 if is_preset else 0,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(
        "Created recipe %s (stage=%s, preset=%s)",
        data["name"],
        taxonomy["stage"],
        is_preset,
    )
    return get_recipe(recipe_id)


def update_recipe(recipe_id: str, patch: dict) -> dict:
    existing = get_recipe(recipe_id)
    if existing["is_preset"]:
        raise PermissionError(PRESET_IMMUTABLE_MSG)

    merged = {
        **existing,
        **{k: v for k, v in patch.items() if k in UPDATABLE_FIELDS},
    }
    if merged.get("name") is not None:
        merged["name"] = str(merged["name"]).strip()
    if not merged.get("name"):
        raise ValueError("name must not be blank")
    _validate_strategy(merged)
    if merged.get("base_checkpoint_id") and not _checkpoint_exists(
        merged["base_checkpoint_id"]
    ):
        raise LookupError(f"checkpoint not found: {merged['base_checkpoint_id']}")

    assignments = ", ".join(f"{k} = ?" for k in UPDATABLE_FIELDS)
    values = []
    for k in UPDATABLE_FIELDS:
        v = merged.get(k)
        if k == "augmentations" and v is not None:
            v = json.dumps(v)
        values.append(v)

    conn = get_db()
    try:
        conn.execute(
            f"UPDATE recipes SET {assignments} WHERE id = ?",
            (*values, recipe_id),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("Updated recipe %s", recipe_id)
    return get_recipe(recipe_id)


def delete_recipe(recipe_id: str) -> None:
    existing = get_recipe(recipe_id)
    if existing["is_preset"]:
        raise PermissionError(PRESET_IMMUTABLE_MSG)

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM chain_steps WHERE recipe_id = ?",
            (recipe_id,),
        ).fetchone()
        if row and row["n"] > 0:
            raise PermissionError(f"recipe {recipe_id} is referenced by chain_steps")
        conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()
    finally:
        conn.close()
    logger.info("Deleted recipe %s", recipe_id)


def seed_presets() -> None:
    """Idempotently seed the four Stage 2 strategy presets."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM taxonomies WHERE name = ? AND stage = 'stage2'",
            (STAGE2_TAXONOMY_NAME,),
        ).fetchone()
        if row is None:
            logger.warning(
                "Cannot seed recipe presets: taxonomy %s not found",
                STAGE2_TAXONOMY_NAME,
            )
            return
        taxonomy_id = row["id"]
        ckpt = conn.execute(
            "SELECT id FROM checkpoints WHERE name = 'yolo26m-seg.pt' "
            "ORDER BY created_at LIMIT 1"
        ).fetchone()
        coco_checkpoint_id = ckpt["id"] if ckpt else None
        existing = {
            r["name"]
            for r in conn.execute(
                "SELECT name FROM recipes WHERE is_preset = 1"
            ).fetchall()
        }
    finally:
        conn.close()

    warmup_aug = {"mosaic": 0.0, "scale": 0.3, "degrees": 15.0, "fliplr": 0.5}
    shared = {
        "taxonomy_id": taxonomy_id,
        "description": None,
        "base_checkpoint_id": None,
        "freeze_layers": None,
        "split_layer_idx": None,
        "backbone_lr_mult": None,
        "fl_gamma": 2.0,
        "fl_alpha": 0.5,
        "fl_scale": 1.0,
        "imgsz": 640,
        "batch_size": 8,
        "epochs": 100,
        "optimizer": "SGD",
        "lr0": 0.01,
        "lrf": 0.01,
        "patience": 20,
        "augmentations": None,
    }
    presets = [
        {
            **shared,
            "name": "Direct from COCO",
            "description": "Train directly from stock COCO pretrained weights.",
            "base_strategy": "native_coco",
            "base_checkpoint_id": coco_checkpoint_id,
            "freeze_mode": "none",
            "lr_mode": "uniform",
            "loss_type": "bce",
            "optimizer": "auto",
        },
        {
            **shared,
            "name": "Freeze Backbone",
            "description": "Freeze the first 15 layers; train head + neck.",
            "base_strategy": "from_checkpoint",
            "freeze_mode": "freeze_n",
            "freeze_layers": 15,
            "lr_mode": "uniform",
            "loss_type": "focal",
            "fl_gamma": 1.5,
            "fl_alpha": 0.5,
        },
        {
            **shared,
            "name": "Head-Only Warmup",
            "description": "Freeze everything except the head; short warmup at 1024.",
            "base_strategy": "from_checkpoint",
            "freeze_mode": "head_only",
            "freeze_layers": 23,
            "lr_mode": "uniform",
            "lr0": 0.005,
            "loss_type": "focal",
            "fl_gamma": 2.0,
            "fl_alpha": 0.5,
            "fl_scale": 1.0,
            "imgsz": 1024,
            "batch_size": 4,
            "epochs": 15,
            "patience": 30,
            "augmentations": warmup_aug,
        },
        {
            **shared,
            "name": "Differential LR Fine-tune",
            "description": "Full fine-tune with a lower backbone LR after warmup.",
            "base_strategy": "from_checkpoint",
            "freeze_mode": "none",
            "lr_mode": "differential",
            "split_layer_idx": 23,
            "backbone_lr_mult": 0.1,
            "lr0": 0.0003,
            "loss_type": "focal",
            "imgsz": 1024,
            "batch_size": 4,
            "epochs": 120,
            "augmentations": warmup_aug,
        },
    ]
    for preset in presets:
        if preset["name"] in existing:
            continue
        create_recipe(preset, is_preset=True)
    logger.info("Recipe presets seeded (idempotent)")
