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
from services.dataset_registry import (
    get_dataset_detail,
    list_datasets,
    run_leakage_audit,
)

router = APIRouter(tags=["datasets"])


# ---------------------------------------------------------------------------
# GET /api/datasets — List all discovered datasets
# ---------------------------------------------------------------------------


@router.get("/api/datasets", response_model=DatasetListResponse)
def api_list_datasets():
    """List all discovered datasets with summary metadata."""
    datasets = list_datasets()
    return DatasetListResponse(datasets=datasets)


# ---------------------------------------------------------------------------
# GET /api/datasets/{dataset_id} — Full detail with class distribution
# ---------------------------------------------------------------------------


@router.get("/api/datasets/{dataset_id}", response_model=DatasetDetail)
def api_get_dataset(dataset_id: str):
    """Get full dataset detail including class distribution."""
    detail = get_dataset_detail(dataset_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return detail


# ---------------------------------------------------------------------------
# POST /api/datasets/{dataset_id}/audit — Leakage audit
# ---------------------------------------------------------------------------


@router.post("/api/datasets/{dataset_id}/audit", response_model=LeakageAuditResult)
def api_audit_dataset(dataset_id: str):
    """Run leakage audit (filename overlap) on a specific dataset."""
    result = run_leakage_audit(dataset_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return result


# ---------------------------------------------------------------------------
# POST /api/datasets/build — Build new version from reviewed feedback
# ---------------------------------------------------------------------------


@router.post("/api/datasets/build", response_model=DatasetBuildResponse)
def api_build_dataset(request: DatasetBuildRequest):
    """Build a new dataset version from reviewed flywheel feedback.

    Phase 9 placeholder: validates the request and returns a queued status.
    Full implementation will connect the review DB to the dataset pipeline.
    """
    # TODO: Implement actual dataset build from reviewed items
    return DatasetBuildResponse(
        dataset_id=f"{request.version_name}_pending",
        version_name=request.version_name,
        status=DatasetStatus.RAW,
        message=(
            f"Dataset build '{request.version_name}' registered. "
            f"Stage: {request.stage.value}. "
            f"Include confirmed={request.include_confirmed}, "
            f"rejected={request.include_rejected}, "
            f"unclear={request.include_unclear}. "
            f"Full build pipeline not yet connected."
        ),
    )
