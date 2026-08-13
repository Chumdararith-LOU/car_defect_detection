from typing import Optional

from pydantic import BaseModel


class SystemMetrics(BaseModel):
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    gpu_name: Optional[str] = None
    gpu_utilization_percent: Optional[float] = None
    gpu_vram_used_gb: Optional[float] = None
    gpu_vram_total_gb: Optional[float] = None


class DeviceInfo(BaseModel):
    name: str
    type: str
    available: bool
