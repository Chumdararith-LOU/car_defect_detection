import logging

import cv2
import numpy as np
from shapely.geometry import Polygon, box as shapely_box
from shapely.ops import unary_union

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

TIRE_LABEL_KEYWORDS = ("wheel", "tire")
TIRE_IOS_THRESHOLD = 0.50
CAR_CONTEXT_IOD_THRESHOLD = 0.20
CONTAINMENT_THRESHOLD = 0.50
RESCUE_OVERLAP_THRESHOLD = 0.30
RESCUE_MIN_AREA_RATIO = 0.0005
CAR_CONTEXT_CLOSE_DISTANCE = 0.02
MIN_CAR_CONTEXT_AREA = 0.05


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
    "damage_severity_index_dsi": "dsi",
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


def build_car_context(panel_polygons):
    """Fuses Stage 3 panel polygons into a single car context mask.

    Returns (car_context, tire_mask). A morphological close (buffer out/in)
    fills gaps between panels so on-car parts between panels count as car.
    """
    all_polys = [p for _, p in panel_polygons if p.is_valid and p.area > 0]
    if not all_polys:
        return None, None
    union = unary_union(all_polys)
    d = CAR_CONTEXT_CLOSE_DISTANCE
    car_context = union.buffer(d).buffer(-d)
    if car_context.is_empty or car_context.area <= 0:
        car_context = None
    tire_polys = [
        p
        for label, p in panel_polygons
        if label and any(kw in label.lower() for kw in TIRE_LABEL_KEYWORDS)
    ]
    tire_mask = unary_union(tire_polys) if tire_polys else None
    return car_context, tire_mask


def assign_defects_to_panels(defects, panels, iod_threshold=0.1):
    """Assigns each defect to the panel with the highest IoD.

    Returns (kept_defects, suppressed_detections). Suppression uses tire
    overlap and car-context containment; a defect is never suppressed just
    because its best panel IoD is low (panel becomes "Unknown" instead).
    """
    panel_shapes = []
    for panel in panels:
        shape = _to_polygon(panel.get("polygon", []))
        if shape is not None:
            panel_shapes.append((panel.get("label"), shape))

    car_context, tire_mask = build_car_context(panel_shapes)
    low_context = car_context is None or car_context.area < MIN_CAR_CONTEXT_AREA

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

        if not low_context and defect_shape is not None and car_context is not None:
            tire_iod = 0.0
            if tire_mask is not None:
                try:
                    tire_iod = float(
                        defect_shape.intersection(tire_mask).area / defect_shape.area
                    )
                except Exception:
                    tire_iod = 0.0

            if tire_iod >= TIRE_IOS_THRESHOLD:
                suppressed.append(
                    _to_suppressed(
                        defect,
                        (
                            LABEL_TO_PANEL_ID.get(best_label, "Unknown")
                            if best_label
                            else "Unknown"
                        ),
                        "tire",
                    )
                )
                continue

            bbox = _get_field(defect, "bbox") or _get_field(defect, "global_bbox_xyxy")
            car_iod = 0.0
            if bbox and len(bbox) == 4:
                try:
                    bbox_shape = shapely_box(
                        float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                    )
                    car_iod = float(
                        bbox_shape.intersection(car_context).area / bbox_shape.area
                    )
                except Exception:
                    car_iod = 0.0
            else:
                try:
                    car_iod = float(
                        defect_shape.intersection(car_context).area / defect_shape.area
                    )
                except Exception:
                    car_iod = 0.0

            if car_iod < CAR_CONTEXT_IOD_THRESHOLD:
                suppressed.append(_to_suppressed(defect, "Unknown", "non_car_context"))
                continue

        if best_iod >= CONTAINMENT_THRESHOLD and best_label is not None:
            panel_id = LABEL_TO_PANEL_ID.get(best_label, "Unknown")
        else:
            panel_id = "Unknown"

        _set_field(defect, "assigned_panel", panel_id)
        _set_field(defect, "containment_ratio_iod", best_iod)
        if panel_id == "Unknown":
            _set_field(defect, "damage_severity_index_dsi", 0.0)
        else:
            assigned_count += 1
        kept.append(defect)

    logger.info(
        "Stage 4: Kept %d/%d defects (assigned %d, suppressed %d, low_context=%s)",
        len(kept),
        len(defects),
        assigned_count,
        len(suppressed),
        low_context,
    )
    return kept, suppressed


