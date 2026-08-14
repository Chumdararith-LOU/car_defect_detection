from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Tuple


class ImageDims(BaseModel):
    width: int
    height: int


class PreScreenResult(BaseModel):
    anomalyDetected: bool
    score: float
    latencyMs: float


class Panel(BaseModel):
    id: str
    label: str
    polygon: List[Tuple[float, float]]


class UnclassifiedAnomaly(BaseModel):
    id: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2] normalized 0-1
    polygon: Optional[List[List[float]]] = None
    panel: Optional[str] = "Unknown"
    reason: str = "stage1_rescue"


class SuppressedDetection(BaseModel):
    id: str
    predicted_class: str
    confidence: float
    bbox: List[float]
    polygon: Optional[List[List[float]]] = None
    panel: Optional[str] = "Unknown"
    reason: str


class Stage1Blob(BaseModel):
    """Raw Stage 1 saliency blob (always in payload for the S1 view)."""

    id: str
    bbox: List[float]  # [x1, y1, x2, y2] normalized 0-1
    polygon: Optional[List[List[float]]] = None
    area_ratio: float = 0.0


class Defect(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., alias="defect_id", serialization_alias="id")
    defect_class: str = Field(..., alias="class", serialization_alias="class")
    confidence: float
    bbox: Tuple[float, float, float, float] = Field(
        ..., alias="global_bbox_xyxy", serialization_alias="bbox"
    )
    polygon: List[Tuple[float, float]] = []
    panel: str = Field(..., alias="assigned_panel", serialization_alias="panel")
    iod: float = Field(..., alias="containment_ratio_iod", serialization_alias="iod")
    dsi: float = Field(
        ..., alias="damage_severity_index_dsi", serialization_alias="dsi"
    )


class InspectionPayload(BaseModel):
    inspection_id: str
    timestamp: str
    vehicle_color_detected: str
    total_defects_found: int
    inspection_status: str = Field(..., description="Expected values: 'PASS' or 'FAIL'")
    imageDims: Optional[ImageDims] = None
    preScreen: Optional[PreScreenResult] = None
    panels: Optional[List[Panel]] = None
    defects: List[Defect]
    unclassified_anomalies: List[UnclassifiedAnomaly] = []
    suppressed_detections: List[SuppressedDetection] = []
    stage1_blobs: List[Stage1Blob] = []
