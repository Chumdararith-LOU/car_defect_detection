"""Service to build YOLO datasets from reviewed flywheel feedback.

Queries the review DB, loads saved inspection payloads, extracts defect polygons,
and writes a standard Ultralytics-format dataset to data/processed/{version_name}/.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.inspection_store import get_inspection_image_path, load_inspection
from services.review_db import review_db

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Class taxonomies per stage (from champion_manifest.md)
STAGE_CLASSES = {
    "stage1": ["background", "defect"],
    "stage2": [
        "dent",
        "scratch",
        "crack",
        "glass_shatter",
        "broken_lamp",
        "corrosion",
        "disjoint_part",
    ],
    "stage3": [
        "Quarter-panel",
        "Front-wheel",
        "Back-window",
        "Trunk",
        "Front-door",
        "Rocker-panel",
        "Grille",
        "Windshield",
        "Front-window",
        "Back-door",
        "Headlight",
        "Back-wheel",
        "Back-windshield",
        "Hood",
        "Fender",
        "Tail-light",
        "License-plate",
        "Front-bumper",
        "Back-bumper",
        "Mirror",
        "Roof",
    ],
}


def build_dataset_from_reviews(
    stage: str,
    version_name: str,
    include_confirmed: bool,
    include_rejected: bool,
    include_unclear: bool,
    notes: Optional[str] = None,
) -> dict:
    """Build a YOLO dataset from reviewed inspection feedback."""

    out_dir = DATA_PROCESSED_DIR / version_name
    if out_dir.exists():
        raise ValueError(
            f"Dataset version '{version_name}' already exists at {out_dir}"
        )

    images_dir = out_dir / "images" / "train"
    labels_dir = out_dir / "labels" / "train"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    class_names = STAGE_CLASSES.get(stage)
    if not class_names:
        shutil.rmtree(out_dir, ignore_errors=True)
        raise ValueError(
            f"Unsupported stage '{stage}'. Must be stage1, stage2, or stage3."
        )

    # 1. Fetch matching reviews from SQLite
    reviews_to_process = []
    with review_db._connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT inspection_id, defect_id, operator_decision, corrected_class, predicted_class FROM reviews"
        )
        for row in cursor.fetchall():
            insp_id, def_id, decision, corr_class, pred_class = row
            if decision == "confirm" and include_confirmed:
                reviews_to_process.append(
                    (insp_id, def_id, "confirm", corr_class, pred_class)
                )
            elif decision == "reclassify" and include_confirmed:
                reviews_to_process.append(
                    (insp_id, def_id, "reclassify", corr_class, pred_class)
                )
            elif decision == "reject" and include_rejected:
                reviews_to_process.append(
                    (insp_id, def_id, "reject", corr_class, pred_class)
                )
            elif decision == "unclear" and include_unclear:
                reviews_to_process.append(
                    (insp_id, def_id, "unclear", corr_class, pred_class)
                )

    if not reviews_to_process:
        shutil.rmtree(out_dir, ignore_errors=True)
        raise ValueError("No reviews matched the selected criteria.")

    # 2. Process reviews into YOLO label lines
    stats = {"images_copied": 0, "instances_written": 0, "skipped": 0}
    processed_inspections: dict[str, list[str]] = {}

    for insp_id, def_id, decision, corr_class, pred_class in reviews_to_process:
        # Rejected items become hard negatives (image copied, empty label file)
        if decision == "reject":
            if insp_id not in processed_inspections:
                processed_inspections[insp_id] = []
            continue

        # Determine final class
        final_class = (
            corr_class if (decision == "reclassify" and corr_class) else pred_class
        )
        if final_class not in class_names:
            logger.warning(
                f"Class '{final_class}' not in {stage} taxonomy. Skipping defect {def_id}"
            )
            stats["skipped"] += 1
            continue

        class_id = class_names.index(final_class)

        # Load payload and find the defect
        payload = load_inspection(insp_id)
        if not payload:
            stats["skipped"] += 1
            continue

        target_defect = None
        for d in payload.get("defects", []):
            if d.get("id") == def_id:
                target_defect = d
                break
        if not target_defect:
            for d in payload.get("unclassified_anomalies", []):
                if d.get("id") == def_id:
                    target_defect = d
                    break

        if not target_defect or not target_defect.get("polygon"):
            stats["skipped"] += 1
            continue

        if insp_id not in processed_inspections:
            processed_inspections[insp_id] = []

        # Flatten polygon to YOLO format: class_id x1 y1 x2 y2 ...
        poly = target_defect["polygon"]
        coords = " ".join(f"{x} {y}" for x, y in poly)
        processed_inspections[insp_id].append(f"{class_id} {coords}")
        stats["instances_written"] += 1

    # 3. Write images and label files
    for insp_id, label_lines in processed_inspections.items():
        img_path = get_inspection_image_path(insp_id)
        if not img_path:
            stats["skipped"] += 1
            continue

        # Unique filename to avoid collisions
        out_img_name = f"{insp_id}_{img_path.name}"
        out_img_path = images_dir / out_img_name
        shutil.copy2(img_path, out_img_path)
        stats["images_copied"] += 1

        # Write label file (empty for hard negatives)
        out_lbl_name = f"{insp_id}_{img_path.stem}.txt"
        out_lbl_path = labels_dir / out_lbl_name
        with open(out_lbl_path, "w") as f:
            f.write("\n".join(label_lines))

    # 4. Write data.yaml
    yaml_content = f"""# Auto-generated by Dataset Builder
# Stage: {stage}
# Version: {version_name}
path: {out_dir.as_posix()}
train: images/train
val: images/train
nc: {len(class_names)}
names: {json.dumps(class_names)}
"""
    with open(out_dir / "data.yaml", "w") as f:
        f.write(yaml_content)

    # 5. Write build manifest
    manifest = {
        "dataset_id": version_name,
        "stage": stage,
        "version_name": version_name,
        "created_at": datetime.now().isoformat(),
        "notes": notes,
        "stats": stats,
        "class_names": class_names,
    }
    with open(out_dir / "build_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Built dataset '{version_name}': {stats}")
    return {
        "dataset_id": version_name,
        "path": str(out_dir),
        "stats": stats,
    }
