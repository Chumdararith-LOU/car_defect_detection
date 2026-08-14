"""Dataset management API endpoints (Phase 9)."""

from fastapi import APIRouter, HTTPException
from schemas.dataset import (
    DatasetBuildRequest,
    DatasetBuildResponse,
    DatasetDetail,
    DatasetListResponse,
    DatasetStatus,
    LeakageAuditResult,
)
from services.dataset_builder import build_dataset_from_reviews
from services.dataset_registry import (
    get_dataset_detail,
    list_datasets,
    run_leakage_audit,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["datasets"])


@router.get("/api/datasets", response_model=DatasetListResponse)
def api_list_datasets():
    """List all discovered datasets with summary metadata."""
    datasets = list_datasets()
    return DatasetListResponse(datasets=datasets)


@router.get("/api/datasets/{dataset_id}", response_model=DatasetDetail)
def api_get_dataset(dataset_id: str):
    """Get full dataset detail including class distribution."""
    detail = get_dataset_detail(dataset_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return detail


@router.post("/api/datasets/{dataset_id}/audit", response_model=LeakageAuditResult)
def api_audit_dataset(dataset_id: str):
    """Run leakage audit (filename overlap) on a specific dataset."""
    result = run_leakage_audit(dataset_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return result


@router.post("/api/datasets/build", response_model=DatasetBuildResponse)
def api_build_dataset(request: DatasetBuildRequest):
    """Build a new dataset version from reviewed flywheel feedback."""
    try:
        result = build_dataset_from_reviews(
            stage=request.stage.value,
            version_name=request.version_name,
            include_confirmed=request.include_confirmed,
            include_rejected=request.include_rejected,
            include_unclear=request.include_unclear,
            notes=request.notes,
        )
        return DatasetBuildResponse(
            dataset_id=result["dataset_id"],
            version_name=request.version_name,
            status=DatasetStatus.CURATED,
            message=(
                f"Dataset '{request.version_name}' built successfully. "
                f"Copied {result['stats']['images_copied']} images, "
                f"wrote {result['stats']['instances_written']} instances. "
                f"Skipped {result['stats']['skipped']} items."
            ),
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Dataset build failed")
        raise HTTPException(status_code=500, detail=f"Dataset build failed: {str(e)}")