def rescue_unclassified_anomalies(binary_mask, defects, panels, inspection_id):
    """Routes Stage 1 saliency blobs to unclassified_anomalies or suppressed.

    Returns (anomalies, suppressed_blobs). Blobs are never added to defects.
    """
    anomalies = []
    suppressed_blobs = []
    if binary_mask is None:
        return anomalies, suppressed_blobs

    mask = np.ascontiguousarray(binary_mask.astype(np.uint8))
    img_h, img_w = mask.shape[:2]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return anomalies, suppressed_blobs

    panel_shapes = []
    for panel in panels:
        shape = _to_polygon(panel.get("polygon", []))
        if shape is not None:
            panel_shapes.append((panel.get("label"), shape))

    car_context, tire_mask = build_car_context(panel_shapes)
    if car_context is None or car_context.area < MIN_CAR_CONTEXT_AREA:
        return anomalies, suppressed_blobs

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
                smaller = min(blob.area, defect_shape.area)
                ios = inter / smaller if smaller > 0 else 0.0
            except Exception:
                ios = 0.0
            if ios >= RESCUE_OVERLAP_THRESHOLD:
                matched = True
                break
        if matched:
            continue

        x1, y1, w_box, h_box = cv2.boundingRect(contour)
        norm_bbox = [
            float(x1) / img_w,
            float(y1) / img_h,
            float(x1 + w_box) / img_w,
            float(y1 + h_box) / img_h,
        ]
        norm_polygon = [[float(p[0]) / img_w, float(p[1]) / img_h] for p in pts]
        blob_id = f"{inspection_id}_UA_{len(anomalies) + len(suppressed_blobs):03d}"

        tire_ratio = 0.0
        if tire_mask is not None:
            try:
                tire_ratio = float(blob.intersection(tire_mask).area / blob.area)
            except Exception:
                tire_ratio = 0.0
        if tire_ratio >= TIRE_IOS_THRESHOLD:
            suppressed_blobs.append(
                SuppressedDetection(
                    id=blob_id,
                    predicted_class="anomaly",
                    confidence=0.85,
                    bbox=norm_bbox,
                    polygon=norm_polygon,
                    panel="Unknown",
                    reason="tire",
                )
            )
            continue

        car_ratio = 0.0
        try:
            car_ratio = float(blob.intersection(car_context).area / blob.area)
        except Exception:
            car_ratio = 0.0
        if car_ratio >= CAR_CONTEXT_IOD_THRESHOLD:
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
            panel_id = (
                LABEL_TO_PANEL_ID.get(best_label, "Unknown")
                if best_iod >= CONTAINMENT_THRESHOLD and best_label
                else "Unknown"
            )
            anomalies.append(
                UnclassifiedAnomaly(
                    id=blob_id,
                    confidence=0.85,
                    bbox=norm_bbox,
                    polygon=norm_polygon,
                    panel=panel_id,
                    reason="stage1_rescue",
                )
            )
        else:
            suppressed_blobs.append(
                SuppressedDetection(
                    id=blob_id,
                    predicted_class="anomaly",
                    confidence=0.85,
                    bbox=norm_bbox,
                    polygon=norm_polygon,
                    panel="Unknown",
                    reason="non_car_context",
                )
            )

    logger.info(
        "Stage 4: Rescued %d anomalies, suppressed %d blobs",
        len(anomalies),
        len(suppressed_blobs),
    )
    return anomalies, suppressed_blobs
