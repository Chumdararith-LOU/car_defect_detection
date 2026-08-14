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


class ResplitRequest(BaseModel):
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    seed: int = 42


class ResplitResponse(BaseModel):
    success: bool
    dataset_id: str
    new_structure: SplitStructure
    message: str


class TileRequest(BaseModel):
    new_dataset_id: str
    tile_size: int = Field(
        default=1024, ge=0, description="0 triggers adaptive 2x2 halving"
    )
    overlap: float = Field(default=0.15, ge=0.0, le=0.9)
    min_area_ratio: float = Field(default=0.01, ge=0.0, le=1.0)


class TileResponse(BaseModel):
    success: bool
    original_dataset_id: str
    new_dataset_id: str
    tiles_generated: int
    message: str
