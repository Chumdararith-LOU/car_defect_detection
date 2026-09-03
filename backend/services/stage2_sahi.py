from pathlib import Path

import cv2
import numpy as np
import yaml
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

import sys

import ultralytics.nn.modules.head as head_module

# Inject custom head class so torch.load can unpickle the objectness model
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT))
from src.stage2.models.segment_head_with_obj import (  # noqa: E402
    Segment26WithObjectness,
)

head_module.Segment26WithObjectness = Segment26WithObjectness

CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "inference"
    / "sahi_production.yaml"
)
with open(CONFIG_PATH) as f:
    SAHI_CFG = yaml.safe_load(f)

_DEFAULT_CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_part",
    5: "corrosion",
    6: "disjoint_part",
}

# Models emit "broken_lamp"; operators' canonical umbrella term is "broken_part"
CANONICAL_ALIASES = {"broken_lamp": "broken_part"}

_CACHED_MODELS = {}


def mask_ios(a_mask, a_area, b_mask, b_area):
    inter = int(np.logical_and(a_mask, b_mask).sum())
    smaller = min(a_area, b_area)
    return inter / smaller if smaller > 0 else 0.0


def _boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def run_sahi_inference(
    img_np: np.ndarray,
    inspection_id: str,
    preset: str = "balanced",
    device: str = "cpu",
) -> list:
    """Runs SAHI sliced inference with per-class rules and mask-IOS NMS."""
    preset_cfg = SAHI_CFG["presets"].get(preset, SAHI_CFG["presets"]["balanced"])
    rules = preset_cfg["class_rules"]
    model_conf = min(float(r["conf"]) for r in rules.values())

    routing = SAHI_CFG.get("routing_strategy", {}).get(
        preset, {"models": ["objectness_branch_new"], "merge": "none"}
    )
    model_names = routing["models"]

    global_gating = SAHI_CFG.get("two_tier_gating", {})
    preset_gating = preset_cfg.get("two_tier_gating", {})
    gating_enabled = global_gating.get("enabled", False)
    gating_model = global_gating.get("applies_to", "objectness_branch_new")
    obj_threshold = float(
        preset_gating.get("obj_threshold", global_gating.get("obj_threshold", 0.20))
    )
    cls_threshold = float(
        preset_gating.get("cls_threshold", global_gating.get("cls_threshold", 0.25))
    )

    model_registry = SAHI_CFG.get("model_registry", {})
    loaded_models = {}
    for model_name in model_names:
        model_path = model_registry.get(model_name)
        if not model_path:
            continue
        # Resolve relative paths against project root (server cwd may be backend/)
        if not Path(model_path).is_absolute():
            model_path = str(_PROJECT_ROOT / model_path)
        if model_name not in _CACHED_MODELS:
            _CACHED_MODELS[model_name] = AutoDetectionModel.from_pretrained(
                model_type=SAHI_CFG.get("model_type", "yolov8"),
                model_path=model_path,
                confidence_threshold=model_conf,
                device=device,
            )
        loaded_models[model_name] = _CACHED_MODELS[model_name]

    if not loaded_models:
        raise ValueError(f"No registry models found for preset '{preset}'")
    img_h, img_w = img_np.shape[:2]
    s = SAHI_CFG["sahi"]

    # Run SAHI on each loaded model
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
            except Exception:
                continue

            m = np.asarray(p.mask.bool_mask) > 0.5
            area = int(m.sum())

            # Canonicalize name first so name-keyed rules hit across both
            # taxonomy families (id 4 is broken_lamp OR disjoint_part
            # depending on the model).
            raw_name = class_names.get(cls_id, str(p.category.name))
            det_name = CANONICAL_ALIASES.get(raw_name, raw_name)

            # Per-class acceptance rules (name-keyed)
            r = rules.get(det_name, rules.get("default", {"conf": 0.25, "min_area": 0}))
            if p.score.value < float(r["conf"]) or area < int(r["min_area"]):
                continue

            # Two-tier objectness gating (applies only to the designated model)
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

    # Apply merge strategy
    merge_mode = routing.get("merge", "none")
    if merge_mode == "per_class":
        class_routing = routing.get("class_routing", {})
        dets = [
            d
            for d in all_dets
            if class_routing.get(d["name"]) is None
            or d["model_name"] == class_routing.get(d["name"])
        ]
    else:  # "none" or "union"
        dets = all_dets

    for d in dets:
        d.pop("model_name", None)

    # Mask-IOS NMS (keyed by canonical name: the two taxonomy families
    # use different raw ids for the same class, so id-keyed dedup lets
    # cross-model duplicates survive)
    thr = float(SAHI_CFG["nms"]["ios_threshold"])
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

    # Format for frontend
    defects = []
    for i, d in enumerate(kept):
        x1, y1, x2, y2 = d["bbox"]
        norm_bbox = (
            float(x1) / img_w,
            float(y1) / img_h,
            float(x2) / img_w,
            float(y2) / img_h,
        )

        # Extract polygon from mask
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

    return defects
