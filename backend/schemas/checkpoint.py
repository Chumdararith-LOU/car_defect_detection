"""Pydantic schemas for the checkpoint entity (Stage 2 Training Platform, Phase A)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

CheckpointOrigin = Literal["native_coco", "trained", "surgery"]


class CheckpointRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    path: str
    origin: CheckpointOrigin = "trained"
    stage: str = "stage2"
    nc: int = 0
    class_names: Optional[list[str]] = None
    architecture: Optional[str] = None
    source_checkpoint_id: Optional[str] = None
    notes: Optional[str] = None


class Checkpoint(BaseModel):
    id: str
    name: str
    path: str
    origin: str
    source_checkpoint_id: Optional[str] = None
    source_job_id: Optional[str] = None
    stage: str
    nc: int
    class_names: Optional[list[str]] = None
    architecture: Optional[str] = None
    created_at: str
    notes: Optional[str] = None
    exists: bool = True
    size_mb: Optional[float] = None


class CheckpointListResponse(BaseModel):
    checkpoints: list[Checkpoint]
    total: int


class ScanResponse(BaseModel):
    registered: int
    skipped: int
