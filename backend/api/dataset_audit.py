"""REST API for the dataset audit gate (Stage 2 Training Platform, Phase B)."""

import logging

from fastapi import APIRouter, HTTPException

from schemas.dataset_audit import AuditReport
from services import dataset_audit
from services.dataset_audit import AuditNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["dataset-audit"])


@router.post("/{dataset_id}/audit/full", response_model=AuditReport)
def run_full_audit(dataset_id: str) -> AuditReport:
    try:
        return dataset_audit.run_full_audit(dataset_id)
    except (AuditNotFoundError, LookupError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="dataset not found") from exc


@router.get("/{dataset_id}/audit/report", response_model=AuditReport)
def get_report(dataset_id: str) -> AuditReport:
    try:
        return dataset_audit.get_cached_report(dataset_id)
    except AuditNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="no audit report yet - run POST /api/datasets/{id}/audit/full",
        ) from exc
