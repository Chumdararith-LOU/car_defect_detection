"""Head surgery service for the Stage 2 Training Platform (Phase C).

Remaps a checkpoint's detection head to a target taxonomy's class count
and registers the result as an origin=surgery checkpoint. Remap core is
ported from src/stage2/Resume-and-Adapt/remap_model1_head.py.
"""

import copy
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import torch
from ultralytics import YOLO
from ultralytics.nn.tasks import SegmentationModel

from schemas.surgery import SurgeryStatusResponse
from schemas.training import JobStatus, StageType, TrainingJob
from services import checkpoint_registry, taxonomy_service
from services.platform_db import get_db
from services.training_db import training_db

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
SURGERY_DIR = BACKEND_DIR / "data" / "surgery"


class SurgeryJobNotFoundError(LookupError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _torch_load(path: str):
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def _remap_head(source_path: str, new_nc: int, head_init_mode: str):
    """Rebuild the source model with new_nc classes, copying matching weights."""
    source = YOLO(source_path)
    source_model = source.model.float()
    src_state = source_model.state_dict()

    model_cfg = getattr(source_model, "yaml", None)
    if model_cfg is None:
        raise RuntimeError(
            "Could not read model YAML from source checkpoint. "
            "The source architecture config is required to rebuild the head."
        )
    model_cfg = copy.deepcopy(model_cfg)
    if not isinstance(model_cfg, dict):
        model_cfg = dict(model_cfg)

    # Remove old class names so they do not conflict with the new nc.
    model_cfg.pop("names", None)
    old_nc = model_cfg.get("nc", None)
    model_cfg["nc"] = new_nc

    target = SegmentationModel(model_cfg, ch=3, nc=new_nc)
    target_state = target.state_dict()

    filtered_src_state = {}
    shape_mismatched = []
    for key, value in src_state.items():
        if key not in target_state:
            continue
        if target_state[key].shape != value.shape:
            shape_mismatched.append(key)
        else:
            filtered_src_state[key] = value

    if head_init_mode == "class_aware" and old_nc:
        # Class-aware init: box/mask head tensors are nc-independent and are
        # already copied by the shape-match loop above. For class-branch (cv3)
        # convs whose only difference is the class dimension, copy the first
        # min(old_nc, new_nc) rows so shared class detectors keep their
        # learned weights while extra rows retain fresh init.
        for key in shape_mismatched:
            src_t = src_state[key]
            tgt_t = target_state[key]
            if ".cv3." not in key or src_t.dim() != tgt_t.dim():
                continue
            if src_t.shape[0] != old_nc or tgt_t.shape[0] != new_nc:
                continue
            if tuple(src_t.shape[1:]) != tuple(tgt_t.shape[1:]):
                continue
            rows = min(int(old_nc), int(new_nc))
            merged = tgt_t.clone()
            merged[:rows] = src_t[:rows]
            filtered_src_state[key] = merged
    # head_init_mode == "fresh" (default): all shape-mismatched head tensors
    # are skipped entirely and keep their new random init — the champion
    # Model-5 Resume-and-Adapt approach.

    target.load_state_dict(filtered_src_state, strict=False)
    return target


def _set_surgery_fields(job_id: str, **fields) -> None:
    """Direct SQL for platform columns not covered by training_db helpers."""
    if not fields:
        return
    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values()) + [job_id]
    conn = get_db()
    try:
        conn.execute(f"UPDATE training_jobs SET {assignments} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def start_surgery(
    source_checkpoint_id: str,
    taxonomy_id: str,
    head_init_mode: str = "fresh",
) -> str:
    source = checkpoint_registry.get_checkpoint(source_checkpoint_id)
    if not source["exists"]:
        raise ValueError(f"source checkpoint file missing on disk: {source['path']}")
    taxonomy = taxonomy_service.get_taxonomy(taxonomy_id)
    classes = taxonomy["class_names"]
    if not classes:
        raise ValueError("taxonomy has no class names")
    try:
        stage = StageType(taxonomy["stage"])
    except ValueError as exc:
        raise ValueError(f"unsupported taxonomy stage: {taxonomy['stage']}") from exc

    job = TrainingJob(
        stage=stage,
        status=JobStatus.PENDING,
        dataset_path="n/a",
        base_model=source["path"],
        device="cpu",
        project_name="surgery",
        run_name=f"head_surgery_{uuid.uuid4().hex[:8]}",
        overrides={
            "job_type": "surgery",
            "source_checkpoint_id": source_checkpoint_id,
            "taxonomy_id": taxonomy_id,
            "head_init_mode": head_init_mode,
        },
    )
    training_db.insert_job(job)
    _set_surgery_fields(job.id, job_type="surgery", status="queued")

    thread = threading.Thread(
        target=_run,
        args=(job.id, source, taxonomy, head_init_mode),
        daemon=True,
    )
    thread.start()
    logger.info(
        "Surgery job %s queued (%s -> nc=%d)",
        job.id,
        source["name"],
        len(classes),
    )
    return job.id


def _run(job_id: str, source: dict, taxonomy: dict, head_init_mode: str) -> None:
    classes = taxonomy["class_names"]
    new_nc = len(classes)
    try:
        training_db.update_job_status(job_id, JobStatus.RUNNING, started_at=_now_iso())

        target = _remap_head(source["path"], new_nc, head_init_mode)

        raw_ckpt = _torch_load(source["path"])
        payload = {}
        if isinstance(raw_ckpt, dict):
            payload.update(raw_ckpt)
        # Drop training-state objects not needed for a remapped init ckpt.
        payload.pop("optimizer", None)
        payload.pop("ema", None)
        payload.pop("best_fitness", None)
        payload["model"] = target
        payload["nc"] = new_nc
        payload["epoch"] = 0

        out_dir = SURGERY_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"remapped_{new_nc}cls.pt"
        torch.save(payload, out_path)

        # Verify the saved checkpoint can be loaded by YOLO.
        check = YOLO(str(out_path))
        logger.info(
            "Surgery %s: saved %s (loaded nc=%s)",
            job_id,
            out_path,
            getattr(check.model, "nc", "unknown"),
        )

        checkpoint = checkpoint_registry.register_checkpoint(
            name=f"{source['name']}_remapped_{new_nc}cls",
            path=str(out_path),
            origin="surgery",
            stage=taxonomy["stage"],
            nc=new_nc,
            class_names=classes,
            architecture=source.get("architecture"),
            source_checkpoint_id=source["id"],
            notes=f"Head surgery from {source['name']} (mode={head_init_mode})",
        )

        training_db.update_job_status(
            job_id, JobStatus.COMPLETED, completed_at=_now_iso()
        )
        _set_surgery_fields(job_id, output_checkpoint_id=checkpoint["id"])
        logger.info("Surgery job %s completed", job_id)
    except Exception as exc:
        logger.exception("Surgery job %s failed", job_id)
        training_db.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=str(exc),
            completed_at=_now_iso(),
        )


def get_status(job_id: str) -> SurgeryStatusResponse:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, status, error_message, output_checkpoint_id, job_type "
            "FROM training_jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None or row["job_type"] != "surgery":
        raise SurgeryJobNotFoundError(job_id)
    return SurgeryStatusResponse(
        job_id=row["id"],
        status=row["status"],
        error_message=row["error_message"],
        output_checkpoint_id=row["output_checkpoint_id"],
    )
