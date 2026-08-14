import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from services.dataset_images import (
    get_image_path,
    list_dataset_images,
    parse_yolo_labels,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["dataset-images"])


@router.get("/{dataset_id}/images")
def api_list_images(
    dataset_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    split: str = Query("train"),
):
    """List image filenames in a dataset with pagination."""
    result = list_dataset_images(dataset_id, page=page, page_size=size, split=split)
    return result


@router.get("/{dataset_id}/images/{filename}")
def api_serve_image(
    dataset_id: str,
    filename: str,
    split: str = Query("train"),
):
    """Serve a dataset image file directly (streaming)."""
    image_path = get_image_path(dataset_id, filename, split=split)
    if image_path is None:
        raise HTTPException(status_code=404, detail=f"Image '{filename}' not found")
    return FileResponse(image_path)


@router.get("/{dataset_id}/images/{filename}/labels")
def api_get_labels(
    dataset_id: str,
    filename: str,
    split: str = Query("train"),
):
    """Get parsed YOLO labels for a specific image."""
    annotations = parse_yolo_labels(dataset_id, filename, split=split)
    return {
        "filename": filename,
        "dataset_id": dataset_id,
        "split": split,
        "annotation_count": len(annotations),
        "annotations": annotations,
    }
