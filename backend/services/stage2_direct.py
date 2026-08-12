import cv2
import numpy as np


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

        for i in range(len(boxes)):
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
                    "defect_id": f"{inspection_id}_S2_{i:03d}",
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
