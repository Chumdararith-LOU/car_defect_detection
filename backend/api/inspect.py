import logging
import time

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from core.model_manager import model_manager
from services import process_uploaded_image, run_inspection
from services.inspection_store import save_inspection

logger = logging.getLogger("InspectAPI")
router = APIRouter(prefix="/api", tags=["inspect"])


def _resolve_device(requested: str) -> str:
    """Resolve 'auto' to the actual device that will be used."""
    if requested and requested != "auto":
        return requested
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


@router.post("/inspect", status_code=status.HTTP_200_OK)
async def inspect_vehicle(
    file: UploadFile = File(...),
    model_name: str = Form(None),
    stage2_model_name: str = Form(None),
    stage2_mode: str = Form("direct"),
    stage2_preset: str = Form("balanced"),
    stage2_conf: float = Form(0.15),
    device: str = Form("auto"),
    enable_stage1: bool = Form(True),
    enable_stage2: bool = Form(True),
    enable_stage3: bool = Form(True),
):
    if not (enable_stage1 or enable_stage2 or enable_stage3):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="at least one stage must be enabled",
        )

    disabled_stages = [
        stage
        for stage, enabled in (
            ("stage1", enable_stage1),
            ("stage2", enable_stage2),
            ("stage3", enable_stage3),
        )
        if not enabled
    ]

    stage1_model = (
        model_manager.get_model(model_name, stage="stage1") if enable_stage1 else None
    )

    if enable_stage1 and stage1_model is None:
        logger.warning(
            "Stage 1 Model not found or not loaded. Returning MOCK PASS payload."
        )
        return {
            "inspection_id": "MOCK_INSP_001",
            "timestamp": "2026-08-01T00:00:00Z",
            "vehicle_color_detected": "Unknown",
            "total_defects_found": 0,
            "inspection_status": "PASS",
            "defects": [],
            "unclassified_anomalies": [],
            "suppressed_detections": [],
            "disabled_stages": disabled_stages,
        }

    try:
        contents = await file.read()
        img_np = process_uploaded_image(contents)

        if not stage2_model_name:
            available_s2 = model_manager.list_available_models(stage="stage2")
            if available_s2:
                stage2_model_name = available_s2[0]
                logger.info(f"Auto-resolved Stage 2 model: {stage2_model_name}")

        stage2_model_path = None
        if stage2_model_name:
            stage2_model_path = model_manager.get_model_path(
                stage2_model_name, stage="stage2"
            )

        t0 = time.time()
        response_data = run_inspection(
            img_np,
            stage1_model=stage1_model,
            stage2_model_name=stage2_model_name,
            stage2_model_path=stage2_model_path,
            stage2_mode=stage2_mode,
            stage2_preset=stage2_preset,
            stage2_conf=stage2_conf,
            device=device,
            enable_stage1=enable_stage1,
            enable_stage2=enable_stage2,
            enable_stage3=enable_stage3,
        )

        inference_ms = round((time.time() - t0) * 1000, 2)
        resolved_device = _resolve_device(device)
        inspection_id = getattr(response_data, "inspection_id", "")
        if hasattr(response_data, "model_dump"):
            payload_dict = response_data.model_dump(by_alias=True)
        elif hasattr(response_data, "dict"):
            payload_dict = response_data.dict(by_alias=True)
        else:
            payload_dict = dict(response_data)
        # Inject performance stats so the LIVE UI receives them too
        payload_dict["inference_ms"] = inference_ms
        payload_dict["device_used"] = resolved_device
        if inspection_id:
            try:
                save_inspection(
                    inspection_id=inspection_id,
                    image_bytes=contents,
                    image_filename=file.filename or "upload.jpg",
                    payload=payload_dict,
                )
            except Exception as save_err:
                logger.warning(
                    f"Failed to persist inspection {inspection_id}: {save_err}"
                )
        return payload_dict

    except Exception as e:
        logger.exception("An error occurred during inspection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during inspection: {str(e)}",
        )
