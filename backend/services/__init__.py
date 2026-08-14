import logging
from datetime import datetime, timezone

import numpy as np

from core.model_manager import model_manager
from core.system_metrics import resolve_device
from schemas.inspection import Defect, InspectionPayload, Panel

from .image_utils import process_uploaded_image
from .stage1 import run_prescreen
from .stage2_direct import run_direct_inference
from .stage2_sahi import run_sahi_inference
from .stage3 import run_panel_inference
from .stage4 import (
    assign_defects_to_panels,
    extract_stage1_blobs,
    rescue_unclassified_anomalies,
)

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
    stage2_conf: float = 0.15,
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

    # --- STAGE 3: PANEL SEGMENTATION ---
    panels = []
    stage3_model = model_manager.get_model(stage="stage3")
    if stage3_model is not None:
        logger.info("Stage 3 | Routing to Panel Segmentation...")
        try:
            panels = run_panel_inference(stage3_model, img_np, resolved_device)
        except Exception as e:
            logger.warning("Stage 3 panel inference failed: %s", e)
            panels = []
    else:
        logger.warning("Stage 3 model not available, skipping panel segmentation")

    # --- STAGE 4: IoD FUSION ---
    suppressed_detections = []
    if panels and defects:
        logger.info("Stage 4 | Routing to IoD Fusion...")
        defects, suppressed_detections = assign_defects_to_panels(defects, panels)

    unclassified_anomalies, suppressed_blobs = rescue_unclassified_anomalies(
        s1_result["binary_mask"], defects, panels, inspection_id
    )
    suppressed_detections.extend(suppressed_blobs)
    stage1_blobs = extract_stage1_blobs(
        s1_result["binary_mask"], inspection_id, panels=panels
    )

    inspection_status = "FAIL" if len(defects) > 0 else "PASS"

    pydantic_defects = [d if isinstance(d, Defect) else Defect(**d) for d in defects]

    payload_panels = [
        Panel(
            id=f"panel_{p['id']}",
            label=p["label"],
            polygon=[(float(pt[0]), float(pt[1])) for pt in p.get("polygon", [])],
        )
        for p in panels
    ]

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
        panels=payload_panels,
        unclassified_anomalies=unclassified_anomalies,
        suppressed_detections=suppressed_detections,
        stage1_blobs=stage1_blobs,
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
