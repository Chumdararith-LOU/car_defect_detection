import logging
from datetime import datetime
from pathlib import Path

from core.config import settings
from schemas.model_registry import (
    DeploymentResponse,
    ModelStatus,
    ModelVersion,
    PromotionResponse,
    RegisterRequest,
    RollbackResponse,
    StageType,
)
from services.evaluation_gates import all_gates_passed, evaluate_gates
from services.model_registry_db import model_registry_db

logger = logging.getLogger("ModelRegistryService")

# Deployment symlink name used by ModelManager to discover active models
DEPLOYED_WEIGHTS_NAME = "deployed.pt"


def _stage_dir(stage: StageType) -> Path:
    """Return the backend/models/stage{N}/ directory for a given stage."""
    return settings.workspace_root / "backend" / "models" / stage.value


def register_model(request: RegisterRequest) -> ModelVersion:
    """Register a new candidate model in the registry."""
    model = ModelVersion(
        stage=request.stage,
        model_name=request.model_name,
        version=request.version,
        status=ModelStatus.CANDIDATE,
        weights_path=request.weights_path,
        config_hash=request.config_hash,
        dataset_version=request.dataset_version,
        training_run_id=request.training_run_id,
        metrics=request.metrics,
        model_card=request.model_card,
    )
    model_registry_db.insert(model)
    logger.info(
        f"Registered candidate model: {model.model_name} v{model.version} ({model.stage.value})"
    )
    return model


def promote_model(model_id: str) -> PromotionResponse:
    """
    Promote a candidate to champion.
    Runs evaluation gates against the current champion.
    If all gates pass, archives the old champion and promotes the candidate.
    """
    candidate = model_registry_db.get_by_id(model_id)
    if candidate is None:
        return PromotionResponse(
            model_id=model_id,
            promoted=False,
            gate_results=[],
            message=f"Model {model_id} not found",
        )

    if candidate.status != ModelStatus.CANDIDATE:
        return PromotionResponse(
            model_id=model_id,
            promoted=False,
            gate_results=[],
            message=f"Model is not a candidate (current status: {candidate.status.value})",
        )

    # Get current champion for comparison
    champion = model_registry_db.get_champion(candidate.stage)

    # Run evaluation gates
    gate_results = evaluate_gates(candidate, champion)
    passed = all_gates_passed(gate_results)

    if not passed:
        # Save gate results to evaluation report but do not promote
        report = {"gates": [g.model_dump() for g in gate_results], "passed": False}
        model_registry_db.update_evaluation_report(model_id, report)
        failed_gates = [g.gate_name for g in gate_results if not g.passed]
        return PromotionResponse(
            model_id=model_id,
            promoted=False,
            gate_results=gate_results,
            message=f"Promotion blocked. Failed gates: {', '.join(failed_gates)}",
        )

    # All gates passed — promote
    now = datetime.utcnow().isoformat()

    # Archive old champion if exists
    if champion is not None:
        model_registry_db.update_status(champion.id, ModelStatus.ARCHIVED)
        logger.info(
            f"Archived previous champion: {champion.model_name} v{champion.version}"
        )

    # Promote candidate to champion
    model_registry_db.update_status(model_id, ModelStatus.CHAMPION, promoted_at=now)

    # Save gate results
    report = {"gates": [g.model_dump() for g in gate_results], "passed": True}
    model_registry_db.update_evaluation_report(model_id, report)

    logger.info(
        f"Promoted model {candidate.model_name} v{candidate.version} to champion"
    )
    return PromotionResponse(
        model_id=model_id,
        promoted=True,
        gate_results=gate_results,
        message="Successfully promoted to champion. Previous champion archived.",
    )


def deploy_model(model_id: str) -> DeploymentResponse:
    """
    Deploy a champion model to production.
    Updates the symlink in backend/models/stage{N}/ to point to the champion weights.
    """
    model = model_registry_db.get_by_id(model_id)
    if model is None:
        return DeploymentResponse(
            model_id=model_id,
            deployed=False,
            message=f"Model {model_id} not found",
        )

    if model.status != ModelStatus.CHAMPION:
        return DeploymentResponse(
            model_id=model_id,
            deployed=False,
            message=f"Only champion models can be deployed (current status: {model.status.value})",
        )

    # Verify weights file exists
    weights_path = Path(model.weights_path)
    if not weights_path.is_absolute():
        weights_path = settings.workspace_root / weights_path
    if not weights_path.exists():
        return DeploymentResponse(
            model_id=model_id,
            deployed=False,
            message=f"Weights file not found: {weights_path}",
        )

    # Create/update symlink in backend/models/stage{N}/
    stage_dir = _stage_dir(model.stage)
    stage_dir.mkdir(parents=True, exist_ok=True)
    symlink_path = stage_dir / DEPLOYED_WEIGHTS_NAME

    # Remove existing symlink if present
    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()

    # Create new symlink
    symlink_path.symlink_to(weights_path.resolve())
    logger.info(f"Deployed {model.model_name} v{model.version} → {symlink_path}")

    # Update status
    now = datetime.utcnow().isoformat()
    model_registry_db.update_status(model_id, ModelStatus.DEPLOYED, deployed_at=now)

    return DeploymentResponse(
        model_id=model_id,
        deployed=True,
        message=f"Deployed successfully. Symlink: {symlink_path} → {weights_path.resolve()}",
    )


def rollback_stage(stage: StageType) -> RollbackResponse:
    """
    Rollback to the previously deployed model for a given stage.
    Finds the current deployed model, then reverts to the one before it.
    """
    current = model_registry_db.get_deployed(stage)
    if current is None:
        return RollbackResponse(
            stage=stage,
            rolled_back=False,
            message=f"No deployed model found for {stage.value}",
        )

    # Find the previous deployed model (before current)
    previous = model_registry_db.get_previous_deployed(stage, exclude_id=current.id)
    if previous is None:
        # Fallback: try to find any champion for this stage
        champion = model_registry_db.get_champion(stage)
        if champion is None:
            return RollbackResponse(
                stage=stage,
                rolled_back=False,
                current_model_id=current.id,
                message="No previous model available for rollback",
            )
        previous = champion

    # Verify previous model weights exist
    weights_path = Path(previous.weights_path)
    if not weights_path.is_absolute():
        weights_path = settings.workspace_root / weights_path
    if not weights_path.exists():
        return RollbackResponse(
            stage=stage,
            rolled_back=False,
            current_model_id=current.id,
            previous_model_id=previous.id,
            message=f"Previous model weights not found: {weights_path}",
        )

    # Update symlink
    stage_dir = _stage_dir(stage)
    symlink_path = stage_dir / DEPLOYED_WEIGHTS_NAME

    if symlink_path.exists() or symlink_path.is_symlink():
        symlink_path.unlink()
    symlink_path.symlink_to(weights_path.resolve())

    # Update statuses
    now = datetime.utcnow().isoformat()
    model_registry_db.update_status(current.id, ModelStatus.ARCHIVED)
    model_registry_db.update_status(previous.id, ModelStatus.DEPLOYED, deployed_at=now)

    logger.info(
        f"Rolled back {stage.value}: {current.model_name} → {previous.model_name}"
    )
    return RollbackResponse(
        stage=stage,
        rolled_back=True,
        previous_model_id=previous.id,
        current_model_id=current.id,
        message=f"Rolled back from {current.model_name} v{current.version} to {previous.model_name} v{previous.version}",
    )
