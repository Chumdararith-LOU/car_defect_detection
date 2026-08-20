from pathlib import Path

import cv2
import numpy as np
import yaml
from sahi import AutoDetectionModel
from sahi.predict import get_sliced_prediction

CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "inference"
    / "sahi_production.yaml"
)
with open(CONFIG_PATH) as f:
    SAHI_CFG = yaml.safe_load(f)

CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_lamp",
    5: "corrosion",
    6: "disjoint_part",
}


def mask_ios(a_mask, a_area, b_mask, b_area):
    inter = int(np.logical_and(a_mask, b_mask).sum())
    smaller = min(a_area, b_area)
    return inter / smaller if smaller > 0 else 0.0


def _boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def run_sahi_inference(
    img_np: np.ndarray,
    model_path: str,
    inspection_id: str,
    preset: str = "balanced",
    device: str = "cpu",
) -> list:
    """Runs SAHI sliced inference with per-class rules and mask-IOS NMS."""
    preset_cfg = SAHI_CFG["presets"].get(preset, SAHI_CFG["presets"]["balanced"])
    rules = preset_cfg["class_rules"]
    model_conf = min(float(r["conf"]) for r in rules.values())

    # Initialize SAHI model
    sahi_model = AutoDetectionModel.from_pretrained(
        model_type=SAHI_CFG.get("model_type", "yolov8"),
        model_path=model_path,
        confidence_threshold=model_conf,
        device=device,
    )

    s = SAHI_CFG["sahi"]
    result = get_sliced_prediction(
        img_np,
        sahi_model,
        slice_height=int(s["slice_size"]),
        slice_width=int(s["slice_size"]),
        overlap_height_ratio=float(s["overlap_ratio"]),
        overlap_width_ratio=float(s["overlap_ratio"]),
    )

    img_h, img_w = img_np.shape[:2]
    dets = []

    for p in result.object_prediction_list:
        try:
            cls_id = int(p.category.id)
        except Exception:
            continue

        m = np.asarray(p.mask.bool_mask) > 0.5
        area = int(m.sum())

        # Per-class acceptance rules
        r = rules.get(str(cls_id), rules.get("default", {"conf": 0.25, "min_area": 0}))
        if p.score.value < float(r["conf"]) or area < int(r["min_area"]):
            continue

        ys, xs = np.nonzero(m)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

        dets.append(
            {
                "cls": cls_id,
                "name": CLASS_NAMES.get(cls_id, str(p.category.name)),
                "score": float(p.score.value),
                "mask": m,
                "area": area,
                "bbox": bbox,
            }
        )

    # Mask-IOS NMS
    thr = float(SAHI_CFG["nms"]["ios_threshold"])
    dets.sort(key=lambda d: -d["score"])
    kept = []
    for d in dets:
        if not any(
            d["cls"] == k["cls"]
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
