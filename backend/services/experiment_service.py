"""MLflow experiment discovery and comparison service."""

import logging
import os

os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

import mlflow  # noqa: E402
from mlflow.tracking import MlflowClient  # noqa: E402

from core.config import settings  # noqa: E402
from schemas.experiments import (  # noqa: E402
    ExperimentRun,
    ExperimentSummary,
    RunMetric,
    RunParam,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = settings.workspace_root
MLRUNS_DIR = PROJECT_ROOT / "mlruns"


def _get_mlflow_client() -> MlflowClient:
    """Create an MLflow client pointing to the local mlruns folder."""
    if MLRUNS_DIR.exists():
        mlflow.set_tracking_uri(f"file://{MLRUNS_DIR}")
    return MlflowClient()


def _extract_key_metrics(metrics: dict) -> list[RunMetric]:
    """Filter to the most important metrics for comparison."""
    important_keys = [
        "metrics/mAP50(B)",
        "metrics/mAP50-95(B)",
        "metrics/precision(B)",
        "metrics/recall(B)",
        "metrics/mAP50(M)",  # Mask mAP for segmentation
        "metrics/mAP50-95(M)",
        "metrics/precision(M)",
        "metrics/recall(M)",
    ]
    result = []
    for key in important_keys:
        if key in metrics:
            result.append(RunMetric(key=key, value=metrics[key]))
    return result


def _extract_key_params(params: dict) -> list[RunParam]:
    """Filter to the most important parameters."""
    important_keys = [
        "model_preset",
        "epochs",
        "imgsz",
        "batch_size",
        "loss_type",
        "dataset_config",
    ]
    result = []
    for key in important_keys:
        if key in params:
            result.append(RunParam(key=key, value=str(params[key])))
    return result


def list_experiments() -> list[ExperimentSummary]:
    """List all MLflow experiments."""
    client = _get_mlflow_client()
    experiments = client.search_experiments()

    summaries = []
    for exp in experiments:
        if exp.name == "Default" or exp.name.startswith("."):
            continue  # Skip default/hidden

        runs = client.search_runs(experiment_ids=[exp.experiment_id])
        latest_time = None
        if runs:
            latest_time = max(r.info.start_time for r in runs if r.info.start_time)
            latest_time = str(latest_time) if latest_time else None

        summaries.append(
            ExperimentSummary(
                experiment_id=exp.experiment_id,
                name=exp.name,
                run_count=len(runs),
                latest_run_time=latest_time,
            )
        )

    return sorted(summaries, key=lambda x: x.name)


def list_runs_for_experiment(experiment_id: str) -> list[ExperimentRun]:
    """List all runs for a specific experiment."""
    client = _get_mlflow_client()
    runs = client.search_runs(experiment_ids=[experiment_id])

    result = []
    for run in runs:
        info = run.info
        metrics = run.data.metrics or {}
        params = run.data.params or {}

        # Calculate duration
        duration = None
        if info.start_time and info.end_time:
            duration = (info.end_time - info.start_time) / 1000.0

        result.append(
            ExperimentRun(
                run_id=info.run_id,
                run_name=info.run_name or "unnamed",
                experiment_name=client.get_experiment(info.experiment_id).name,
                status=info.status,
                start_time=str(info.start_time) if info.start_time else None,
                end_time=str(info.end_time) if info.end_time else None,
                duration_seconds=duration,
                metrics=_extract_key_metrics(metrics),
                params=_extract_key_params(params),
                artifact_uri=info.artifact_uri,
            )
        )

    return sorted(result, key=lambda x: x.start_time or "", reverse=True)


def compare_runs(run_ids: list[str]) -> list[ExperimentRun]:
    """Fetch multiple runs for side-by-side comparison."""
    client = _get_mlflow_client()
    result = []

    for run_id in run_ids:
        run = client.get_run(run_id)
        info = run.info
        metrics = run.data.metrics or {}
        params = run.data.params or {}

        duration = None
        if info.start_time and info.end_time:
            duration = (info.end_time - info.start_time) / 1000.0

        result.append(
            ExperimentRun(
                run_id=info.run_id,
                run_name=info.run_name or "unnamed",
                experiment_name=client.get_experiment(info.experiment_id).name,
                status=info.status,
                start_time=str(info.start_time) if info.start_time else None,
                end_time=str(info.end_time) if info.end_time else None,
                duration_seconds=duration,
                metrics=_extract_key_metrics(metrics),
                params=_extract_key_params(params),
                artifact_uri=info.artifact_uri,
            )
        )

    return result
