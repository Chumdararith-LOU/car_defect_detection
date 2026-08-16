from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.model_registry import (
    DeploymentResponse,
    ModelListResponse,
    ModelStatus,
    ModelVersion,
    PromotionResponse,
    RegisterRequest,
    RollbackResponse,
    StageType,
)
from services.model_registry_service import (
    deploy_model,
    promote_model,
    register_model,
    rollback_stage,
)
from services.model_registry_db import model_registry_db

router = APIRouter(prefix="/api/model-registry", tags=["Model Registry"])


@router.get("", response_model=ModelListResponse)
def list_models(
    stage: Optional[StageType] = Query(None),
    status: Optional[ModelStatus] = Query(None),
) -> ModelListResponse:
    """List all model versions, optionally filtered by stage and status."""
    models = model_registry_db.list_models(stage=stage, status=status)
    return ModelListResponse(models=models, total=len(models))


@router.get("/{model_id}", response_model=ModelVersion)
def get_model_detail(model_id: str) -> ModelVersion:
    """Get detailed information about a specific model version."""
    model = model_registry_db.get_by_id(model_id)
    if model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return model


@router.post("/register", response_model=ModelVersion, status_code=201)
def register_candidate(request: RegisterRequest) -> ModelVersion:
    """Register a new candidate model in the registry."""
    return register_model(request)


@router.post("/{model_id}/promote", response_model=PromotionResponse)
def promote_candidate(model_id: str) -> PromotionResponse:
    """
    Promote a candidate to champion.
    Runs evaluation gates against the current champion.
    If all gates pass, archives the old champion and promotes the candidate.
    """
    result = promote_model(model_id)
    if not result.promoted and "not found" in result.message:
        raise HTTPException(status_code=404, detail=result.message)
    return result


@router.post("/{model_id}/deploy", response_model=DeploymentResponse)
def deploy_champion(model_id: str) -> DeploymentResponse:
    """
    Deploy a champion model to production.
    Updates the symlink in backend/models/stage{N}/ to point to the champion weights.
    """
    result = deploy_model(model_id)
    if not result.deployed and "not found" in result.message:
        raise HTTPException(status_code=404, detail=result.message)
    return result


@router.post("/stage/{stage}/rollback", response_model=RollbackResponse)
def rollback_to_previous(stage: StageType) -> RollbackResponse:
    """
    Rollback to the previously deployed model for a given stage.
    Reverts the production symlink to the model that was deployed before the current one.
    """
    result = rollback_stage(stage)
    if not result.rolled_back and "No deployed model found" in result.message:
        raise HTTPException(status_code=404, detail=result.message)
    return result
