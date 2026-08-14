import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.dataset_images import (
    delete_annotation,
    get_class_names,
    get_image_path,
    list_dataset_images,
    parse_yolo_labels,
    reclassify_annotation,
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
    class_names = get_class_names(dataset_id)
    return {
        "filename": filename,
        "dataset_id": dataset_id,
        "split": split,
        "annotation_count": len(annotations),
        "annotations": annotations,
        "class_names": class_names,
    }


# ---------------------------------------------------------------------------
# Reclassify annotation
# ---------------------------------------------------------------------------


class ReclassifyRequest(BaseModel):
    new_class_id: int


@router.patch("/{dataset_id}/images/{filename}/labels/{annotation_index}")
def api_reclassify_annotation(
    dataset_id: str,
    filename: str,
    annotation_index: int,
    body: ReclassifyRequest,
    split: str = Query("train"),
):
    """Change the class_id of a specific annotation in the YOLO label file."""
    try:
        result = reclassify_annotation(
            dataset_id=dataset_id,
            filename=filename,
            annotation_index=annotation_index,
            new_class_id=body.new_class_id,
            split=split,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Reclassify failed")
        raise HTTPException(status_code=500, detail=f"Reclassify failed: {str(e)}")


@router.delete("/{dataset_id}/images/{filename}/labels/{annotation_index}")
def api_delete_annotation(
    dataset_id: str,
    filename: str,
    annotation_index: int,
    split: str = Query("train"),
):
    """Delete a specific annotation from the YOLO label file (false positive removal)."""
    try:
        result = delete_annotation(
            dataset_id=dataset_id,
            filename=filename,
            annotation_index=annotation_index,
            split=split,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Delete annotation failed")
        raise HTTPException(
            status_code=500, detail=f"Delete annotation failed: {str(e)}"
        )
