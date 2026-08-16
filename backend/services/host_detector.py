import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import psutil

from core.config import settings
from schemas.host import (
    Capabilities,
    CpuInfo,
    DiskInfo,
    GpuDevice,
    GpuInfo,
    HostProfile,
    MachineInfo,
    MemoryInfo,
    ModelAvailability,
    Recommendations,
    RemoteInfo,
)
from schemas.model_registry import ModelStatus, StageType
from services.model_registry_db import model_registry_db

GB = 1024**3
MIN_TRAINING_VRAM_GB = 12.0
LOW_DISK_FREE_GB = 50.0

CHAMPION_WEIGHT_PATHS = {
    "stage1": Path(
        "mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt"
    ),
    "stage2": Path(
        "runs/segment/stage1_head_warmup_7cls_extended/"
        "stage1_head_warmup_7cls_extended/weights/best.pt"
    ),
    "stage3": Path(
        "mlruns/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt"
    ),
}

MODEL_VERSIONS = {
    "stage1": "sod_v1.0.0",
    "stage2": "stage2_head_warmup_7cls_extended_v1.0.0",
    "stage3": "panel_segmenter_baseline_v1.0.0",
}

STAGE4_CONFIG_PATH = Path("configs/inference/sahi_production.yaml")

DATASET_YAML_PATHS = {
    "stage1_binary": Path("data/processed/sod_tiled/sod_data_tiled.yaml"),
    "stage2_7cls": Path("data/processed/yolo_seg_clean_2200_7cls/dataset.yaml"),
    "stage3_panel": Path(
        "data/processed/stage3/car_damages_panel/car_damages_panel.yaml"
    ),
}


def _detect_machine() -> MachineInfo:
    return MachineInfo(
        hostname=socket.gethostname(),
        os=f"{platform.system()} {platform.release()}",
        platform=platform.platform(),
        architecture=platform.machine(),
        python_version=platform.python_version(),
    )


def _detect_cpu() -> CpuInfo:
    return CpuInfo(
        logical_cores=psutil.cpu_count(logical=True) or 0,
        physical_cores=psutil.cpu_count(logical=False) or 0,
    )


def _detect_memory() -> MemoryInfo:
    vm = psutil.virtual_memory()
    return MemoryInfo(
        total_gb=round(vm.total / GB, 2),
        available_gb=round(vm.available / GB, 2),
    )


def _detect_disk(workspace_root: Path) -> DiskInfo:
    usage = psutil.disk_usage(str(workspace_root))
    return DiskInfo(
        workspace_path=str(workspace_root),
        free_gb=round(usage.free / GB, 2),
        total_gb=round(usage.total / GB, 2),
    )


def _detect_gpu() -> GpuInfo:
    try:
        import torch
    except Exception:
        return GpuInfo(cuda_available=False, mps_available=False)

    # Check CUDA first (Ubuntu server)
    if torch.cuda.is_available():
        devices: List[GpuDevice] = []
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            free_gb = None
            try:
                free_bytes, _ = torch.cuda.mem_get_info(index)
                free_gb = round(free_bytes / GB, 2)
            except Exception:
                free_gb = None
            devices.append(
                GpuDevice(
                    index=index,
                    name=props.name,
                    total_vram_gb=round(props.total_memory / GB, 2),
                    free_vram_gb=free_gb,
                )
            )
        return GpuInfo(
            cuda_available=True,
            mps_available=False,
            cuda_version=torch.version.cuda,
            device_count=len(devices),
            devices=devices,
        )

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        vm = psutil.virtual_memory()
        total_gb = round(vm.total / GB, 2)
        try:
            allocated_bytes = torch.mps.current_allocated_memory()
            free_gb = round((vm.total - allocated_bytes) / GB, 2)
        except Exception:
            free_gb = round(vm.available / GB, 2)

        devices = [
            GpuDevice(
                index=0,
                name="Apple Silicon (MPS)",
                total_vram_gb=total_gb,
                free_vram_gb=free_gb,
            )
        ]
        return GpuInfo(
            cuda_available=False,
            mps_available=True,
            device_count=1,
            devices=devices,
        )

    return GpuInfo(cuda_available=False, mps_available=False)


def _resolve_stage_weights(workspace_root: Path, stage: str) -> Optional[Path]:
    deployed_link = workspace_root / "backend" / "models" / stage / "deployed.pt"
    if deployed_link.is_file():
        return deployed_link

    try:
        deployed_rows = model_registry_db.list_models(
            stage=StageType(stage), status=ModelStatus.DEPLOYED
        )
    except Exception:
        deployed_rows = []
    for row in deployed_rows:
        candidate = Path(row.weights_path)
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        if candidate.is_file():
            return candidate

    fallback = CHAMPION_WEIGHT_PATHS.get(stage)
    if fallback is not None and (workspace_root / fallback).is_file():
        return workspace_root / fallback

    return None


