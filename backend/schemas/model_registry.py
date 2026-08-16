from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ModelStatus(str, Enum):
    CANDIDATE = "candidate"
    CHAMPION = "champion"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class StageType(str, Enum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"


class ModelVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage: StageType
    model_name: str
    version: str
    status: ModelStatus = ModelStatus.CANDIDATE
    weights_path: str
    config_hash: Optional[str] = None
    dataset_version: Optional[str] = None
    training_run_id: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evaluation_report: Dict[str, Any] = Field(default_factory=dict)
    model_card: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    promoted_at: Optional[str] = None
    deployed_at: Optional[str] = None


class RegisterRequest(BaseModel):
    stage: StageType
    model_name: str
    version: str
    weights_path: str
    config_hash: Optional[str] = None
    dataset_version: Optional[str] = None
    training_run_id: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    model_card: Optional[str] = None


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    candidate_value: Optional[float] = None
    champion_value: Optional[float] = None
    threshold: Optional[str] = None
    reason: Optional[str] = None


class PromotionResponse(BaseModel):
    model_id: str
    promoted: bool
    gate_results: List[GateResult]
    message: str


class DeploymentResponse(BaseModel):
    model_id: str
    deployed: bool
    message: str


class RollbackResponse(BaseModel):
    stage: StageType
    rolled_back: bool
    previous_model_id: Optional[str] = None
    current_model_id: Optional[str] = None
    message: str


class ModelListResponse(BaseModel):
    models: List[ModelVersion]
    total: int
