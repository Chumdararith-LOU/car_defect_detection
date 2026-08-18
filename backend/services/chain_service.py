"""Chain orchestration for the Stage 2 Training Platform (Phase F).

A chain executes ordered recipe steps sequentially; a step can consume the
previous step's best checkpoint (previous_step_best handoff).
Chain run state is in-memory; the underlying jobs persist in training_jobs.
"""

import logging
import re
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Optional

from schemas.training import LaunchRequest, StageType
from services import checkpoint_registry, recipe_service
from services.dataset_registry import get_dataset_detail
from services.platform_db import get_db
from services.recipe_config_builder import build_config_from_recipe
from services.training_db import training_db
from services.training_worker import worker

logger = logging.getLogger(__name__)

_RUNS: Dict[str, dict] = {}
_LOCK = threading.Lock()


class ChainNotFoundError(LookupError):
    pass


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------------- CRUD ----------------


def list_chains() -> list:
    conn = get_db()
    try:
        chains = [
            dict(r)
            for r in conn.execute("SELECT * FROM chains ORDER BY created_at").fetchall()
        ]
        steps = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM chain_steps ORDER BY order_index"
            ).fetchall()
        ]
    finally:
        conn.close()
    by_chain: Dict[str, list] = {}
    for s in steps:
        by_chain.setdefault(s["chain_id"], []).append(s)
    for c in chains:
        c["steps"] = by_chain.get(c["id"], [])
    return chains


def get_chain(chain_id: str) -> dict:
    for c in list_chains():
        if c["id"] == chain_id:
            return c
    raise ChainNotFoundError(chain_id)


