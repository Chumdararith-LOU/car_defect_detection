from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageType(str, Enum):
    STAGE1 = "stage1"
    STAGE2 = "stage2"
    STAGE3 = "stage3"


class LaunchRequest(BaseModel):
    stage: StageType
    dataset_path: Optional[str] = None
    dataset_id: Optional[str] = None
    config_path: Optional[str] = None
    base_model: Optional[str] = None
    device: str = "0"
    project_name: Optional[str] = None
    run_name: Optional[str] = None
    overrides: Dict[str, Any] = Field(default_factory=dict)
    recipe_id: Optional[str] = None
    base_checkpoint_id: Optional[str] = None
    job_type: str = "training"


class TrainingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage: StageType
    status: JobStatus = JobStatus.PENDING
    dataset_path: str
    config_path: Optional[str] = None
    base_model: Optional[str] = None
    device: str = "0"
    project_name: str
    run_name: str
    overrides: Dict[str, Any] = Field(default_factory=dict)
    config_dict: Optional[Dict[str, Any]] = Field(default=None, exclude=True)

    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    log_file: Optional[str] = None
    mlflow_run_id: Optional[str] = None
    error_message: Optional[str] = None

    job_type: str = "training"
    recipe_id: Optional[str] = None
    base_checkpoint_id: Optional[str] = None
    output_checkpoint_id: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[TrainingJob]
    total: int
