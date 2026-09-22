"""Defect close-up crop extraction and storage.

Extracts a padded crop around each detected defect's bounding box, saves it to
the crops storage directory, and returns a URL the API can serve via
``GET /v1/crops/{filename}``.
"""
import logging

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger("crops")

# Fraction of the bbox dimension added as padding on each side.
CROP_PADDING_RATIO = 0.15


def extract_crop(
    img_np: np.ndarray,
    bbox_xyxy: tuple,
    inspection_id: str,
    defect_index: int,
    padding_ratio: float = CROP_PADDING_RATIO,
):
    """Crop the region around a normalized bbox, save it, and return its URL.

    Args:
        img_np: RGB image as a numpy array.
        bbox_xyxy: normalized (x1, y1, x2, y2) in [0, 1].
        inspection_id: unique inspection id.
        defect_index: index of the defect within this inspection.
        padding_ratio: fraction of bbox size to pad on each side.

    Returns:
        The crop URL path (e.g. ``/v1/crops/INSP_..._000.png``), or None if the
        bbox is degenerate.
    """
    img_h, img_w = img_np.shape[:2]
    x1, y1, x2, y2 = bbox_xyxy

    # Normalized -> pixel coordinates.
    px1, py1 = int(x1 * img_w), int(y1 * img_h)
    px2, py2 = int(x2 * img_w), int(y2 * img_h)

    # Pad, clamped to image bounds.
    bw, bh = px2 - px1, py2 - py1
    pad_x, pad_y = int(bw * padding_ratio), int(bh * padding_ratio)
    px1 = max(0, px1 - pad_x)
    py1 = max(0, py1 - pad_y)
    px2 = min(img_w, px2 + pad_x)
    py2 = min(img_h, py2 + pad_y)

    if px2 <= px1 or py2 <= py1:
        return None

    crop = img_np[py1:py2, px1:px2]
    if crop.size == 0:
        return None

    settings.crops_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{inspection_id}_{defect_index:03d}.png"
    crop_path = settings.crops_dir / filename
    crop_bgr = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(crop_path), crop_bgr)

    return f"{settings.api_v1_str}/crops/{filename}"


def attach_crops(img_np, defects, inspection_id, padding_ratio=CROP_PADDING_RATIO):
    """Extract a crop for every defect and set its ``crop_url``. Returns defects."""
    for i, defect in enumerate(defects):
        bbox = defect.get("global_bbox_xyxy") or defect.get("bbox")
        if bbox and len(bbox) == 4:
            defect["crop_url"] = extract_crop(
                img_np, tuple(bbox), inspection_id, i, padding_ratio
            )
    return defects
