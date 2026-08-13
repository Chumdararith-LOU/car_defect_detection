import logging

import cv2
import numpy as np
from shapely.geometry import Polygon

from schemas.inspection import SuppressedDetection, UnclassifiedAnomaly

logger = logging.getLogger("Stage4")

# Stage 3 class label -> frontend PanelId (snake_case) mapping.
LABEL_TO_PANEL_ID = {
    "Quarter-panel": "quarter_panel",
    "Front-wheel": "front_wheel",
    "Back-window": "back_window",
    "Trunk": "trunk",
    "Front-door": "front_door",
    "Rocker-panel": "rocker_panel",
    "Grille": "grille",
    "Windshield": "windshield",
    "Front-window": "front_window",
    "Back-door": "back_door",
    "Headlight": "headlight",
    "Back-wheel": "back_wheel",
    "Back-windshield": "back_windshield",
    "Hood": "hood",
    "Fender": "fender",
    "Tail-light": "tail_light",
    "License-plate": "license_plate",
    "Front-bumper": "front_bumper",
    "Back-bumper": "back_bumper",
    "Mirror": "mirror",
    "Roof": "roof",
}

TIRE_PANEL_IDS = {"front_wheel", "back_wheel"}
NON_CAR_IOD_THRESHOLD = 0.02
RESCUE_OVERLAP_THRESHOLD = 0.30
RESCUE_MIN_AREA_RATIO = 0.0005


def _to_polygon(points):
    """Builds a valid Shapely polygon from a list of [x, y] points."""
    try:
        poly = Polygon(points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.area <= 0:
            return None
        return poly
    except Exception:
        return None


def compute_iod(defect_polygon, panel_polygon) -> float:
    """Intersection-over-Defect: area(defect ∩ panel) / area(defect)."""
    try:
        defect = _to_polygon(defect_polygon)
        panel = _to_polygon(panel_polygon)
        if defect is None or panel is None:
            return 0.0
        return float(defect.intersection(panel).area / defect.area)
    except Exception:
        return 0.0


def _get_field(defect, key):
    if hasattr(defect, "get"):
        return defect.get(key)
    return getattr(defect, key, None)


_PYDANTIC_FIELD_MAP = {
    "assigned_panel": "panel",
    "containment_ratio_iod": "iod",
}


def _set_field(defect, key, value):
    if hasattr(defect, "get"):
        defect[key] = value
    else:
        field_name = _PYDANTIC_FIELD_MAP.get(key) or key
        setattr(defect, field_name, value)


def _to_suppressed(defect, panel_id, reason) -> SuppressedDetection:
    bbox = _get_field(defect, "global_bbox_xyxy") or _get_field(defect, "bbox") or []
    defect_id = _get_field(defect, "defect_id") or _get_field(defect, "id") or "unknown"
    return SuppressedDetection(
        id=str(defect_id),
        predicted_class=str(_get_field(defect, "defect_class") or "unknown"),
        confidence=float(_get_field(defect, "confidence") or 0.0),
        bbox=[float(v) for v in bbox],
        polygon=_get_field(defect, "polygon") or None,
        panel=panel_id,
        reason=reason,
    )


def assign_defects_to_panels(defects, panels, iod_threshold=0.1):
    """Assigns each defect to the panel with the highest IoD.

    Returns (kept_defects, suppressed_detections). Defects on tire panels
    or clearly outside the car are suppressed instead of reported.
    """
    panel_shapes = []
    for panel in panels:
        shape = _to_polygon(panel.get("polygon", []))
        if shape is not None:
            panel_shapes.append((panel.get("label"), shape))

    kept = []
    suppressed = []
    assigned_count = 0
    for defect in defects:
        defect_shape = _to_polygon(_get_field(defect, "polygon") or [])
        best_iod = 0.0
        best_label = None
        if defect_shape is not None:
            for label, panel_shape in panel_shapes:
                try:
                    iod = float(
                        defect_shape.intersection(panel_shape).area / defect_shape.area
                    )
                except Exception:
                    iod = 0.0
                if iod > best_iod:
                    best_iod = iod
                    best_label = label

        if best_iod >= iod_threshold and best_label is not None:
            panel_id = LABEL_TO_PANEL_ID.get(best_label, "Unknown")
        else:
            panel_id = "Unknown"

        if panel_id in TIRE_PANEL_IDS:
            suppressed.append(_to_suppressed(defect, panel_id, "tire"))
            continue
        if panel_id == "Unknown" and best_iod < NON_CAR_IOD_THRESHOLD:
            suppressed.append(_to_suppressed(defect, "Unknown", "non_car_context"))
            continue

        _set_field(defect, "assigned_panel", panel_id)
        _set_field(defect, "containment_ratio_iod", best_iod)
        if panel_id != "Unknown":
            assigned_count += 1
        kept.append(defect)

    logger.info(
        "Stage 4: Assigned %d/%d defects to panels (threshold=%.2f), suppressed %d",
        assigned_count,
        len(defects),
        iod_threshold,
        len(suppressed),
    )
    return kept, suppressed


def rescue_unclassified_anomalies(
    binary_mask, defects, panels, inspection_id, iod_threshold=0.1
):
    """Extracts Stage 1 saliency blobs not covered by any Stage 2 defect."""
    anomalies = []
    if binary_mask is None:
        return anomalies

    mask = np.ascontiguousarray(binary_mask.astype(np.uint8))
    img_h, img_w = mask.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return anomalies

    panel_shapes = []
    for panel in panels:
        shape = _to_polygon(panel.get("polygon", []))
        if shape is not None:
            panel_shapes.append((panel.get("label"), shape))
    if not panel_shapes:
        return anomalies

    defect_shapes = [_to_polygon(_get_field(d, "polygon") or []) for d in defects]

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < RESCUE_MIN_AREA_RATIO * img_w * img_h:
            continue

        pts = contour.squeeze()
        if pts.ndim != 2:
            continue
        blob = _to_polygon(pts.tolist())
        if blob is None:
            continue

        matched = False
        for defect_shape in defect_shapes:
            if defect_shape is None:
                continue
            try:
                inter = float(blob.intersection(defect_shape).area)
                union = blob.area + defect_shape.area - inter
                iou = inter / union if union > 0 else 0.0
            except Exception:
                iou = 0.0
            if iou >= RESCUE_OVERLAP_THRESHOLD:
                matched = True
                break
        if matched:
            continue

        best_iod = 0.0
        best_label = None
        for label, panel_shape in panel_shapes:
            try:
                iod = float(blob.intersection(panel_shape).area / blob.area)
            except Exception:
                iod = 0.0
            if iod > best_iod:
                best_iod = iod
                best_label = label

        if best_iod < iod_threshold or best_label is None:
            continue
        panel_id = LABEL_TO_PANEL_ID.get(best_label, "Unknown")
        if panel_id in TIRE_PANEL_IDS:
            continue

        x1, y1, w_box, h_box = cv2.boundingRect(contour)
        anomalies.append(
            UnclassifiedAnomaly(
                id=f"{inspection_id}_UA_{len(anomalies):03d}",
                confidence=0.85,
                bbox=[
                    float(x1) / img_w,
                    float(y1) / img_h,
                    float(x1 + w_box) / img_w,
                    float(y1 + h_box) / img_h,
                ],
                polygon=[[float(p[0]) / img_w, float(p[1]) / img_h] for p in pts],
                panel=panel_id,
                reason="stage1_rescue",
            )
        )

    logger.info("Stage 4: Rescued %d unclassified anomalies", len(anomalies))
    return anomalies
