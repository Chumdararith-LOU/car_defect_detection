"""Async batch inspection endpoints and job status polling."""
import json
import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.core.image import ImageDecodeError, decode_image
from app.core.job_queue import job_queue
from app.pipeline.orchestrator import run_pipeline
from app.schemas.pipeline import PipelineSpec

logger = logging.getLogger("api.batch")

router = APIRouter(prefix=settings.api_v1_str, tags=["batch"])


@router.post("/inspect/batch")
async def inspect_batch(
    files: List[UploadFile] = File(...),
    preset: str = Form("safety"),
    spec: Optional[str] = Form(None),
    return_crops: bool = Form(True),
    device: str = Form("auto"),
):
    """Submit a batch of images for asynchronous inspection. Returns a job_id."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided"
        )

    # Decode all images up front so we fail early on bad input.
    images = []
    for f in files:
        contents = await f.read()
        try:
            img_np = decode_image(contents)
        except ImageDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not decode '{f.filename}': {e}",
            )
        images.append((f.filename, img_np))

    # Build the pipeline spec once and reuse it for every image.
    try:
        if spec:
            base_spec = PipelineSpec(**json.loads(spec))
        else:
            base_spec = PipelineSpec(
                preset=preset, return_crops=return_crops, device=device
            )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid pipeline spec: {e}",
        )

    job_id = job_queue.create_job(total=len(images), preset=base_spec.preset)

    def worker():
        job_queue.mark_running(job_id)
        results = []
        try:
            for filename, img_np in images:
                payload = run_pipeline(img_np, base_spec)
                result = payload.model_dump(by_alias=True)
                result["source_filename"] = filename
                results.append(result)
                job_queue.increment_completed(job_id)
            job_queue.mark_done(job_id, results)
        except Exception as e:  # noqa: BLE001
            logger.exception("Batch job %s failed", job_id)
            job_queue.mark_failed(job_id, str(e))

    job_queue.submit(worker)
    return {"job_id": job_id, "status": "queued", "total": len(images)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    """Poll the status and results of a batch job."""
    job = job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


@router.get("/jobs")
def list_jobs(limit: int = 20):
    """List recent batch jobs."""
    return {"jobs": job_queue.list_jobs(limit=limit)}
