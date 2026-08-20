import cv2
import numpy as np
import logging

logger = logging.getLogger("Stage2Direct")

DIRECT_MASK_IOS_THRESHOLD = 0.50


def _boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _polygon_to_bool_mask(polygon_px, img_w, img_h):
    m = np.zeros((img_h, img_w), dtype=np.uint8)
    if len(polygon_px) > 2:
        pts = np.array(polygon_px, dtype=np.float32).astype(np.int32).reshape(-1, 1, 2)
        cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def run_direct_inference(
    img_np: np.ndarray,
    model,
    inspection_id: str,
    conf_threshold: float = 0.25,
    device: str = "cpu",
) -> list:
    """Runs standard Ultralytics YOLO inference at 1024px."""
    results = model(
        img_np, imgsz=1024, conf=conf_threshold, device=device, verbose=False
    )
    res = results[0]

    img_h, img_w = img_np.shape[:2]
    defects = []

    if res.masks is not None and res.boxes is not None:
        boxes = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy().astype(int)
        masks_xy = res.masks.xy

        bool_masks = [
            _polygon_to_bool_mask(masks_xy[j], img_w, img_h) for j in range(len(boxes))
        ]
        areas = [int(m.sum()) for m in bool_masks]
        order = sorted(range(len(boxes)), key=lambda j: -confs[j])
        kept_idx = []
        for j in order:
            is_duplicate = False
            for k in kept_idx:
                if classes[j] != classes[k]:
                    continue
                if not _boxes_overlap(boxes[j], boxes[k]):
                    continue
                inter = int(np.logical_and(bool_masks[j], bool_masks[k]).sum())
                smaller = min(areas[j], areas[k])
                ios = inter / smaller if smaller > 0 else 0.0
                if ios >= DIRECT_MASK_IOS_THRESHOLD:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept_idx.append(j)
        kept_idx.sort()
        logger.info(
            "Stage 2 Direct: kept %d/%d detections after Mask-IOS NMS",
            len(kept_idx),
            len(boxes),
        )

        for seq, i in enumerate(kept_idx):
            conf = float(confs[i])
            cls_id = classes[i]
            cls_name = model.names[cls_id]

            x1, y1, x2, y2 = boxes[i]
            norm_bbox = (
                float(x1) / img_w,
                float(y1) / img_h,
                float(x2) / img_w,
                float(y2) / img_h,
            )

            poly = masks_xy[i]
            norm_polygon = (
                [(float(pt[0]) / img_w, float(pt[1]) / img_h) for pt in poly]
                if len(poly) > 0
                else []
            )

            # Calculate pixel area for DSI
            pixel_area = (
                float(cv2.contourArea(poly.astype(np.int32))) if len(poly) > 0 else 0.0
            )

            defects.append(
                {
                    "defect_id": f"{inspection_id}_S2_{seq:03d}",
                    "defect_class": cls_name,
                    "confidence": conf,
                    "global_bbox_xyxy": norm_bbox,
                    "polygon": norm_polygon,
                    "assigned_panel": "Unknown",
                    "containment_ratio_iod": 0.0,
                    "damage_severity_index_dsi": min(0.99, pixel_area / 5000.0),
                }
            )

    return defects
