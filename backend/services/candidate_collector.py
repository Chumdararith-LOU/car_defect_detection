"""Collects training outputs (weights + metrics) after a job completes
and registers the result as a candidate model in the model registry.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Optional

from core.config import settings
from schemas.model_registry import RegisterRequest, StageType
from schemas.training import TrainingJob
from services.model_registry_service import register_model

logger = logging.getLogger("CandidateCollector")

PROJECT_ROOT = settings.workspace_root

# Map Ultralytics results.csv column names → registry metric keys
METRIC_KEY_MAP = {
    # Segmentation metrics (Stage 2 / Stage 3)
    "metrics/mAP50(M)": "test_mask_map50",
    "metrics/mAP50-95(M)": "test_mask_map50_95",
    "metrics/precision(M)": "test_precision",
    "metrics/recall(M)": "test_recall",
    # Box / binary metrics (Stage 1)
    "metrics/mAP50(B)": "test_box_map50",
    "metrics/mAP50-95(B)": "test_box_map50_95",
    "metrics/precision(B)": "test_precision",
    "metrics/recall(B)": "recall",
}


def find_best_weights(job: TrainingJob) -> Optional[Path]:
    """Locate the best.pt produced by a training job."""
    # Pattern 1: Ultralytics convention runs/{task}/{project}/{run}/weights/best.pt
    for task in ("segment", "detect"):
        expected = (
            PROJECT_ROOT
            / "runs"
            / task
            / job.project_name
            / job.run_name
            / "weights"
            / "best.pt"
        )
        if expected.exists():
            return expected

    # Fallback: most recently modified best.pt anywhere under runs/
    runs_dir = PROJECT_ROOT / "runs"
    if runs_dir.exists():
        candidates = list(runs_dir.rglob("weights/best.pt"))
        if candidates:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            logger.info(f"Using fallback weights discovery: {newest}")
            return newest

    return None


def extract_metrics(weights_path: Path) -> Dict[str, float]:
    """Parse the last row of results.csv (written next to weights by Ultralytics)."""
    results_csv = weights_path.parent.parent / "results.csv"
    if not results_csv.exists():
        logger.warning(f"No results.csv found at {results_csv}")
        return {}

    metrics: Dict[str, float] = {}
    try:
        with open(results_csv, "r") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            return {}
        last_row = rows[-1]
        for raw_key, raw_value in last_row.items():
            key = raw_key.strip() if raw_key else ""
            mapped = METRIC_KEY_MAP.get(key)
            if mapped is None:
                continue
            try:
                metrics[mapped] = float(raw_value)
            except (TypeError, ValueError):
                continue
    except Exception as e:
        logger.warning(f"Failed to parse results.csv: {e}")
    return metrics


def register_candidate_from_job(job: TrainingJob) -> None:
    """Register a completed training job as a candidate model."""
    weights_path = find_best_weights(job)
    if weights_path is None:
        logger.warning(
            f"Job {job.id}: could not locate best.pt — skipping candidate registration"
        )
        return

    metrics = extract_metrics(weights_path)

    request = RegisterRequest(
        stage=StageType(job.stage.value),
        model_name=job.project_name,
        version=job.run_name,
        weights_path=str(weights_path),
        dataset_version=job.dataset_path,
        training_run_id=job.id,
        metrics=metrics,
        model_card=None,
    )
    model = register_model(request)
    logger.info(
        f"Job {job.id}: registered candidate '{model.model_name}' "
        f"v{model.version} ({len(metrics)} metrics extracted)"
    )
