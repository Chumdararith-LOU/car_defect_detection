import logging
import re
import yaml
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from core.config import settings
from schemas.training import JobListResponse, LaunchRequest, TrainingJob
from services.training_db import training_db
from services.training_worker import worker
from services import checkpoint_registry, recipe_service
from services.dataset_registry import get_dataset_detail
from services.recipe_config_builder import build_config_from_recipe

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training", tags=["training"])


def _resolve_recipe_config(request: LaunchRequest) -> dict:
    """Validate a recipe launch request and build the trainer config dict."""
    recipe_id = request.recipe_id
    if not recipe_id:
        raise HTTPException(status_code=422, detail="recipe_id is required")
    try:
        recipe = recipe_service.get_recipe(recipe_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="recipe not found")

    if not request.dataset_id:
        raise HTTPException(
            status_code=422, detail="dataset_id is required for recipe launches"
        )
    dataset = get_dataset_detail(request.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=422, detail=f"dataset not found: {request.dataset_id}"
        )

    strategy = recipe.get("base_strategy")
    if strategy == "from_previous_step":
        raise HTTPException(
            status_code=422,
            detail="base_strategy 'from_previous_step' is only valid inside a chain",
        )

    checkpoint_id = request.base_checkpoint_id or recipe.get("base_checkpoint_id")
    if strategy == "native_coco" and not checkpoint_id:
        natives = [
            c
            for c in checkpoint_registry.list_checkpoints()
            if c["origin"] == "native_coco"
        ]
        if natives:
            checkpoint_id = natives[0]["id"]
    if not checkpoint_id:
        raise HTTPException(
            status_code=422,
            detail="base_checkpoint_id is required for this recipe strategy",
        )

    try:
        checkpoint = checkpoint_registry.get_checkpoint(checkpoint_id)
    except LookupError:
        raise HTTPException(
            status_code=422, detail=f"checkpoint not found: {checkpoint_id}"
        )
    if not checkpoint.get("exists"):
        raise HTTPException(
            status_code=422,
            detail=f"checkpoint file missing on disk: {checkpoint['path']}",
        )

    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", recipe["name"]).strip("_") or "recipe"
    run_name = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    request.dataset_path = dataset.yaml_path
    request.run_name = run_name
    request.project_name = request.project_name or safe_name
    request.base_checkpoint_id = checkpoint_id
    return build_config_from_recipe(
        recipe, dataset.yaml_path, checkpoint["path"], run_name
    )


@router.post("/jobs", response_model=TrainingJob)
def launch_training_job(request: LaunchRequest):
    """Launch a new training job in the background."""
    try:
        config_dict = None
        if request.recipe_id:
            config_dict = _resolve_recipe_config(request)
        if not request.dataset_path:
            raise HTTPException(
                status_code=422,
                detail="dataset_path is required (or recipe_id with dataset_id)",
            )
        job = worker.launch(request, config_dict=config_dict)
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to launch training job")
        raise HTTPException(status_code=500, detail=f"Failed to launch job: {str(e)}")


@router.get("/jobs", response_model=JobListResponse)
def list_training_jobs(limit: int = 50, offset: int = 0):
    """List past and current training jobs."""
    jobs = training_db.list_jobs(limit=limit, offset=offset)
    total = training_db.count_jobs()
    return JobListResponse(jobs=jobs, total=total)


@router.get("/jobs/{job_id}", response_model=TrainingJob)
def get_training_job(job_id: str):
    """Get details of a specific training job."""
    job = training_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.get("/jobs/{job_id}/logs")
def get_training_job_logs(job_id: str):
    """Read the stdout/stderr log file for a training job."""
    job = training_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if not job.log_file or not Path(job.log_file).exists():
        return PlainTextResponse(content="", media_type="text/plain")

    try:
        with open(job.log_file, "r") as f:
            content = f.read()
        return PlainTextResponse(content=content, media_type="text/plain")
    except Exception as e:
        logger.exception(f"Failed to read logs for {job_id}")
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")


@router.get("/config-template")
def get_config_template(stage: str):
    """Return the champion config template for a given stage as JSON."""
    template_map = {
        "stage1": "configs/train/stage1/stage1-sod.yaml",
        "stage2": "configs/train/stage2/model5_stage1_head_warmup_7cls_extended.yaml",
        "stage3": "configs/train/stage3/panel_segmenter_baseline.yaml",
    }
    rel_path = template_map.get(stage)
    if not rel_path:
        raise HTTPException(status_code=400, detail=f"Unknown stage: {stage}")

    abs_path = settings.workspace_root / rel_path
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail=f"Template not found: {rel_path}")

    with open(abs_path, "r") as f:
        data = yaml.safe_load(f) or {}

    return {"stage": stage, "template": data, "source_path": rel_path}


@router.post("/jobs/{job_id}/stop")
def stop_training_job(job_id: str):
    """Stop a running training job."""
    success = worker.stop_job(job_id)
    if success:
        return {"success": True, "message": f"Job '{job_id}' terminated."}
    else:
        # Might be already finished or not found in active processes
        job = training_db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return {
            "success": False,
            "message": f"Job '{job_id}' is not currently running.",
        }
