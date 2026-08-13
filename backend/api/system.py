from typing import List

import psutil
from fastapi import APIRouter

from schemas.system import DeviceInfo, SystemMetrics

router = APIRouter(prefix="/api", tags=["system"])

GB = 1024**3


@router.get("/system/metrics", response_model=SystemMetrics)
def get_system_metrics() -> SystemMetrics:
    cpu_percent = psutil.cpu_percent(interval=0.5)
    vm = psutil.virtual_memory()

    gpu_name = None
    gpu_utilization_percent = None
    gpu_vram_used_gb = None
    gpu_vram_total_gb = None

    try:
        import torch

        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            gpu_name = torch.cuda.get_device_name(device)
            gpu_vram_total_gb = round(
                torch.cuda.get_device_properties(device).total_memory / GB, 2
            )
            allocated = torch.cuda.memory_allocated(device)
            gpu_vram_used_gb = round(allocated / GB, 2)
            gpu_utilization_percent = 0.0
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu_name = "Apple Silicon (MPS)"
            gpu_vram_total_gb = round(vm.total / GB, 2)
            try:
                gpu_vram_used_gb = round(torch.mps.current_allocated_memory() / GB, 2)
            except Exception:
                gpu_vram_used_gb = 0.0
            gpu_utilization_percent = None
    except Exception:
        pass

    return SystemMetrics(
        cpu_percent=cpu_percent,
        ram_used_gb=round(vm.used / GB, 2),
        ram_total_gb=round(vm.total / GB, 2),
        gpu_name=gpu_name,
        gpu_utilization_percent=gpu_utilization_percent,
        gpu_vram_used_gb=gpu_vram_used_gb,
        gpu_vram_total_gb=gpu_vram_total_gb,
    )


@router.get("/system/devices", response_model=List[DeviceInfo])
def get_system_devices() -> List[DeviceInfo]:
    devices = [DeviceInfo(name="cpu", type="cpu", available=True)]

    try:
        import torch

        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_properties(i).name
                devices.append(DeviceInfo(name=name, type=f"cuda:{i}", available=True))
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devices.append(DeviceInfo(name="Apple Silicon", type="mps", available=True))
    except Exception:
        pass

    return devices
