import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "reviews.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id TEXT NOT NULL,
    defect_id TEXT,
    model_version TEXT,
    predicted_class TEXT,
    predicted_panel TEXT,
    operator_decision TEXT NOT NULL,
    corrected_class TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT = """
INSERT INTO reviews (
    inspection_id, defect_id, model_version, predicted_class,
    predicted_panel, operator_decision, corrected_class, notes
) VALUES (
    :inspection_id, :defect_id, :model_version, :predicted_class,
    :predicted_panel, :operator_decision, :corrected_class, :notes
)
"""

_UPDATABLE_COLUMNS = ("operator_decision", "corrected_class", "notes")


class ReviewDB:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as conn:
            cursor = conn.execute(_INSERT, data)
            row = conn.execute(
                "SELECT * FROM reviews WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def list_reviews(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM reviews ORDER BY id DESC"
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reviews WHERE id = ?", (review_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def delete_review(self, review_id: int) -> bool:
        """Deletes a review by ID. Returns True if a row was deleted."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_review(
        self, review_id: int, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if self.get_review(review_id) is None:
            return None
        filtered = {
            column: value
            for column, value in updates.items()
            if column in _UPDATABLE_COLUMNS and value is not None
        }
        if filtered:
            set_clause = ", ".join(f"{column} = ?" for column in filtered)
            params = tuple(filtered.values()) + (review_id,)
            with self._connect() as conn:
                conn.execute(f"UPDATE reviews SET {set_clause} WHERE id = ?", params)
        return self.get_review(review_id)


review_db = ReviewDB()
