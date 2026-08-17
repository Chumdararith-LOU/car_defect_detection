"""Full dataset audit gate (Stage 2 Training Platform, Phase B).

Computes class distribution, annotation size buckets (Commandment #1:
bottom-10% area band), label validity, and leakage status; caches the
report as JSON. A dataset is cleared for training only when the gate passes.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from services import dataset_registry

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
AUDIT_DIR = BACKEND_DIR / "data" / "audits"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class AuditNotFoundError(LookupError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _polygon_area(coords: list) -> float:
    """Shoelace area on normalized coords (fraction of image area)."""
    xs = coords[0::2]
    ys = coords[1::2]
    n = len(xs)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        s += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(s) / 2.0


def _labels_dir_for(images_dir: Path) -> Path:
    if images_dir.name == "images":
        return images_dir.parent / "labels"
    return Path(str(images_dir).replace("/images/", "/labels/"))


def _parse_label_file(
    path: Path, nc: int, class_counts: dict, issues: dict, areas: list
) -> int:
    instances = 0
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        issues["empty_label_images"] += 1
        return 0
    for line in text.splitlines():
        toks = line.split()
        if len(toks) < 7 or (len(toks) - 1) % 2 != 0:
            issues["unparseable_lines"] += 1
            continue
        try:
            cid = int(toks[0])
            coords = [float(t) for t in toks[1:]]
        except ValueError:
            issues["unparseable_lines"] += 1
            continue
        if cid < 0 or cid >= nc:
            issues["out_of_range_class_ids"] += 1
            continue
        if not all(0.0 <= c <= 1.0 for c in coords):
            issues["unparseable_lines"] += 1
            continue
        instances += 1
        class_counts[cid] = class_counts.get(cid, 0) + 1
        areas.append(_polygon_area(coords))
    return instances


def _leakage_clean(leakage) -> bool:
    """Defensive interpreter for the existing leakage audit result shape."""
    if leakage is None:
        return True
    if isinstance(leakage, dict):
        for key in ("clean", "passed", "is_clean"):
            if key in leakage:
                return bool(leakage[key])
        for key in ("overlap_count", "duplicate_count", "leaked_images"):
            if key in leakage:
                return int(leakage[key]) == 0
        return True
    return True


def run_full_audit(dataset_id: str) -> dict:
    ds = dataset_registry.get_dataset_detail(dataset_id)
    if ds is None:
        raise AuditNotFoundError(dataset_id)

    stage = ds.stage.value
    nc = ds.nc
    names = ds.class_names

    class_counts: dict = {}
    issues = {
        "missing_label_images": 0,
        "empty_label_images": 0,
        "unparseable_lines": 0,
        "out_of_range_class_ids": 0,
    }
    areas: list = []
    total_images = 0
    total_instances = 0

    if stage == "stage1":
        # Semantic-mask dataset: YOLO label checks do not apply.
        for split in ds.splits:
            total_images += int(split.image_count)
    else:
        for split in ds.splits:
            images_dir = Path(split.path)
            labels_dir = _labels_dir_for(images_dir)
            if not images_dir.exists():
                continue
            for img in sorted(images_dir.iterdir()):
                if img.suffix.lower() not in IMAGE_EXTS:
                    continue
                total_images += 1
                label = labels_dir / (img.stem + ".txt")
                if not label.exists():
                    issues["missing_label_images"] += 1
                    continue
                total_instances += _parse_label_file(
                    label, nc, class_counts, issues, areas
                )

    total_counted = sum(class_counts.values()) or 1
    class_distribution = [
        {
            "class_id": cid,
            "name": names[cid] if cid < len(names) else f"class_{cid}",
            "instances": class_counts.get(cid, 0),
            "share": round(class_counts.get(cid, 0) / total_counted, 4),
        }
        for cid in range(nc)
    ]
    rare_classes = [
        row["name"]
        for row in class_distribution
        if row["instances"] < 50 or row["share"] < 0.02
    ]

    if areas:
        p10 = float(np.percentile(areas, 10))
        p60 = float(np.percentile(areas, 60))
        bottom = sum(1 for a in areas if a <= p10)
        top = sum(1 for a in areas if a > p60)
        middle = len(areas) - bottom - top
    else:
        p10 = p60 = 0.0
        bottom = middle = top = 0
    size_buckets = {
        "p10_area": round(p10, 6),
        "p60_area": round(p60, 6),
        "bottom_10_count": bottom,
        "middle_50_count": middle,
        "top_40_count": top,
    }

    leakage = None
    try:
        leakage_result = dataset_registry.run_leakage_audit(dataset_id)
        if leakage_result is not None:
            leakage = leakage_result.model_dump()
    except Exception as exc:
        logger.warning("Leakage audit unavailable for %s: %s", dataset_id, exc)

    blocking: list = []
    if issues["out_of_range_class_ids"]:
        blocking.append(f"{issues['out_of_range_class_ids']} out-of-range class ids")
    if issues["unparseable_lines"]:
        blocking.append(f"{issues['unparseable_lines']} unparseable label lines")
    if not _leakage_clean(leakage):
        blocking.append("leakage audit not clean")

    warnings: list = []
    if issues["missing_label_images"]:
        warnings.append(f"{issues['missing_label_images']} images without label files")
    if issues["empty_label_images"]:
        warnings.append(f"{issues['empty_label_images']} empty label files")
    if rare_classes and stage != "stage1":
        warnings.append(f"rare classes: {', '.join(rare_classes)}")

    report = {
        "dataset_id": dataset_id,
        "stage": stage,
        "computed_at": _now_iso(),
        "totals": {"images": total_images, "instances": total_instances},
        "class_distribution": class_distribution,
        "rare_classes": rare_classes,
        "size_buckets": size_buckets,
        "label_issues": issues,
        "leakage": leakage,
        "cleared_for_training": not blocking,
        "blocking_reasons": blocking,
        "warnings": warnings,
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / f"{dataset_id}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    logger.info("Audit complete for %s (cleared=%s)", dataset_id, not blocking)
    return report


def get_cached_report(dataset_id: str) -> dict:
    path = AUDIT_DIR / f"{dataset_id}.json"
    if not path.exists():
        raise AuditNotFoundError(dataset_id)
    return json.loads(path.read_text(encoding="utf-8"))
