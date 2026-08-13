from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MachineInfo(BaseModel):
    hostname: str
    os: str
    platform: str
    architecture: str
    python_version: str


class CpuInfo(BaseModel):
    logical_cores: int
    physical_cores: int


class MemoryInfo(BaseModel):
    total_gb: float
    available_gb: float


class DiskInfo(BaseModel):
    workspace_path: str
    free_gb: float
    total_gb: float


class GpuDevice(BaseModel):
    index: int
    name: str
    total_vram_gb: float
    free_vram_gb: Optional[float] = None


class GpuInfo(BaseModel):
    cuda_available: bool = False
    mps_available: bool = False
    cuda_version: Optional[str] = None
    device_count: int = 0
    devices: List[GpuDevice] = Field(default_factory=list)


class ModelAvailability(BaseModel):
    available: bool
    version: Optional[str] = None
    path_status: str = "missing"
    path: Optional[str] = None


class RemoteInfo(BaseModel):
    configured: bool = False
    reachable: bool = False
    auth_ok: bool = False
    base_url: Optional[str] = None
    host_profile: Optional[str] = None


class Capabilities(BaseModel):
    can_infer_stage1: bool
    can_infer_stage2: bool
    can_infer_stage3: bool
    can_run_stage4: bool
    can_train_stage1: bool
    can_train_stage2: bool
    can_train_stage3: bool
    can_use_local_gpu: bool
    can_use_remote: bool


class Recommendations(BaseModel):
    runtime_mode: str
    inference_device: str
    training_device: str
    reason: str


class HostProfile(BaseModel):
    schema_version: str = "0.1"
    generated_at: datetime
    machine: MachineInfo
    cpu: CpuInfo
    memory: MemoryInfo
    disk: DiskInfo
    gpu: GpuInfo
    models: Dict[str, ModelAvailability]
    datasets: Dict[str, str] = Field(default_factory=dict)
    remote: RemoteInfo = Field(default_factory=RemoteInfo)
    capabilities: Capabilities
    recommendations: Recommendations
    warnings: List[str] = Field(default_factory=list)
