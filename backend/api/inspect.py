import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from core.model_manager import model_manager
from services import process_uploaded_image, run_inspection

logger = logging.getLogger("InspectAPI")

router = APIRouter(prefix="/api", tags=["inspect"])


@router.post("/inspect", status_code=status.HTTP_200_OK)
async def inspect_vehicle(
    file: UploadFile = File(...),
    model_name: str = Form(None),
    stage2_model_name: str = Form(None),
    stage2_mode: str = Form("direct"),
    stage2_preset: str = Form("balanced"),
    stage2_conf: float = Form(0.25),
    device: str = Form("auto"),
):
    stage1_model = model_manager.get_model(model_name, stage="stage1")

    if stage1_model is None:
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
        }

    try:
        contents = await file.read()
        img_np = process_uploaded_image(contents)

        stage2_model_path = None
        if stage2_model_name:
            stage2_model_path = model_manager.get_model_path(
                stage2_model_name, stage="stage2"
            )

        response_data = run_inspection(
            img_np,
            stage1_model=stage1_model,
            stage2_model_name=stage2_model_name,
            stage2_model_path=stage2_model_path,
            stage2_mode=stage2_mode,
            stage2_preset=stage2_preset,
            stage2_conf=stage2_conf,
            device=device,
        )
        return response_data

    except Exception as e:
        logger.exception("An error occurred during inspection")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during inspection: {str(e)}",
        )
