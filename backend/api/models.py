from fastapi import APIRouter

from core.model_manager import model_manager

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models")
def get_models() -> dict:
    """
    Dynamically scans backend/models/stage{1,2,3}/ for all valid .pt files.
    Automatically filters out Git LFS pointers and hidden files.
    """
    stage1_files = model_manager.list_available_models("stage1")
    stage2_files = model_manager.list_available_models("stage2")
    stage3_files = model_manager.list_available_models("stage3")

    return {
        "models": stage1_files,  # Legacy key for older frontend code
        "stage1": stage1_files,
        "stage2": stage2_files,
        "stage3": stage3_files,
    }
