import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.dataset_prep import (
    detect_dataset_structure,
    import_dataset_zip,
    resplit_dataset,
)
from schemas.dataset_prep import ResplitRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dataset-prep"])


@router.post("/api/datasets/import-dataset")
async def api_import_dataset(
    file: UploadFile = File(...),
    version_name: str = Form(...),
):
    """Import a whole YOLO-format dataset ZIP and auto-detect its split structure."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")
    try:
        contents = await file.read()
        return import_dataset_zip(version_name=version_name, zip_bytes=contents)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Dataset import failed")
        raise HTTPException(status_code=500, detail=f"Dataset import failed: {str(e)}")


@router.get("/api/datasets/{dataset_id}/split-structure")
def api_split_structure(dataset_id: str):
    """Detect and return the split structure of a dataset."""
    try:
        return detect_dataset_structure(dataset_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Split detection failed")
        raise HTTPException(status_code=500, detail=f"Split detection failed: {str(e)}")


@router.post("/api/datasets/{dataset_id}/resplit")
def api_resplit_dataset(dataset_id: str, body: ResplitRequest):
    """Re-split a dataset into train/val/test using image-level split."""
    try:
        new_structure = resplit_dataset(
            dataset_id=dataset_id,
            train_ratio=body.train_ratio,
            val_ratio=body.val_ratio,
            test_ratio=body.test_ratio,
            seed=body.seed,
        )
        return {
            "success": True,
            "dataset_id": dataset_id,
            "new_structure": new_structure,
            "message": f"Re-split '{dataset_id}' into train/val/test.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Resplit failed")
        raise HTTPException(status_code=500, detail=f"Resplit failed: {str(e)}")
