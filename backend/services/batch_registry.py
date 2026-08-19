"""Batch registry: groups saved inspections into named runs (batches).
Stored as a single JSON manifest at backend/data/batches.json."""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BATCHES_FILE = PROJECT_ROOT / "backend" / "data" / "batches.json"

_lock = threading.Lock()


def _load() -> list[dict]:
    if not BATCHES_FILE.exists():
        return []
    try:
        with open(BATCHES_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"Failed to read batches.json: {e}")
        return []


def _save(batches: list[dict]) -> None:
    BATCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BATCHES_FILE, "w") as f:
        json.dump(batches, f, indent=2)


def _default_name(count: int) -> str:
    return f"{datetime.now():%b %d, %H:%M} · {count} image{'s' if count != 1 else ''}"


def create_batch(
    inspection_ids: list[str],
    name: str | None = None,
    settings: dict | None = None,
) -> dict:
    """Register a new batch; stats computed from saved payloads."""
    from services.inspection_store import load_inspection

    if not inspection_ids:
        raise ValueError("inspection_ids must not be empty")

    fail = 0
    passed = 0
    total_defects = 0
    for insp_id in inspection_ids:
        payload = load_inspection(insp_id)
        if not payload:
            continue
        status = payload.get("inspection_status", "UNKNOWN")
        if status == "FAIL":
            fail += 1
        elif status == "PASS":
            passed += 1
        total_defects += len(payload.get("defects", []))

    with _lock:
        batches = _load()
        base_id = f"BATCH_{datetime.now():%Y%m%d%H%M%S}"
        batch_id = base_id
        suffix = 2
        while any(b.get("batch_id") == batch_id for b in batches):
            batch_id = f"{base_id}_{suffix}"
            suffix += 1
        batch = {
            "batch_id": batch_id,
            "name": name or _default_name(len(inspection_ids)),
            "created_at": datetime.now().isoformat(),
            "count": len(inspection_ids),
            "fail_count": fail,
            "pass_count": passed,
            "total_defects": total_defects,
            "settings": settings or {},
            "inspection_ids": inspection_ids,
        }
        batches.insert(0, batch)  # newest first
        _save(batches)
    return batch


def list_batches() -> list[dict]:
    return _load()


def get_batch(batch_id: str) -> dict | None:
    for b in _load():
        if b.get("batch_id") == batch_id:
            return b
    return None


def rename_batch(batch_id: str, new_name: str) -> dict:
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("Batch name must not be empty")
    with _lock:
        batches = _load()
        for b in batches:
            if b.get("batch_id") == batch_id:
                b["name"] = new_name
                _save(batches)
                return b
    raise ValueError(f"Batch '{batch_id}' not found")
