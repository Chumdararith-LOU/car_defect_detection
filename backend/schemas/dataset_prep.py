"""Pydantic schemas for Dataset Preparation (split detection, re-split, tiling)."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SplitLayout(str, Enum):
    """Detected physical layout of a dataset directory."""

    ULTRALYTICS = "ultralytics"  # images/<split>/ + labels/<split>/
    GROUPED = "grouped"  # <split>/images/ + <split>/labels/
    UNSPLIT = "unsplit"  # images/ + labels/ (single pool)
    FLAT = "flat"  # image + label files loose in root
    UNKNOWN = "unknown"


class DetectedSplit(BaseModel):
    name: str  # "train" | "val" | "test" | "all"
    image_count: int
    label_count: int
    images_path: str
    labels_path: Optional[str] = None


class SplitStructure(BaseModel):
    dataset_id: str
    layout: SplitLayout
    has_data_yaml: bool
    splits: list[DetectedSplit]
    total_images: int
    total_labels: int
    is_split: bool  # True if train/val(/test) already present
    has_test: bool
    warnings: list[str] = Field(default_factory=list)


class ImportDatasetResponse(BaseModel):
    success: bool
    dataset_id: str
    path: str
    structure: SplitStructure
    message: str
