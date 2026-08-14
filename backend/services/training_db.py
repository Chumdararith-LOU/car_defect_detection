import sqlite3
import json
from typing import List, Optional
from core.config import settings
from schemas.training import TrainingJob, JobStatus

DB_DIR = settings.workspace_root / "backend" / "data"
DB_PATH = DB_DIR / "training_jobs.db"


class TrainingDB:
    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS training_jobs (
                    id TEXT PRIMARY KEY,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dataset_path TEXT NOT NULL,
                    config_path TEXT,
                    base_model TEXT,
                    device TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    run_name TEXT NOT NULL,
                    overrides TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    log_file TEXT,
                    mlflow_run_id TEXT,
                    error_message TEXT
                )
            """)

    def insert_job(self, job: TrainingJob) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO training_jobs (
                    id, stage, status, dataset_path, config_path, base_model, device,
                    project_name, run_name, overrides, created_at, started_at, completed_at,
                    log_file, mlflow_run_id, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job.id,
                    job.stage.value,
                    job.status.value,
                    job.dataset_path,
                    job.config_path,
                    job.base_model,
                    job.device,
                    job.project_name,
                    job.run_name,
                    json.dumps(job.overrides),
                    job.created_at,
                    job.started_at,
                    job.completed_at,
                    job.log_file,
                    job.mlflow_run_id,
                    job.error_message,
                ),
            )

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        mlflow_run_id: Optional[str] = None,
    ) -> None:
        with self.conn:
            self.conn.execute(
                """
                UPDATE training_jobs
                SET status = ?, error_message = ?, started_at = COALESCE(?, started_at),
                    completed_at = COALESCE(?, completed_at), mlflow_run_id = COALESCE(?, mlflow_run_id)
                WHERE id = ?
            """,
                (
                    status.value,
                    error_message,
                    started_at,
                    completed_at,
                    mlflow_run_id,
                    job_id,
                ),
            )

    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        cursor = self.conn.execute(
            "SELECT * FROM training_jobs WHERE id = ?", (job_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_jobs(self, limit: int = 50, offset: int = 0) -> List[TrainingJob]:
        cursor = self.conn.execute(
            "SELECT * FROM training_jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [self._row_to_job(row) for row in cursor.fetchall()]

    def count_jobs(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) FROM training_jobs")
        return cursor.fetchone()[0]

    def _row_to_job(self, row: sqlite3.Row) -> TrainingJob:
        data = dict(row)
        data["overrides"] = json.loads(data["overrides"])
        return TrainingJob.model_validate(data)


training_db = TrainingDB()
