"""REST API for head surgery (Stage 2 Training Platform, Phase C)."""

import logging

from fastapi import APIRouter, HTTPException

from schemas.surgery import (
    SurgeryRequest,
    SurgeryStartResponse,
    SurgeryStatusResponse,
)
from services import surgery_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/surgery", tags=["surgery"])


@router.post("", response_model=SurgeryStartResponse, status_code=202)
def start_surgery(payload: SurgeryRequest) -> SurgeryStartResponse:
    try:
        job_id = surgery_service.start_surgery(
            source_checkpoint_id=payload.source_checkpoint_id,
            taxonomy_id=payload.taxonomy_id,
            head_init_mode=payload.head_init_mode,
        )
    except (LookupError, KeyError) as exc:
        raise HTTPException(
            status_code=404, detail="source checkpoint or taxonomy not found"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SurgeryStartResponse(job_id=job_id, status="queued")


@router.get("/{job_id}", response_model=SurgeryStatusResponse)
def surgery_status(job_id: str) -> SurgeryStatusResponse:
    try:
        return surgery_service.get_status(job_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="surgery job not found") from exc
