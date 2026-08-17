"""REST API for the checkpoint registry (Stage 2 Training Platform, Phase A)."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.checkpoint import (
    Checkpoint,
    CheckpointListResponse,
    CheckpointRegister,
    ScanResponse,
)
from services import checkpoint_registry
from services.checkpoint_registry import (
    CheckpointInUseError,
    CheckpointNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


@router.get("", response_model=CheckpointListResponse)
def list_checkpoints(stage: Optional[str] = Query(None)) -> CheckpointListResponse:
    items = checkpoint_registry.list_checkpoints(stage=stage)
    return CheckpointListResponse(checkpoints=items, total=len(items))


@router.post("/scan", response_model=ScanResponse)
def scan() -> ScanResponse:
    return ScanResponse(**checkpoint_registry.scan_filesystem())


@router.post("/register", response_model=Checkpoint, status_code=201)
def register(payload: CheckpointRegister) -> Checkpoint:
    return checkpoint_registry.register_checkpoint(
        name=payload.name,
        path=payload.path,
        origin=payload.origin,
        stage=payload.stage,
        nc=payload.nc,
        class_names=payload.class_names,
        architecture=payload.architecture,
        source_checkpoint_id=payload.source_checkpoint_id,
        notes=payload.notes,
    )


@router.get("/{checkpoint_id}", response_model=Checkpoint)
def get_checkpoint(checkpoint_id: str) -> Checkpoint:
    try:
        return checkpoint_registry.get_checkpoint(checkpoint_id)
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail="checkpoint not found") from exc


@router.delete("/{checkpoint_id}", status_code=204)
def delete_checkpoint(checkpoint_id: str) -> None:
    try:
        checkpoint_registry.delete_checkpoint(checkpoint_id)
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail="checkpoint not found") from exc
    except CheckpointInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
