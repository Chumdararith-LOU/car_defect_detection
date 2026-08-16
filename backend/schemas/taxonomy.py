"""Pydantic schemas for the taxonomy entity (Stage 2 Training Platform, Phase A)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

StageLiteral = Literal["stage1", "stage2", "stage3"]


class TaxonomyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    stage: StageLiteral
    class_names: list[str] = Field(..., min_length=1)
    description: Optional[str] = None


class TaxonomyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    class_names: Optional[list[str]] = Field(None, min_length=1)
    description: Optional[str] = None


class Taxonomy(BaseModel):
    id: str
    name: str
    stage: str
    class_names: list[str]
    description: Optional[str] = None
    created_at: str
    updated_at: str


class TaxonomyListResponse(BaseModel):
    taxonomies: list[Taxonomy]
    total: int
