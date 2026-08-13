import logging

from shapely.geometry import Polygon

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
        field_name = _PYDANTIC_FIELD_MAP.get(key, key)
        setattr(defect, field_name, value)


def assign_defects_to_panels(defects, panels, iod_threshold=0.1) -> list:
    """Assigns each defect to the panel with the highest IoD."""
    panel_shapes = []
    for panel in panels:
        shape = _to_polygon(panel.get("polygon", []))
        if shape is not None:
            panel_shapes.append((panel.get("label"), shape))

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
            _set_field(
                defect, "assigned_panel", LABEL_TO_PANEL_ID.get(best_label, "Unknown")
            )
            assigned_count += 1
        else:
            _set_field(defect, "assigned_panel", "Unknown")
        _set_field(defect, "containment_ratio_iod", best_iod)

    logger.info(
        "Stage 4: Assigned %d/%d defects to panels (threshold=%.2f)",
        assigned_count,
        len(defects),
        iod_threshold,
    )
    return defects
