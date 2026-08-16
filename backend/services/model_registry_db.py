import json
import sqlite3
from typing import List, Optional

from core.config import settings
from schemas.model_registry import ModelStatus, ModelVersion, StageType

DB_PATH = settings.workspace_root / "backend" / "data" / "model_registry.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    stage TEXT NOT NULL,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate',
    weights_path TEXT NOT NULL,
    config_hash TEXT,
    dataset_version TEXT,
    training_run_id TEXT,
    metrics_json TEXT NOT NULL DEFAULT '{}',
    evaluation_report_json TEXT NOT NULL DEFAULT '{}',
    model_card TEXT,
    created_at TEXT NOT NULL,
    promoted_at TEXT,
    deployed_at TEXT
);
"""


class ModelRegistryDB:
    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def insert(self, model: ModelVersion) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO models (
                    id, stage, model_name, version, status,
                    weights_path, config_hash, dataset_version,
                    training_run_id, metrics_json, evaluation_report_json,
                    model_card, created_at, promoted_at, deployed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model.id,
                    model.stage.value,
                    model.model_name,
                    model.version,
                    model.status.value,
                    model.weights_path,
                    model.config_hash,
                    model.dataset_version,
                    model.training_run_id,
                    json.dumps(model.metrics),
                    json.dumps(model.evaluation_report),
                    model.model_card,
                    model.created_at,
                    model.promoted_at,
                    model.deployed_at,
                ),
            )

    def get_by_id(self, model_id: str) -> Optional[ModelVersion]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE id = ?", (model_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def list_models(
        self,
        stage: Optional[StageType] = None,
        status: Optional[ModelStatus] = None,
    ) -> List[ModelVersion]:
        query = "SELECT * FROM models WHERE 1=1"
        params: list = []
        if stage is not None:
            query += " AND stage = ?"
            params.append(stage.value)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get_champion(self, stage: StageType) -> Optional[ModelVersion]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE stage = ? AND status = 'champion' ORDER BY promoted_at DESC LIMIT 1",
                (stage.value,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def get_deployed(self, stage: StageType) -> Optional[ModelVersion]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM models WHERE stage = ? AND status = 'deployed' ORDER BY deployed_at DESC LIMIT 1",
                (stage.value,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def get_previous_deployed(
        self, stage: StageType, exclude_id: str
    ) -> Optional[ModelVersion]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM models
                WHERE stage = ? AND status = 'deployed' AND id != ?
                ORDER BY deployed_at DESC LIMIT 1
                """,
                (stage.value, exclude_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def update_status(
        self,
        model_id: str,
        status: ModelStatus,
        promoted_at: Optional[str] = None,
        deployed_at: Optional[str] = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE models
                SET status = ?, promoted_at = COALESCE(?, promoted_at),
                    deployed_at = COALESCE(?, deployed_at)
                WHERE id = ?
                """,
                (status.value, promoted_at, deployed_at, model_id),
            )

    def update_evaluation_report(self, model_id: str, report: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE models SET evaluation_report_json = ? WHERE id = ?",
                (json.dumps(report), model_id),
            )

    def _row_to_model(self, row: sqlite3.Row) -> ModelVersion:
        return ModelVersion(
            id=row["id"],
            stage=StageType(row["stage"]),
            model_name=row["model_name"],
            version=row["version"],
            status=ModelStatus(row["status"]),
            weights_path=row["weights_path"],
            config_hash=row["config_hash"],
            dataset_version=row["dataset_version"],
            training_run_id=row["training_run_id"],
            metrics=json.loads(row["metrics_json"]),
            evaluation_report=json.loads(row["evaluation_report_json"]),
            model_card=row["model_card"],
            created_at=row["created_at"],
            promoted_at=row["promoted_at"],
            deployed_at=row["deployed_at"],
        )


model_registry_db = ModelRegistryDB()
