"""CRUD service for the taxonomy entity.

A taxonomy is an ordered, editable class list bound to a stage.
Part of the Stage 2 Training Platform (Phase A).
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from services.platform_db import get_db

logger = logging.getLogger(__name__)

# Champion Stage 2 taxonomy (locked per docs/champion_manifest_verified.md)
DEFAULT_STAGE2_CLASSES = [
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "broken_lamp",
    "corrosion",
    "disjoint_part",
]


class TaxonomyValidationError(ValueError):
    pass


class TaxonomyNotFoundError(LookupError):
    pass


class TaxonomyInUseError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_class_names(class_names: list[str]) -> list[str]:
    """Normalize and validate: non-empty, no blanks, no case-insensitive duplicates."""
    if not class_names:
        raise TaxonomyValidationError("class_names must not be empty")
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in class_names:
        if not isinstance(raw, str):
            raise TaxonomyValidationError("each class name must be a string")
        name = raw.strip()
        if not name:
            raise TaxonomyValidationError("class names must not be blank")
        key = name.lower()
        if key in seen:
            raise TaxonomyValidationError(f"duplicate class name: {name}")
        seen.add(key)
        cleaned.append(name)
    return cleaned


def _row_to_taxonomy(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "stage": row["stage"],
        "class_names": json.loads(row["class_names"]),
        "description": row["description"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_taxonomies(stage: Optional[str] = None) -> list[dict]:
    conn = get_db()
    try:
        if stage:
            rows = conn.execute(
                "SELECT * FROM taxonomies WHERE stage = ? ORDER BY created_at",
                (stage,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM taxonomies ORDER BY created_at"
            ).fetchall()
        return [_row_to_taxonomy(r) for r in rows]
    finally:
        conn.close()


def get_taxonomy(taxonomy_id: str) -> dict:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM taxonomies WHERE id = ?", (taxonomy_id,)
        ).fetchone()
        if row is None:
            raise TaxonomyNotFoundError(taxonomy_id)
        return _row_to_taxonomy(row)
    finally:
        conn.close()


def create_taxonomy(
    name: str,
    stage: str,
    class_names: list[str],
    description: Optional[str] = None,
) -> dict:
    cleaned = _validate_class_names(class_names)
    taxonomy_id = str(uuid.uuid4())
    now = _now_iso()
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO taxonomies
                (id, name, stage, class_names, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                taxonomy_id,
                name.strip(),
                stage,
                json.dumps(cleaned),
                description,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("Created taxonomy %s (%s, %d classes)", name, stage, len(cleaned))
    return get_taxonomy(taxonomy_id)


def update_taxonomy(
    taxonomy_id: str,
    name: Optional[str] = None,
    class_names: Optional[list[str]] = None,
    description: Optional[str] = None,
) -> dict:
    existing = get_taxonomy(taxonomy_id)  # raises if missing
    new_name = name.strip() if name is not None else existing["name"]
    new_classes = (
        _validate_class_names(class_names)
        if class_names is not None
        else existing["class_names"]
    )
    new_description = (
        description if description is not None else existing["description"]
    )
    conn = get_db()
    try:
        conn.execute(
            """
            UPDATE taxonomies
            SET name = ?, class_names = ?, description = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                new_name,
                json.dumps(new_classes),
                new_description,
                _now_iso(),
                taxonomy_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return get_taxonomy(taxonomy_id)


def delete_taxonomy(taxonomy_id: str) -> None:
    get_taxonomy(taxonomy_id)  # raises if missing
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM recipes WHERE taxonomy_id = ?",
            (taxonomy_id,),
        ).fetchone()
        if row and row["n"] > 0:
            raise TaxonomyInUseError(
                f"taxonomy {taxonomy_id} is referenced by {row['n']} recipe(s)"
            )
        conn.execute("DELETE FROM taxonomies WHERE id = ?", (taxonomy_id,))
        conn.commit()
    finally:
        conn.close()
    logger.info("Deleted taxonomy %s", taxonomy_id)


def ensure_default_taxonomies() -> None:
    """Idempotently seed the locked champion Stage 2 7-class taxonomy."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM taxonomies "
            "WHERE name = ? AND stage = 'stage2'",
            ("stage2_7class_defects",),
        ).fetchone()
        if row and row["n"] > 0:
            return
    finally:
        conn.close()
    create_taxonomy(
        name="stage2_7class_defects",
        stage="stage2",
        class_names=list(DEFAULT_STAGE2_CLASSES),
        description="Champion Stage 2 taxonomy (locked per champion manifest).",
    )
    logger.info("Seeded default Stage 2 7-class taxonomy")
