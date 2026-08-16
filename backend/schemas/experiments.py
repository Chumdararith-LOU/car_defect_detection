"""Pydantic schemas for the Experiment Comparison module."""

from typing import Optional
from pydantic import BaseModel


class RunMetric(BaseModel):
    """A single metric from an MLflow run."""

    key: str
    value: float


class RunParam(BaseModel):
    """A single parameter from an MLflow run."""

    key: str
    value: str


class ExperimentRun(BaseModel):
    """Summary of one MLflow run."""

    run_id: str
    run_name: str
    experiment_name: str
    status: str  # "RUNNING" | "FINISHED" | "FAILED" | "KILLED"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    metrics: list[RunMetric]
    params: list[RunParam]
    artifact_uri: Optional[str] = None


class ExperimentSummary(BaseModel):
    """One MLflow experiment (groups multiple runs)."""

    experiment_id: str
    name: str
    run_count: int
    latest_run_time: Optional[str] = None


class ExperimentListResponse(BaseModel):
    experiments: list[ExperimentSummary]


class RunListResponse(BaseModel):
    runs: list[ExperimentRun]


class RunComparisonResponse(BaseModel):
    runs: list[ExperimentRun]
    best_run_id: Optional[str] = None  # Run with highest mAP50 or mAP50-95
