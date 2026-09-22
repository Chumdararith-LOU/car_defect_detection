"""Pipeline specification schemas for configurable stage execution.

These models express the operator's request for which stages to run and how
Stage 2 should combine models, enabling arbitrary model combinations or a
single individual model.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StageConfig(BaseModel):
    """Configuration for a single pipeline stage.

    ``models``, ``merge``, and ``class_routing`` apply to Stage 2 only and are
    ignored for other stages. Omitting them falls back to the preset's routing.
    """

    enabled: bool = True
    models: Optional[List[str]] = Field(
        None, description="Stage 2 only: model names to run (overrides preset)."
    )
    merge: Optional[str] = Field(
        None, description="Stage 2 only: 'none' | 'union' | 'per_class'."
    )
    class_routing: Optional[Dict[str, str]] = Field(
        None, description="Stage 2 only: map of class -> model name."
    )


class PipelineSpec(BaseModel):
    """Full pipeline execution specification."""

    preset: str = Field("safety", description="Operating preset name.")
    stage1: StageConfig = Field(default_factory=lambda: StageConfig(enabled=True))
    stage2: StageConfig = Field(default_factory=lambda: StageConfig(enabled=True))
    stage3: StageConfig = Field(default_factory=lambda: StageConfig(enabled=True))
    stage4: StageConfig = Field(default_factory=lambda: StageConfig(enabled=True))
    return_crops: bool = True
    device: str = "auto"
