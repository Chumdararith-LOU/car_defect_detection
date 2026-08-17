"""Pydantic schemas for the dataset audit gate (Stage 2 Training Platform, Phase B)."""

from typing import Any, Optional

from pydantic import BaseModel


class ClassCount(BaseModel):
    class_id: int
    name: str
    instances: int
    share: float


class SizeBuckets(BaseModel):
    p10_area: float
    p60_area: float
    bottom_10_count: int
    middle_50_count: int
    top_40_count: int


class LabelIssues(BaseModel):
    missing_label_images: int
    empty_label_images: int
    unparseable_lines: int
    out_of_range_class_ids: int


class AuditReport(BaseModel):
    dataset_id: str
    stage: str
    computed_at: str
    totals: dict
    class_distribution: list[ClassCount]
    rare_classes: list[str]
    size_buckets: SizeBuckets
    label_issues: LabelIssues
    leakage: Optional[Any] = None
    cleared_for_training: bool
    blocking_reasons: list[str]
    warnings: list[str]
