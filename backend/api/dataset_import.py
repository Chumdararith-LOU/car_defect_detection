import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from services.dataset_import import (
    create_new_dataset,
    import_inspection_to_dataset,
    import_zip_to_dataset,
    list_available_inspections,
    upload_image_to_dataset,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dataset-import"])


@router.get("/api/import/inspections")
def api_list_inspections(limit: int = Query(50, ge=1, le=200)):
    """List saved inspections available for import."""
    inspections = list_available_inspections(limit=limit)
    return {"inspections": inspections, "total": len(inspections)}


@router.delete("/api/import/inspections/{inspection_id}", status_code=204)
def api_delete_inspection(inspection_id: str):
    """Delete a saved inspection from disk."""
    try:
        from services.dataset_import import delete_saved_inspection

        delete_saved_inspection(inspection_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.exception("Delete inspection failed")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


class InspectionImportRequest(BaseModel):
    inspection_id: str
    split: str = "train"


@router.post("/api/datasets/{dataset_id}/import/inspection")
def api_import_inspection(dataset_id: str, body: InspectionImportRequest):
    """Import a saved inspection (image + labels) into a dataset."""
    try:
        result = import_inspection_to_dataset(
            dataset_id=dataset_id,
            inspection_id=body.inspection_id,
            split=body.split,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Import inspection failed")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/api/datasets/{dataset_id}/import/upload")
async def api_upload_image(
    dataset_id: str,
    file: UploadFile = File(...),
    split: str = Form("train"),
):
    """Upload an image file directly into a dataset."""
    try:
        contents = await file.read()
        result = upload_image_to_dataset(
            dataset_id=dataset_id,
            image_bytes=contents,
            filename=file.filename or "upload.jpg",
            split=split,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# ---------------------------------------------------------------------------
# Create new dataset
# ---------------------------------------------------------------------------


class CreateDatasetRequest(BaseModel):
    version_name: str
    stage: str
    notes: Optional[str] = None


@router.post("/api/datasets/create")
def api_create_dataset(body: CreateDatasetRequest):
    """Create a new empty dataset with standard folder structure."""
    try:
        result = create_new_dataset(
            version_name=body.version_name,
            stage=body.stage,
            notes=body.notes,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Create dataset failed")
        raise HTTPException(status_code=500, detail=f"Create dataset failed: {str(e)}")


# ---------------------------------------------------------------------------
# Import ZIP archive
# ---------------------------------------------------------------------------


@router.post("/api/datasets/{dataset_id}/import/zip")
async def api_import_zip(
    dataset_id: str,
    file: UploadFile = File(...),
    split: str = Form("train"),
):
    """Import images and labels from a ZIP file into a dataset split."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    try:
        contents = await file.read()
        result = import_zip_to_dataset(
            dataset_id=dataset_id,
            zip_bytes=contents,
            split=split,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("ZIP import failed")
        raise HTTPException(status_code=500, detail=f"ZIP import failed: {str(e)}")
