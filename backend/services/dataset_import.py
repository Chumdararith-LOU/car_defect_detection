import io
import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from services.dataset_builder import STAGE_CLASSES
from services.dataset_images import (
    _find_dataset_root,
    _find_images_dir,
    _find_labels_dir,
    get_class_names,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INSPECTIONS_DIR = PROJECT_ROOT / "backend" / "data" / "inspections"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def list_available_inspections(limit: int = 50) -> list[dict]:
    """List saved inspections with basic metadata."""
    if not INSPECTIONS_DIR.exists():
        return []

    inspections = []
    for insp_dir in sorted(INSPECTIONS_DIR.iterdir(), reverse=True):
        if not insp_dir.is_dir():
            continue

        payload_path = insp_dir / "payload.json"
        if not payload_path.exists():
            continue

        # Find image
        image_file = None
        for f in insp_dir.iterdir():
            if f.suffix.lower() in IMAGE_EXTENSIONS and f.name.startswith("image"):
                image_file = f.name
                break

        # Read basic payload info
        try:
            with open(payload_path, "r") as f:
                payload = json.load(f)
            defect_count = len(payload.get("defects", []))
            status = payload.get("inspection_status", "UNKNOWN")
            timestamp = payload.get("timestamp", "")
        except Exception:
            defect_count = 0
            status = "UNKNOWN"
            timestamp = ""

        inspections.append(
            {
                "inspection_id": insp_dir.name,
                "image_filename": image_file,
                "defect_count": defect_count,
                "inspection_status": status,
                "timestamp": timestamp,
            }
        )

        if len(inspections) >= limit:
            break

    return inspections


# ---------------------------------------------------------------------------
# Import from saved inspection
# ---------------------------------------------------------------------------


def import_inspection_to_dataset(
    dataset_id: str,
    inspection_id: str,
    split: str = "train",
) -> dict:
    """Import a saved inspection (image + defect labels) into a dataset."""
    # Validate inspection exists
    insp_dir = INSPECTIONS_DIR / inspection_id
    if not insp_dir.exists():
        raise ValueError(f"Inspection '{inspection_id}' not found")

    payload_path = insp_dir / "payload.json"
    if not payload_path.exists():
        raise ValueError(f"Inspection '{inspection_id}' has no payload.json")

    # Find source image
    source_image = None
    for f in insp_dir.iterdir():
        if f.suffix.lower() in IMAGE_EXTENSIONS and f.name.startswith("image"):
            source_image = f
            break

    if source_image is None:
        raise ValueError(f"Inspection '{inspection_id}' has no image file")

    # Resolve dataset paths
    root = _find_dataset_root(dataset_id)
    if root is None:
        raise ValueError(f"Dataset '{dataset_id}' not found")

    images_dir = _find_images_dir(root, split)
    labels_dir = _find_labels_dir(root, split)

    if images_dir is None:
        images_dir = root / "images" / split
        images_dir.mkdir(parents=True, exist_ok=True)
    if labels_dir is None:
        labels_dir = root / "labels" / split
        labels_dir.mkdir(parents=True, exist_ok=True)

    # Copy image with unique name
    out_image_name = f"{inspection_id}_{source_image.name}"
    out_image_path = images_dir / out_image_name
    shutil.copy2(source_image, out_image_path)

    # Generate YOLO label from payload defects
    with open(payload_path, "r") as f:
        payload = json.load(f)

    class_names = get_class_names(dataset_id)
    label_lines = _payload_to_yolo_labels(payload, class_names)

    # Write label file
    out_label_name = f"{inspection_id}_{source_image.stem}.txt"
    out_label_path = labels_dir / out_label_name
    with open(out_label_path, "w") as f:
        f.write("\n".join(label_lines))

    return {
        "success": True,
        "message": f"Imported inspection '{inspection_id}' into '{dataset_id}' ({split})",
        "image_filename": out_image_name,
        "labels_written": len(label_lines),
    }


def _payload_to_yolo_labels(payload: dict, class_names: list[str]) -> list[str]:
    """Convert inspection payload defects to YOLO label lines."""
    lines = []
    defects = payload.get("defects", [])

    for defect in defects:
        class_name = defect.get("class", "")
        polygon = defect.get("polygon", [])

        if not class_name or not polygon:
            continue

        # Find class_id
        if class_name not in class_names:
            logger.warning(f"Class '{class_name}' not in dataset taxonomy. Skipping.")
            continue

        class_id = class_names.index(class_name)

        # Flatten polygon to YOLO format
        coords = " ".join(f"{x} {y}" for x, y in polygon)
        lines.append(f"{class_id} {coords}")

    return lines


# ---------------------------------------------------------------------------
# Direct file upload
# ---------------------------------------------------------------------------


def upload_image_to_dataset(
    dataset_id: str,
    image_bytes: bytes,
    filename: str,
    split: str = "train",
) -> dict:
    """Upload an image directly into a dataset (creates empty label file)."""
    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image format '{ext}'. Allowed: {sorted(IMAGE_EXTENSIONS)}"
        )

    # Resolve dataset paths
    root = _find_dataset_root(dataset_id)
    if root is None:
        raise ValueError(f"Dataset '{dataset_id}' not found")

    images_dir = _find_images_dir(root, split)
    labels_dir = _find_labels_dir(root, split)

    if images_dir is None:
        images_dir = root / "images" / split
        images_dir.mkdir(parents=True, exist_ok=True)
    if labels_dir is None:
        labels_dir = root / "labels" / split
        labels_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename (handle collisions)
    safe_name = filename.replace(" ", "_")
    out_image_path = images_dir / safe_name
    counter = 1
    while out_image_path.exists():
        stem = Path(safe_name).stem
        out_image_path = images_dir / f"{stem}_{counter}{ext}"
        counter += 1

    # Write image
    with open(out_image_path, "wb") as f:
        f.write(image_bytes)

    # Create empty label file (engineer will annotate later)
    out_label_name = out_image_path.stem + ".txt"
    out_label_path = labels_dir / out_label_name
    if not out_label_path.exists():
        out_label_path.touch()

    return {
        "success": True,
        "message": f"Uploaded '{out_image_path.name}' to '{dataset_id}' ({split})",
        "image_filename": out_image_path.name,
        "labels_written": 0,
    }