def create_chain(
    name: str,
    stage: str,
    description: Optional[str],
    steps: list,
) -> dict:
    chain_id = str(uuid.uuid4())
    conn = get_db()
    try:
        for st in steps:  # validate recipes exist before inserting
            recipe_service.get_recipe(st["recipe_id"])
        conn.execute(
            "INSERT INTO chains (id, name, stage, description, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (chain_id, name.strip(), stage, description, _now_iso()),
        )
        for i, st in enumerate(steps):
            conn.execute(
                """
                INSERT INTO chain_steps
                    (id, chain_id, order_index, recipe_id, dataset_id,
                     base_source, base_checkpoint_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    chain_id,
                    st.get("order_index", i),
                    st["recipe_id"],
                    st["dataset_id"],
                    st.get("base_source", "recipe_default"),
                    st.get("base_checkpoint_id"),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    logger.info("Created chain %s (%d steps)", name, len(steps))
    return get_chain(chain_id)


def delete_chain(chain_id: str) -> None:
    get_chain(chain_id)
    conn = get_db()
    try:
        conn.execute("DELETE FROM chain_steps WHERE chain_id = ?", (chain_id,))
        conn.execute("DELETE FROM chains WHERE id = ?", (chain_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------- Orchestration ----------------


def _resolve_base(
    step: dict, recipe: dict, prev_output_checkpoint_id: Optional[str]
) -> Optional[str]:
    src = step["base_source"]
    if src == "previous_step_best":
        if not prev_output_checkpoint_id:
            raise ValueError("previous_step_best requested but no previous step output")
        return prev_output_checkpoint_id
    if src == "specific_checkpoint":
        if not step["base_checkpoint_id"]:
            raise ValueError(
                "specific_checkpoint requested but base_checkpoint_id not set"
            )
        return step["base_checkpoint_id"]
    return recipe.get("base_checkpoint_id")


def _set_job_chain_meta(
    job_id: str,
    chain_id: str,
    step_index: int,
    parent_job_id: Optional[str],
) -> None:
    conn = get_db()
    try:
        conn.execute(
            "UPDATE training_jobs SET job_type = 'chain_step', chain_id = ?, "
            "chain_step_index = ?, parent_job_id = ? WHERE id = ?",
            (chain_id, step_index, parent_job_id, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def _wait_for_job(job_id: str, timeout_s: int = 4 * 3600, poll_s: float = 3.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        job = training_db.get_job(job_id)
        if job and job.status.value in ("completed", "failed", "cancelled"):
            return job
        time.sleep(poll_s)
    raise RuntimeError(f"job {job_id} timed out")


def start_chain_run(chain_id: str) -> str:
    chain = get_chain(chain_id)
    if not chain["steps"]:
        raise ValueError("chain has no steps")
    run_id = str(uuid.uuid4())
    with _LOCK:
        _RUNS[run_id] = {
            "run_id": run_id,
            "chain_id": chain_id,
            "status": "running",
            "current_step": 0,
            "jobs": [],
            "error": None,
        }
    threading.Thread(target=_run_chain, args=(run_id, chain), daemon=True).start()
    return run_id


def _run_chain(run_id: str, chain: dict) -> None:
    prev_output_checkpoint_id: Optional[str] = None
    prev_job_id: Optional[str] = None
    try:
        for idx, step in enumerate(chain["steps"]):
            with _LOCK:
                _RUNS[run_id]["current_step"] = idx
            recipe = recipe_service.get_recipe(step["recipe_id"])
            dataset = get_dataset_detail(step["dataset_id"])
            if not dataset:
                raise ValueError(f"dataset not found: {step['dataset_id']}")

            # Convert Pydantic model to dict for uniform access
            dataset_dict = (
                dataset.model_dump() if hasattr(dataset, "model_dump") else dataset
            )

            base_id = _resolve_base(step, recipe, prev_output_checkpoint_id)
            checkpoint = checkpoint_registry.get_checkpoint(base_id)
            if not checkpoint.get("exists"):
                raise ValueError(f"step {idx}: base checkpoint missing on disk")

            safe = re.sub(r"[^A-Za-z0-9_-]+", "_", chain["name"]).strip("_") or "chain"
            run_name = f"{safe}_s{idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            config = build_config_from_recipe(
                recipe, dataset_dict["yaml_path"], checkpoint["path"], run_name
            )
            request = LaunchRequest(
                stage=StageType(recipe["stage"]),
                dataset_path=dataset_dict["yaml_path"],
                dataset_id=step["dataset_id"],
                recipe_id=recipe["id"],
                base_checkpoint_id=base_id,
                project_name=safe,
                run_name=run_name,
            )
            job = worker.launch(request, config_dict=config)
            _set_job_chain_meta(job.id, chain["id"], idx, prev_job_id)
            with _LOCK:
                _RUNS[run_id]["jobs"].append(
                    {"step_index": idx, "job_id": job.id, "status": "running"}
                )

            final = _wait_for_job(job.id)
            if final.status.value != "completed":
                raise RuntimeError(
                    f"step {idx} job {job.id} {final.status.value}: "
                    f"{final.error_message}"
                )
            prev_output_checkpoint_id = final.output_checkpoint_id
            prev_job_id = job.id
        with _LOCK:
            _RUNS[run_id]["status"] = "completed"
        logger.info("Chain run %s completed", run_id)
    except Exception as exc:
        logger.exception("Chain run %s failed", run_id)
        with _LOCK:
            _RUNS[run_id]["status"] = "failed"
            _RUNS[run_id]["error"] = str(exc)


def get_run_status(run_id: str) -> dict:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is None:
            raise LookupError(run_id)
        jobs = []
        for j in run["jobs"]:
            job = training_db.get_job(j["job_id"])
            jobs.append({**j, "status": job.status.value if job else j["status"]})
        return {**run, "jobs": jobs}


# ---------------- Seeding ----------------


def seed_champion_chain() -> None:
    """Idempotently seed the Stage 2 Resume-and-Adapt champion chain."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM chains WHERE name = ?",
            ("Stage 2 Resume-and-Adapt Champion",),
        ).fetchone()
        if row and row["n"] > 0:
            return
    finally:
        conn.close()

    presets = {r["name"]: r for r in recipe_service.list_recipes(presets_only=True)}
    warmup = presets.get("Head-Only Warmup")
    difflr = presets.get("Differential LR Fine-tune")
    if not warmup or not difflr:
        logger.warning("Champion chain not seeded: presets missing")
        return

    surgery_id = None
    for c in checkpoint_registry.list_checkpoints():
        if c["origin"] == "surgery" and c.get("exists"):
            surgery_id = c["id"]
            break

    dataset_id = "yolo_seg_clean_2200_7cls"
    steps = [
        {
            "order_index": 0,
            "recipe_id": warmup["id"],
            "dataset_id": dataset_id,
            "base_source": "specific_checkpoint" if surgery_id else "recipe_default",
            "base_checkpoint_id": surgery_id,
        },
        {
            "order_index": 1,
            "recipe_id": difflr["id"],
            "dataset_id": dataset_id,
            "base_source": "previous_step_best",
            "base_checkpoint_id": None,
        },
    ]
    create_chain(
        name="Stage 2 Resume-and-Adapt Champion",
        stage="stage2",
        description=(
            "Head-only warmup (from surgery output) then differential LR "
            "fine-tune. One-click re-run of the champion recipe."
        ),
        steps=steps,
    )
    logger.info("Seeded champion chain")
