"""API endpoints for the Experiment Comparison module."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.experiments import (
    ExperimentListResponse,
    RunComparisonResponse,
    RunListResponse,
)
from services.experiment_service import (
    compare_runs,
    list_experiments,
    list_runs_for_experiment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/experiments", tags=["experiments"])


@router.get("", response_model=ExperimentListResponse)
def api_list_experiments():
    """List all MLflow experiments (excluding Default and hidden)."""
    try:
        experiments = list_experiments()
        return ExperimentListResponse(experiments=experiments)
    except Exception as e:
        logger.exception("Failed to list experiments")
        raise HTTPException(
            status_code=500, detail=f"Failed to list experiments: {str(e)}"
        )


@router.get("/{experiment_id}/runs", response_model=RunListResponse)
def api_list_runs(experiment_id: str):
    """List all runs for a specific experiment."""
    try:
        runs = list_runs_for_experiment(experiment_id)
        return RunListResponse(runs=runs)
    except Exception as e:
        logger.exception(f"Failed to list runs for experiment {experiment_id}")
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


class CompareRunsRequest(BaseModel):
    run_ids: list[str]


@router.post("/compare", response_model=RunComparisonResponse)
def api_compare_runs(body: CompareRunsRequest):
    """Compare multiple runs side-by-side."""
    if not body.run_ids:
        raise HTTPException(status_code=400, detail="No run_ids provided")
    if len(body.run_ids) > 10:
        raise HTTPException(
            status_code=400, detail="Cannot compare more than 10 runs at once"
        )

    try:
        runs = compare_runs(body.run_ids)

        # Determine best run by highest mAP50(M) or mAP50(B)
        best_run_id = None
        best_map = -1.0
        for run in runs:
            for metric in run.metrics:
                if metric.key in ("metrics/mAP50(M)", "metrics/mAP50(B)"):
                    if metric.value > best_map:
                        best_map = metric.value
                        best_run_id = run.run_id

        return RunComparisonResponse(runs=runs, best_run_id=best_run_id)
    except Exception as e:
        logger.exception("Failed to compare runs")
        raise HTTPException(status_code=500, detail=f"Failed to compare runs: {str(e)}")