def _detect_models(workspace_root: Path) -> Dict[str, ModelAvailability]:
    models: Dict[str, ModelAvailability] = {}
    for stage, rel_path in CHAMPION_WEIGHT_PATHS.items():
        resolved = _resolve_stage_weights(workspace_root, stage)
        found = resolved is not None
        if found:
            try:
                display_path = str(resolved.relative_to(workspace_root))
            except ValueError:
                display_path = str(resolved)
        else:
            display_path = str(rel_path)
        models[stage] = ModelAvailability(
            available=found,
            version=MODEL_VERSIONS[stage],
            path_status="found" if found else "missing",
            path=display_path,
        )
    stage4_found = (workspace_root / STAGE4_CONFIG_PATH).is_file()
    models["stage4"] = ModelAvailability(
        available=stage4_found,
        path_status="found" if stage4_found else "missing",
        path=str(STAGE4_CONFIG_PATH),
    )
    return models


def _detect_datasets(workspace_root: Path) -> Dict[str, str]:
    return {
        name: ("released" if (workspace_root / rel_path).is_file() else "missing")
        for name, rel_path in DATASET_YAML_PATHS.items()
    }


def _build_capabilities(
    models: Dict[str, ModelAvailability],
    gpu: GpuInfo,
    remote: RemoteInfo,
    allow_cpu: bool,
) -> Capabilities:
    has_gpu = gpu.cuda_available or gpu.mps_available
    inference_device_ok = has_gpu or allow_cpu
    return Capabilities(
        can_infer_stage1=models["stage1"].available and inference_device_ok,
        can_infer_stage2=models["stage2"].available and inference_device_ok,
        can_infer_stage3=models["stage3"].available and inference_device_ok,
        can_run_stage4=models["stage4"].available,
        can_train_stage1=gpu.cuda_available,
        can_train_stage2=gpu.cuda_available,
        can_train_stage3=gpu.cuda_available,
        can_use_local_gpu=has_gpu,
        can_use_remote=remote.configured and remote.reachable,
    )


def _build_recommendations(
    models: Dict[str, ModelAvailability],
    gpu: GpuInfo,
    remote: RemoteInfo,
    allow_cpu: bool,
) -> Recommendations:
    all_models_present = all(
        models[stage].available for stage in ("stage1", "stage2", "stage3")
    )

    if gpu.cuda_available and all_models_present:
        return Recommendations(
            runtime_mode="local",
            inference_device="cuda",
            training_device="cuda",
            reason="Local CUDA GPU detected and champion models are available.",
        )

    if gpu.mps_available and all_models_present:
        return Recommendations(
            runtime_mode="local",
            inference_device="mps",
            training_device="none",
            reason="Apple Silicon MPS detected. Inference on MPS; training requires CUDA server.",
        )

    if remote.configured and remote.reachable:
        return Recommendations(
            runtime_mode="remote",
            inference_device="remote",
            training_device="remote",
            reason="Local GPU or models insufficient; remote server is configured and reachable.",
        )

    if allow_cpu and all_models_present:
        return Recommendations(
            runtime_mode="local",
            inference_device="cpu",
            training_device="none",
            reason="No GPU available; falling back to local CPU inference (slow).",
        )

    return Recommendations(
        runtime_mode="unavailable",
        inference_device="none",
        training_device="none",
        reason="No usable local device, models, or remote server detected.",
    )


def _build_warnings(
    models: Dict[str, ModelAvailability],
    gpu: GpuInfo,
    disk: DiskInfo,
) -> List[str]:
    warnings: List[str] = []
    has_gpu = gpu.cuda_available or gpu.mps_available
    if not has_gpu:
        warnings.append("no_gpu")
    elif gpu.cuda_available and all(
        device.total_vram_gb < MIN_TRAINING_VRAM_GB for device in gpu.devices
    ):
        warnings.append("low_vram")
    if any(not model.available for model in models.values()):
        warnings.append("missing_models")
    if disk.free_gb < LOW_DISK_FREE_GB:
        warnings.append("low_disk")
    return warnings


def detect_host_profile() -> HostProfile:
    workspace_root = Path(settings.workspace_root).resolve()
    remote = RemoteInfo()
    gpu = _detect_gpu()
    models = _detect_models(workspace_root)
    disk = _detect_disk(workspace_root)

    return HostProfile(
        schema_version="0.1",
        generated_at=datetime.now(timezone.utc),
        machine=_detect_machine(),
        cpu=_detect_cpu(),
        memory=_detect_memory(),
        disk=disk,
        gpu=gpu,
        models=models,
        datasets=_detect_datasets(workspace_root),
        remote=remote,
        capabilities=_build_capabilities(
            models, gpu, remote, settings.allow_cpu_inference
        ),
        recommendations=_build_recommendations(
            models, gpu, remote, settings.allow_cpu_inference
        ),
        warnings=_build_warnings(models, gpu, disk),
    )
