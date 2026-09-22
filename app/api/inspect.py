"""Sync single-image inspection endpoint."""
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.core.image import ImageDecodeError, decode_image
from app.pipeline.orchestrator import run_pipeline
from app.schemas.pipeline import PipelineSpec

logger = logging.getLogger("api.inspect")

router = APIRouter(prefix=settings.api_v1_str, tags=["inspect"])


@router.post("/inspect")
async def inspect(
    file: UploadFile = File(...),
    preset: str = Form("safety"),
    spec: Optional[str] = Form(None),
    return_crops: bool = Form(True),
    device: str = Form("auto"),
):
    """Run the full inspection pipeline on one uploaded image (synchronous).

    The caller may pass a simple ``preset`` (with all stages enabled) or a full
    ``spec`` JSON string encoding a ``PipelineSpec`` for stage toggles and
    Stage-2 model combinations.
    """
    contents = await file.read()
    try:
        img_np = decode_image(contents)
    except ImageDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {e}",
        )

    try:
        if spec:
            pipeline_spec = PipelineSpec(**json.loads(spec))
        else:
            pipeline_spec = PipelineSpec(
                preset=preset, return_crops=return_crops, device=device
            )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid pipeline spec: {e}",
        )

    t0 = time.time()
    try:
        payload = run_pipeline(img_np, pipeline_spec)
    except Exception as e:  # noqa: BLE001
        logger.exception("Inspection failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inspection failed: {e}",
        )
    inference_ms = round((time.time() - t0) * 1000, 2)

    # Serialize with frontend-facing aliases (id/class/bbox/panel/iod/dsi).
    result = payload.model_dump(by_alias=True)
    result["inference_ms"] = inference_ms
    return result
