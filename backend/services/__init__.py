import logging
from datetime import datetime, timezone

import cv2
import numpy as np

from core.model_manager import model_manager
from core.system_metrics import resolve_device
from schemas.inspection import Defect, InspectionPayload

from .image_utils import process_uploaded_image
from .stage1 import run_prescreen
from .stage2_direct import run_direct_inference
from .stage2_sahi import run_sahi_inference

logger = logging.getLogger("Orchestrator")

__all__ = ["process_uploaded_image", "run_inspection"]


def run_inspection(
    img_np: np.ndarray,
    stage1_model=None,
    stage2_model=None,
    stage2_model_name: str | None = None,
    stage2_model_path: str | None = None,
    stage2_mode: str = "direct",
    stage2_preset: str = "balanced",
    stage2_conf: float = 0.25,
    device: str = "auto",
    model=None,
    **kwargs,
) -> InspectionPayload:
    stage1_model = stage1_model or model
    resolved_device = resolve_device(device)
    logger.info("Resolved compute device: %s", resolved_device)
    inspection_id = f"INSP_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.now(timezone.utc).isoformat()

    if stage1_model is None or img_np is None:
        return _build_pass_payload(inspection_id, timestamp, 1600, 900, 0.0, 0.0)

    img_h, img_w = img_np.shape[:2]

    # --- STAGE 1: PRE-SCREEN ---
    s1_result = run_prescreen(img_np, stage1_model, resolved_device)

    if s1_result.get("error"):
        return _build_pass_payload(
            inspection_id, timestamp, img_w, img_h, 0.0, s1_result["latency_ms"]
        )

    if not s1_result["is_active"]:
        return _build_pass_payload(
            inspection_id,
            timestamp,
            img_w,
            img_h,
            s1_result["saliency_score"],
            s1_result["latency_ms"],
        )

    # --- STAGE 2: DEFECT LOCALIZATION ---
    defects = []

    if stage2_model_name and stage2_model_path:
        logger.info(
            "Stage 2 | Mode: %s | Routing to Defect Localization...", stage2_mode
        )

        if stage2_mode == "sahi":
            try:
                defects = run_sahi_inference(
                    img_np,
                    stage2_model_path,
                    inspection_id,
                    stage2_preset,
                    resolved_device,
                )
            except Exception as e:
                logger.warning("SAHI inference failed: %s. Falling back to direct.", e)
                stage2_mode = "direct"

        if stage2_mode == "direct":
            # We need the loaded model object for direct inference
            s2_model_obj = model_manager.get_model(stage2_model_name, stage="stage2")
            if s2_model_obj:
                defects = run_direct_inference(
                    img_np, s2_model_obj, inspection_id, stage2_conf, resolved_device
                )

    # Fallback synthetic anomaly blob derived from the Stage 1 saliency mask
    if s1_result["binary_mask"] is not None:
        binary_mask = s1_result["binary_mask"]
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x1, y1, w_box, h_box = cv2.boundingRect(largest_contour)
            x2, y2 = x1 + w_box, y1 + h_box
            pixel_area = float(cv2.contourArea(largest_contour))
            pts = largest_contour.squeeze()

            norm_polygon = (
                [(float(pt[0]) / img_w, float(pt[1]) / img_h) for pt in pts]
                if len(pts.shape) == 2
                else []
            )
            norm_bbox = (
                float(x1) / img_w,
                float(y1) / img_h,
                float(x2) / img_w,
                float(y2) / img_h,
            )

            # Confidence approximation for the anomaly blob
            confidence = 0.85

            defects.append(
                Defect(
                    defect_id=f"{inspection_id}_DEF_000",
                    defect_class="anomaly",
                    confidence=confidence,
                    global_bbox_xyxy=norm_bbox,
                    polygon=norm_polygon,
                    assigned_panel="Unknown",
                    containment_ratio_iod=0.95,
                    damage_severity_index_dsi=min(0.99, pixel_area / 5000),
                )
            )

    inspection_status = "FAIL" if len(defects) > 0 else "PASS"

    pydantic_defects = [d if isinstance(d, Defect) else Defect(**d) for d in defects]

    return InspectionPayload(
        inspection_id=inspection_id,
        timestamp=timestamp,
        vehicle_color_detected="Unknown",
        total_defects_found=len(defects),
        inspection_status=inspection_status,
        defects=pydantic_defects,
        imageDims={"width": img_w, "height": img_h},
        preScreen={
            "anomalyDetected": s1_result["is_active"],
            "score": s1_result["saliency_score"],
            "latencyMs": s1_result["latency_ms"],
        },
        panels=[],
    )


def _build_pass_payload(inspection_id, timestamp, w, h, score, latency):
    return InspectionPayload(
        inspection_id=inspection_id,
        timestamp=timestamp,
        vehicle_color_detected="Unknown",
        total_defects_found=0,
        inspection_status="PASS",
        defects=[],
        imageDims={"width": w, "height": h},
        preScreen={"anomalyDetected": False, "score": score, "latencyMs": latency},
        panels=[],
    )
