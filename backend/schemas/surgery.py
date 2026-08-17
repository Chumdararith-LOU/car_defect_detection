"""Pydantic schemas for head surgery (Stage 2 Training Platform, Phase C)."""

from typing import Literal, Optional

from pydantic import BaseModel

HeadInitMode = Literal["fresh", "class_aware"]


class SurgeryRequest(BaseModel):
    source_checkpoint_id: str
    taxonomy_id: str
    head_init_mode: HeadInitMode = "fresh"


class SurgeryStartResponse(BaseModel):
    job_id: str
    status: str


class SurgeryStatusResponse(BaseModel):
    job_id: str
    status: str
    error_message: Optional[str] = None
    output_checkpoint_id: Optional[str] = None
