"""Stage 2: Multi-class defect segmentation via Slicing Aided Hyper Inference.

Ports the proven production logic (SAHI tiling, per-class acceptance rules,
two-tier objectness gating, mask-IoS NMS, and per-class multi-model routing)
and adapts it to the inference-api model registry and config.

:func:`run_defect_inference` supports both preset-driven routing (the default)
and explicit overrides for the model list, merge strategy, and per-class
routing, enabling arbitrary model combinations or a single individual model.
"""
import logging
from typing import Optional

import cv2
import numpy as np
import yaml
from sahi.predict import get_sliced_prediction

from app.config import settings
from app.core.model_registry import model_registry

logger = logging.getLogger("stage2_defect")

_CONFIG_PATH = settings.configs_dir / settings.production_config
with open(_CONFIG_PATH) as _f:
    STAGE2_CFG = yaml.safe_load(_f)

_DEFAULT_CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_part",
    5: "corrosion",
    6: "disjoint_part",
}

# Models may emit "broken_lamp"; the canonical operator term is "broken_part".
CANONICAL_ALIASES = {"broken_lamp": "broken_part"}


def mask_ios(a_mask, a_area, b_mask, b_area) -> float:
    inter = int(np.logical_and(a_mask, b_mask).sum())
    smaller = min(a_area, b_area)
    return inter / smaller if smaller > 0 else 0.0


def _boxes_overlap(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def run_defect_inference(
    img_np: np.ndarray,
    inspection_id: str,
    preset: str = "safety",
    device: str = "cpu",
    models: Optional[list] = None,
    merge: Optional[str] = None,
    class_routing: Optional[dict] = None,
) -> list:
    """Run SAHI sliced defect inference.

    Args:
        img_np: RGB image as a numpy array.
        inspection_id: unique id used to prefix defect ids.
        preset: operating preset name (selects class_rules + gating defaults).
        device: torch device string.
        models: optional override list of model names (else from preset routing).
        merge: optional override merge mode ("none" | "union" | "per_class").
        class_routing: optional override dict mapping class -> model name.

    Returns:
        List of defect dicts ready for Stage 4 context mapping.
    """
    preset_cfg = STAGE2_CFG["presets"].get(preset, STAGE2_CFG["presets"]["safety"])
    rules = preset_cfg["class_rules"]

    # Resolve routing: explicit overrides take precedence over the preset.
    routing = STAGE2_CFG.get("routing_strategy", {}).get(preset, {})
    model_names = models if models is not None else routing.get("models", [])
    merge_mode = merge if merge is not None else routing.get("merge", "none")
    routing_table = (
        class_routing if class_routing is not None else routing.get("class_routing", {})
    )

    if not model_names:
        raise ValueError(f"No models resolved for preset '{preset}'")

    # Two-tier gating config.
    global_gating = STAGE2_CFG.get("two_tier_gating", {})
    preset_gating = preset_cfg.get("two_tier_gating", {})
    gating_enabled = global_gating.get("enabled", False)
    gating_model = global_gating.get("applies_to", "objectness_branch_new")
    obj_threshold = float(
        preset_gating.get("obj_threshold", global_gating.get("obj_threshold", 0.20))
    )
    cls_threshold = float(
        preset_gating.get("cls_threshold", global_gating.get("cls_threshold", 0.25))
    )

    # Load models via the registry (stage2 -> sahi AutoDetectionModel).
    loaded_models = {}
    for name in model_names:
        try:
            loaded_models[name] = model_registry.get_model(name, device=device)
        except Exception as e:  # noqa: BLE001
            logger.warning("Could not load model '%s': %s", name, e)
    if not loaded_models:
        raise ValueError(f"No models could be loaded for preset '{preset}'")

    img_h, img_w = img_np.shape[:2]
    s = STAGE2_CFG["sahi"]

    all_dets = []
    for model_name, sahi_model in loaded_models.items():
        try:
            class_names = {int(k): v for k, v in sahi_model.model.names.items()}
        except AttributeError:
            class_names = _DEFAULT_CLASS_NAMES

        result = get_sliced_prediction(
            img_np,
            sahi_model,
            slice_height=int(s["slice_size"]),
            slice_width=int(s["slice_size"]),
            overlap_height_ratio=float(s["overlap_ratio"]),
            overlap_width_ratio=float(s["overlap_ratio"]),
        )

        for p in result.object_prediction_list:
            try:
                cls_id = int(p.category.id)
            except Exception:  # noqa: BLE001
                continue
            m = np.asarray(p.mask.bool_mask) > 0.5
            area = int(m.sum())

            # Canonicalize name so name-keyed rules hit across taxonomy families.
            raw_name = class_names.get(cls_id, str(p.category.name))
            det_name = CANONICAL_ALIASES.get(raw_name, raw_name)

            # Per-class acceptance rules (name-keyed).
            r = rules.get(det_name, rules.get("default", {"conf": 0.25, "min_area": 0}))
            if p.score.value < float(r["conf"]) or area < int(r["min_area"]):
                continue

            # Two-tier objectness gating (applies only to the designated model).
            if gating_enabled and model_name == gating_model:
                if p.score.value < obj_threshold:
                    continue
                if p.score.value < cls_threshold:
                    det_name = "defect_unknown"

            ys, xs = np.nonzero(m)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            all_dets.append(
                {
                    "cls": cls_id,
                    "name": det_name,
                    "score": float(p.score.value),
                    "mask": m,
                    "area": area,
                    "bbox": bbox,
                    "model_name": model_name,
                }
            )

    # Apply merge strategy.
    if merge_mode == "per_class":
        dets = [
            d
            for d in all_dets
            if routing_table.get(d["name"]) is None
            or d["model_name"] == routing_table.get(d["name"])
        ]
    else:  # "none" or "union"
        dets = all_dets
    for d in dets:
        d.pop("model_name", None)

    # Mask-IoS NMS (keyed by canonical name).
    thr = float(STAGE2_CFG["nms"]["ios_threshold"])
    dets.sort(key=lambda d: -d["score"])
    kept = []
    for d in dets:
        if not any(
            d["name"] == k["name"]
            and _boxes_overlap(d["bbox"], k["bbox"])
            and mask_ios(d["mask"], d["area"], k["mask"], k["area"]) >= thr
            for k in kept
        ):
            kept.append(d)

    # Format for downstream stages.
    defects = []
    for i, d in enumerate(kept):
        x1, y1, x2, y2 = d["bbox"]
        norm_bbox = (
            float(x1) / img_w,
            float(y1) / img_h,
            float(x2) / img_w,
            float(y2) / img_h,
        )
        contours, _ = cv2.findContours(
            d["mask"].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        norm_polygon = []
        if contours:
            cnt = max(contours, key=cv2.contourArea)
            norm_polygon = [
                (float(pt[0][0]) / img_w, float(pt[0][1]) / img_h) for pt in cnt
            ]
        defects.append(
            {
                "defect_id": f"{inspection_id}_S2_{i:03d}",
                "defect_class": d["name"],
                "confidence": d["score"],
                "global_bbox_xyxy": norm_bbox,
                "polygon": norm_polygon,
                "assigned_panel": "Unknown",
                "containment_ratio_iod": 0.0,
                "damage_severity_index_dsi": min(0.99, d["area"] / 5000.0),
            }
        )
    logger.info("Stage2 | %d defects kept after mask-IoS NMS", len(defects))
    return defects
