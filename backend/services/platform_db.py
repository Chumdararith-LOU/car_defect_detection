"""
Platform database schema for Stage 2 Training Platform.
Extends training_jobs.db with taxonomy, checkpoint, recipe, and chain tables.
"""

import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# DB path (same as training_jobs)
DB_PATH = Path(__file__).parent.parent / "data" / "training_jobs.db"


def get_db() -> sqlite3.Connection:
    """Get DB connection with foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_platform_tables():
    """Create platform tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. taxonomies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS taxonomies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            stage TEXT NOT NULL CHECK (stage IN ('stage1', 'stage2', 'stage3')),
            class_names TEXT NOT NULL,  -- JSON array
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 2. checkpoints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            origin TEXT NOT NULL CHECK (origin IN ('native_coco', 'trained', 'surgery')),
            source_checkpoint_id TEXT,
            source_job_id TEXT,
            stage TEXT NOT NULL,
            nc INTEGER NOT NULL,
            class_names TEXT,  -- JSON array (for surgery outputs)
            architecture TEXT,
            created_at TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (source_checkpoint_id) REFERENCES checkpoints(id),
            FOREIGN KEY (source_job_id) REFERENCES training_jobs(id)
        )
    """)

    # 3. recipes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            stage TEXT NOT NULL,
            taxonomy_id TEXT NOT NULL,
            description TEXT,
            base_strategy TEXT NOT NULL CHECK (base_strategy IN ('native_coco', 'from_checkpoint', 'from_previous_step')),
            base_checkpoint_id TEXT,
            freeze_mode TEXT NOT NULL CHECK (freeze_mode IN ('none', 'freeze_n', 'head_only')),
            freeze_layers INTEGER,
            lr_mode TEXT NOT NULL CHECK (lr_mode IN ('uniform', 'differential')),
            split_layer_idx INTEGER,
            backbone_lr_mult REAL,
            loss_type TEXT NOT NULL CHECK (loss_type IN ('bce', 'focal', 'ce')),
            fl_gamma REAL,
            fl_alpha REAL,
            fl_scale REAL,
            imgsz INTEGER NOT NULL,
            batch_size INTEGER NOT NULL,
            epochs INTEGER NOT NULL,
            optimizer TEXT NOT NULL,
            lr0 REAL NOT NULL,
            lrf REAL NOT NULL,
            patience INTEGER,
            augmentations TEXT,  -- JSON
            is_preset BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (taxonomy_id) REFERENCES taxonomies(id),
            FOREIGN KEY (base_checkpoint_id) REFERENCES checkpoints(id)
        )
    """)

    # 4. chains
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chains (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            stage TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 5. chain_steps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chain_steps (
            id TEXT PRIMARY KEY,
            chain_id TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            recipe_id TEXT NOT NULL,
            dataset_id TEXT,
            base_source TEXT NOT NULL CHECK (base_source IN ('recipe_default', 'previous_step_best', 'specific_checkpoint')),
            base_checkpoint_id TEXT,
            FOREIGN KEY (chain_id) REFERENCES chains(id) ON DELETE CASCADE,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id),
            FOREIGN KEY (base_checkpoint_id) REFERENCES checkpoints(id)
        )
    """)

    # 6. Extend training_jobs table (ALTER TABLE)
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(training_jobs)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        new_columns = [
            ("job_type", "TEXT DEFAULT 'training'"),
            ("recipe_id", "TEXT"),
            ("chain_id", "TEXT"),
            ("chain_step_index", "INTEGER"),
            ("parent_job_id", "TEXT"),
            ("output_checkpoint_id", "TEXT"),
        ]

        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                cursor.execute(
                    f"ALTER TABLE training_jobs ADD COLUMN {col_name} {col_type}"
                )
                logger.info(f"Added column {col_name} to training_jobs")
    except Exception as e:
        logger.warning(f"Could not extend training_jobs: {e}")

    conn.commit()
    conn.close()
    logger.info("Platform tables initialized successfully")


if __name__ == "__main__":
    init_platform_tables()
