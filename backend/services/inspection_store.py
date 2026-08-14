"""Service to persist inspection images and payloads to disk.

Creates:
    backend/data/inspections/{inspection_id}/image.{ext}
    backend/data/inspections/{inspection_id}/payload.json
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Base directory for storing inspection data
INSPECTIONS_DIR = Path(__file__).resolve().parent.parent / "data" / "inspections"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def _ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def save_inspection(
    inspection_id: str,
    image_bytes: bytes,
    image_filename: str,
    payload: dict,
) -> Path:
    """Save an inspection's image and payload to disk."""
    inspection_dir = INSPECTIONS_DIR / inspection_id
    _ensure_dir(inspection_dir)

    # Determine image extension from filename
    ext = Path(image_filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        ext = ".jpg"

    # Save image
    image_path = inspection_dir / f"image{ext}"
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # Save payload as JSON
    payload_path = inspection_dir / "payload.json"
    with open(payload_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    logger.info(f"Saved inspection {inspection_id} to {inspection_dir}")
    return inspection_dir


def load_inspection(inspection_id: str) -> Optional[dict]:
    """Load an inspection's payload from disk."""
    payload_path = INSPECTIONS_DIR / inspection_id / "payload.json"
    if not payload_path.exists():
        logger.warning(f"Inspection {inspection_id} not found at {payload_path}")
        return None

    with open(payload_path, "r") as f:
        return json.load(f)


def get_inspection_image_path(inspection_id: str) -> Optional[Path]:
    """Get the path to the saved image for an inspection."""
    inspection_dir = INSPECTIONS_DIR / inspection_id
    if not inspection_dir.exists():
        return None

    for f in inspection_dir.iterdir():
        if f.suffix.lower() in IMAGE_EXTENSIONS and f.name.startswith("image"):
            return f

    return None


def list_inspection_ids() -> list[str]:
    """List all saved inspection IDs."""
    if not INSPECTIONS_DIR.exists():
        return []
    return sorted(
        d.name
        for d in INSPECTIONS_DIR.iterdir()
        if d.is_dir() and (d / "payload.json").exists()
    )
