"""Checkpoint registry for the Stage 2 Training Platform (Phase A).

A checkpoint is any .pt weights file with tracked lineage.
Origins: native_coco (stock COCO pretrain) | trained (from a job) | surgery (Phase C).
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from services.platform_db import get_db

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

# Stock COCO pretrained weights expected at repo root
NATIVE_COCO_ROOTS = {
    "yolo26m-seg.pt": "yolo26m-seg",
    "yolo11n-seg.pt": "yolo11n-seg",
}


class CheckpointNotFoundError(LookupError):
    pass


class CheckpointInUseError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_info(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return {"exists": True, "size_mb": round(p.stat().st_size / (1024 * 1024), 2)}
    return {"exists": False, "size_mb": None}


def _row_to_checkpoint(row) -> dict:
    data = {
        "id": row["id"],
        "name": row["name"],
        "path": row["path"],
        "origin": row["origin"],
        "source_checkpoint_id": row["source_checkpoint_id"],
        "source_job_id": row["source_job_id"],
        "stage": row["stage"],
        "nc": row["nc"],
        "class_names": json.loads(row["class_names"]) if row["class_names"] else None,
        "architecture": row["architecture"],
        "created_at": row["created_at"],
        "notes": row["notes"],
    }
    data.update(_file_info(row["path"]))
    return data


def _guess_stage(rel_path: str) -> str:
    low = rel_path.lower()
    if "stage3" in low or "panel" in low:
        return "stage3"
    if "stage2" in low or "head_warmup" in low or "differential" in low:
        return "stage2"
    if "stage1" in low or "sod" in low:
        return "stage1"
    return "unknown"


def list_checkpoints(stage: Optional[str] = None) -> list[dict]:
    conn = get_db()
    try:
        if stage:
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE stage IN (?, 'any') "
                "ORDER BY created_at",
                (stage,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM checkpoints ORDER BY created_at"
            ).fetchall()
        return [_row_to_checkpoint(r) for r in rows]
    finally:
        conn.close()


def get_checkpoint(checkpoint_id: str) -> dict:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        if row is None:
            raise CheckpointNotFoundError(checkpoint_id)
        return _row_to_checkpoint(row)
    finally:
        conn.close()


def register_checkpoint(
    name: str,
    path: str,
    origin: str = "trained",
    stage: str = "stage2",
    nc: int = 0,
    class_names: Optional[list[str]] = None,
    architecture: Optional[str] = None,
    source_checkpoint_id: Optional[str] = None,
    source_job_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    checkpoint_id = str(uuid.uuid4())
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO checkpoints
                (id, name, path, origin, source_checkpoint_id, source_job_id,
                 stage, nc, class_names, architecture, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                checkpoint_id,
                name.strip(),
                str(Path(path).resolve()),
                origin,
                source_checkpoint_id,
                source_job_id,
                stage,
                nc,
                json.dumps(class_names) if class_names else None,
                architecture,
                _now_iso(),
                notes,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("Registered checkpoint %s (%s)", name, origin)
    return get_checkpoint(checkpoint_id)


def _extract_nc_from_pt(path: Path) -> int:
    """Safely extract class count (nc) from an Ultralytics .pt checkpoint."""
    try:
        import torch

        # weights_only=False is required for Ultralytics custom classes in PyTorch 2.6+
        ckpt = torch.load(str(path), map_location="cpu", weights_only=False)
        model = ckpt.get("model", ckpt) if isinstance(ckpt, dict) else ckpt
        if hasattr(model, "nc") and model.nc is not None:
            return int(model.nc)
        if hasattr(model, "names") and model.names is not None:
            return len(model.names)
    except Exception:
        pass
    return 0


def _collect_candidates() -> list[dict]:
    candidates: list[dict] = []
    for fname, arch in NATIVE_COCO_ROOTS.items():
        p = REPO_ROOT / fname
        if p.exists():
            candidates.append(
                {
                    "name": fname,
                    "path": str(p.resolve()),
                    "origin": "native_coco",
                    "stage": "any",
                    "nc": 80,
                    "architecture": arch,
                    "notes": "Stock COCO pretrained weights",
                }
            )
    runs_dir = REPO_ROOT / "runs"
    if runs_dir.exists():
        for p in sorted(runs_dir.rglob("weights/*.pt")):
            rel = p.relative_to(REPO_ROOT).as_posix()
            parts = rel.split("/")
            run_name = parts[2] if len(parts) > 3 else p.parent.parent.name
            candidates.append(
                {
                    "name": f"{run_name}/{p.name}",
                    "path": str(p.resolve()),
                    "origin": "trained",
                    "stage": _guess_stage(rel),
                    "nc": _extract_nc_from_pt(p),
                    "architecture": None,
                    "notes": None,
                }
            )
    return candidates


def scan_filesystem() -> dict:
    """Idempotently register native COCO roots + runs/**/weights/*.pt."""
    candidates = _collect_candidates()
    registered = 0
    skipped = 0
    conn = get_db()
    try:
        known = {
            r["path"] for r in conn.execute("SELECT path FROM checkpoints").fetchall()
        }
        for c in candidates:
            if c["path"] in known:
                skipped += 1
                continue
            conn.execute(
                """
                INSERT INTO checkpoints
                    (id, name, path, origin, source_checkpoint_id, source_job_id,
                     stage, nc, class_names, architecture, created_at, notes)
                VALUES (?, ?, ?, ?, NULL, NULL, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    c["name"],
                    c["path"],
                    c["origin"],
                    c["stage"],
                    c["nc"],
                    c["architecture"],
                    _now_iso(),
                    c["notes"],
                ),
            )
            registered += 1
        conn.commit()
    finally:
        conn.close()
    logger.info("Checkpoint scan: %d registered, %d skipped", registered, skipped)
    return {"registered": registered, "skipped": skipped}


def ensure_native_checkpoints() -> None:
    """Idempotent startup seed: native COCO roots only (no full scan)."""
    conn = get_db()
    try:
        known = {
            r["path"] for r in conn.execute("SELECT path FROM checkpoints").fetchall()
        }
        for fname, arch in NATIVE_COCO_ROOTS.items():
            p = REPO_ROOT / fname
            if not p.exists():
                continue
            path = str(p.resolve())
            if path in known:
                continue
            conn.execute(
                """
                INSERT INTO checkpoints
                    (id, name, path, origin, source_checkpoint_id, source_job_id,
                     stage, nc, class_names, architecture, created_at, notes)
                VALUES (?, ?, ?, 'native_coco', NULL, NULL, 'any', 80, NULL, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    fname,
                    path,
                    arch,
                    _now_iso(),
                    "Stock COCO pretrained weights",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def delete_checkpoint(checkpoint_id: str) -> None:
    get_checkpoint(checkpoint_id)  # raises if missing
    conn = get_db()
    try:
        for table, col in (
            ("recipes", "base_checkpoint_id"),
            ("chain_steps", "base_checkpoint_id"),
            ("checkpoints", "source_checkpoint_id"),
        ):
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE {col} = ?",
                (checkpoint_id,),
            ).fetchone()
            if row and row["n"] > 0:
                raise CheckpointInUseError(
                    f"checkpoint {checkpoint_id} is referenced by {table}"
                )
        conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
        conn.commit()
    finally:
        conn.close()
    logger.info("Deleted checkpoint %s", checkpoint_id)
