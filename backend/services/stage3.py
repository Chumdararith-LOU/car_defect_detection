import logging

import cv2
import numpy as np

logger = logging.getLogger("Stage3")

PANEL_CLASS_NAMES = {
    0: "Quarter-panel",
    1: "Front-wheel",
    2: "Back-window",
    3: "Trunk",
    4: "Front-door",
    5: "Rocker-panel",
    6: "Grille",
    7: "Windshield",
    8: "Front-window",
    9: "Back-door",
    10: "Headlight",
    11: "Back-wheel",
    12: "Back-windshield",
    13: "Hood",
    14: "Fender",
    15: "Tail-light",
    16: "License-plate",
    17: "Front-bumper",
    18: "Back-bumper",
    19: "Mirror",
    20: "Roof",
}

# Simplification tolerance as a fraction of the contour perimeter.
APPROX_EPSILON_RATIO = 0.002


def run_panel_inference(model, img_np, device, conf=0.25) -> list:
    """Runs Stage 3 panel segmentation at 640px (the training resolution)."""
    results = model(img_np, imgsz=640, conf=conf, device=device, verbose=False)
    res = results[0]

    img_h, img_w = img_np.shape[:2]
    panels = []

    if res.masks is not None and res.boxes is not None:
        confs = res.boxes.conf.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy().astype(int)
        masks_xy = res.masks.xy

        panel_id = 0
        for i in range(len(confs)):
            poly = masks_xy[i]
            if len(poly) < 3:
                continue

            cls_id = int(classes[i])
            label = PANEL_CLASS_NAMES.get(cls_id, model.names.get(cls_id, str(cls_id)))

            # Simplify in pixel space first so epsilon is scale-correct.
            contour = np.asarray(poly, dtype=np.float32).reshape(-1, 1, 2)
            epsilon = APPROX_EPSILON_RATIO * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
            if len(approx) < 3:
                continue

            norm_polygon = [
                [float(pt[0]) / img_w, float(pt[1]) / img_h] for pt in approx
            ]

            panels.append(
                {
                    "id": panel_id,
                    "label": label,
                    "class_index": cls_id,
                    "confidence": float(confs[i]),
                    "polygon": norm_polygon,
                }
            )
            panel_id += 1

    logger.info("Stage 3 | Detected %d panels at imgsz=640", len(panels))
    return panels
