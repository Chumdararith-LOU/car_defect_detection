from pathlib import Path
from typing import List

from fastapi import APIRouter

from core.config import settings
from core.model_manager import model_manager
from schemas.models import ChampionModel

router = APIRouter(prefix="/api", tags=["models"])

CHAMPION_MODELS = [
    {
        "stage": "stage1",
        "name": "Stage 1 — Binary SOD Pre-Screener",
        "path": "mlruns/1/f3b8f26d4f5847d2bc57f453253af798/artifacts/weights/best.pt",
    },
    {
        "stage": "stage2",
        "name": "Stage 2 — 7-Class Defect Segmentation",
        "path": "runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt",
    },
    {
        "stage": "stage3",
        "name": "Stage 3 — 21-Class Panel Segmenter",
        "path": "archive/pre_standardization/mlruns_legacy/Stage 3/2347b4e3ce1845cc97003d5534fedf99/artifacts/weights/best.pt",
    },
]

MB = 1024**2


@router.get("/models")
def get_models() -> dict:
    workspace = Path(settings.workspace_root).resolve()
    champions: List[ChampionModel] = []

    for entry in CHAMPION_MODELS:
        full_path = workspace / entry["path"]
        exists = full_path.is_file()
        size_mb = round(full_path.stat().st_size / MB, 2) if exists else None
        champions.append(
            ChampionModel(
                stage=entry["stage"],
                name=entry["name"],
                path=entry["path"],
                available=exists,
                size_mb=size_mb,
            )
        )

    stage1_files = model_manager.list_available_models("stage1")
    return {
        "models": stage1_files,
        "stage1": stage1_files,
        "stage2": model_manager.list_available_models("stage2"),
        "stage3": model_manager.list_available_models("stage3"),
        "champions": champions,
    }
