"""Async batch job queue: SQLite-backed job store + bounded thread pool.

Jobs are durable: metadata lives in SQLite (``storage/jobs/jobs.db``) and each
job's results are written to ``storage/jobs/{job_id}/results.json``. Inference is
GPU-bound, so the pool is bounded (default 1 worker) to avoid GPU memory
contention; additional batch requests queue behind running ones.
"""
import json
import logging
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings

logger = logging.getLogger("job_queue")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobQueue:
    def __init__(self, max_workers: int = 1):
        settings.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = settings.jobs_dir / "jobs.db"
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._write_lock = threading.Lock()
        self._init_db()

    # ------------------------------------------------------------- schema

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    preset TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    error TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------- lifecycle

    def create_job(self, total: int, preset: str) -> str:
        job_id = (
            f"JOB_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        )
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, status, total, completed, preset, "
                "created_at, updated_at) VALUES (?, 'queued', ?, 0, ?, ?, ?)",
                (job_id, total, preset, _now(), _now()),
            )
        return job_id

    def get_job(self, job_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if row is None:
            return None
        job = dict(row)
        results_path = settings.jobs_dir / job_id / "results.json"
        job["results"] = (
            json.loads(results_path.read_text())
            if job["status"] == "done" and results_path.exists()
            else None
        )
        return job

    def list_jobs(self, limit: int = 20) -> List[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT job_id, status, total, completed, preset, created_at, "
                "updated_at, error FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------- transitions

    def _set(self, job_id: str, **fields) -> None:
        fields["updated_at"] = _now()
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._write_lock, self._connect() as conn:
            conn.execute(
                f"UPDATE jobs SET {cols} WHERE job_id = ?",
                (*fields.values(), job_id),
            )

    def mark_running(self, job_id: str) -> None:
        self._set(job_id, status="running")

    def increment_completed(self, job_id: str) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET completed = completed + 1, updated_at = ? "
                "WHERE job_id = ?",
                (_now(), job_id),
            )

    def mark_done(self, job_id: str, results: list) -> None:
        out_dir = settings.jobs_dir / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "results.json").write_text(json.dumps(results))
        self._set(job_id, status="done", completed=len(results))

    def mark_failed(self, job_id: str, error: str) -> None:
        self._set(job_id, status="failed", error=error)

    # ------------------------------------------------------------- execution

    def submit(self, fn) -> None:
        """Submit a no-arg callable that performs the batch work."""
        self._executor.submit(fn)


job_queue = JobQueue(max_workers=settings.max_workers)