# ---------------------------------------------------------------------------
# Create new dataset
# ---------------------------------------------------------------------------


def create_new_dataset(
    version_name: str,
    stage: str,
    notes: Optional[str] = None,
) -> dict:
    """Create a new empty dataset with standard folder structure and data.yaml."""
    out_dir = DATA_PROCESSED_DIR / version_name
    if out_dir.exists():
        raise ValueError(f"Dataset '{version_name}' already exists at {out_dir}")

    class_names = STAGE_CLASSES.get(stage)
    if not class_names:
        raise ValueError(f"Unsupported stage '{stage}'.")

    # Create standard YOLO folder structure
    for split in ("train", "val", "test"):
        (out_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # Write data.yaml
    yaml_content = {
        "path": str(out_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(class_names),
        "names": class_names,
    }
    with open(out_dir / "data.yaml", "w") as f:
        yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False)

    # Write build manifest
    manifest = {
        "dataset_id": version_name,
        "stage": stage,
        "version_name": version_name,
        "created_at": datetime.now().isoformat(),
        "notes": notes,
        "class_names": class_names,
    }
    with open(out_dir / "build_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return {
        "success": True,
        "dataset_id": version_name,
        "path": str(out_dir),
        "message": f"Created empty dataset '{version_name}' for {stage}.",
    }


def import_zip_to_dataset(
    dataset_id: str,
    zip_bytes: bytes,
    split: str = "train",
) -> dict:
    """Import images and labels from a ZIP file into a dataset split."""
    root = _find_dataset_root(dataset_id)
    if root is None:
        raise ValueError(f"Dataset '{dataset_id}' not found")

    images_dir = _find_images_dir(root, split)
    if images_dir is None:
        images_dir = root / "images" / split
        images_dir.mkdir(parents=True, exist_ok=True)

    labels_dir = _find_labels_dir(root, split)
    if labels_dir is None:
        labels_dir = root / "labels" / split
        labels_dir.mkdir(parents=True, exist_ok=True)

    stats = {"images": 0, "labels": 0, "skipped": 0}

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Security: check for path traversal
        for name in zf.namelist():
            if name.startswith("/") or ".." in name:
                raise ValueError(f"Unsafe path in ZIP: {name}")

        for info in zf.infolist():
            if info.is_dir():
                continue

            filename = Path(info.filename).name
            ext = Path(filename).suffix.lower()

            if ext in IMAGE_EXTENSIONS:
                target = images_dir / filename
                with zf.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                stats["images"] += 1
            elif ext == ".txt":
                target = labels_dir / filename
                with zf.open(info) as src, open(target, "wb") as dst:
                    dst.write(src.read())
                stats["labels"] += 1
            else:
                stats["skipped"] += 1

    return {
        "success": True,
        "message": f"Imported {stats['images']} images and {stats['labels']} labels into {split}.",
        "stats": stats,
    }
