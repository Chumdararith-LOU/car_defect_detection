"""Pydantic schemas for the Dataset Management module (Phase 9)."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DatasetStage(str, Enum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"


class DatasetStatus(str, Enum):
    RAW = "raw"
    CURATED = "curated"
    RELEASED = "released"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class SplitInfo(BaseModel):
    """Metadata about one dataset split (train / val / test)."""

    name: str
    image_count: int
    path: str


class ClassDistributionItem(BaseModel):
    """Instance count for a single class."""

    class_id: int
    class_name: str
    instance_count: int
    percentage: float


# ---------------------------------------------------------------------------
# List view (lightweight)
# ---------------------------------------------------------------------------


class DatasetSummary(BaseModel):
    """One row in the dataset list."""

    dataset_id: str
    name: str
    stage: DatasetStage
    yaml_path: str
    nc: int
    class_names: list[str]
    splits: list[SplitInfo]
    total_images: int
    is_champion: bool
    status: DatasetStatus


class DatasetListResponse(BaseModel):
    datasets: list[DatasetSummary]


# ---------------------------------------------------------------------------
# Detail view (heavier, computed on demand)
# ---------------------------------------------------------------------------


class DatasetDetail(BaseModel):
    """Full dataset info including class distribution."""

    dataset_id: str
    name: str
    stage: DatasetStage
    yaml_path: str
    root_path: str
    nc: int
    class_names: list[str]
    splits: list[SplitInfo]
    total_images: int
    is_champion: bool
    status: DatasetStatus
    class_distribution: list[ClassDistributionItem]


# ---------------------------------------------------------------------------
# Leakage audit
# ---------------------------------------------------------------------------


class FilenameOverlap(BaseModel):
    filename: str
    found_in: list[str]  # e.g. ["train", "test"]


class LeakageAuditResult(BaseModel):
    dataset_id: str
    passed: bool
    total_checked: int
    filename_overlaps: list[FilenameOverlap]
    issues: list[str]


# ---------------------------------------------------------------------------
# Build from reviewed feedback
# ---------------------------------------------------------------------------


class DatasetBuildRequest(BaseModel):
    """Request to create a new dataset version from reviewed flywheel items."""

    stage: DatasetStage
    version_name: str
    include_confirmed: bool = True
    include_rejected: bool = False
    include_unclear: bool = False
    notes: Optional[str] = None


class DatasetBuildResponse(BaseModel):
    dataset_id: str
    version_name: str
    status: DatasetStatus
    message: str
