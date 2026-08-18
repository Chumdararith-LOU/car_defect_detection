"""REST API for chains (Stage 2 Training Platform, Phase F)."""

import logging

from fastapi import APIRouter, HTTPException

from schemas.chain import (
    Chain,
    ChainCreate,
    ChainListResponse,
    ChainRunStartResponse,
    ChainRunStatusResponse,
)
from services import chain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chains", tags=["chains"])


@router.get("", response_model=ChainListResponse)
def list_chains() -> ChainListResponse:
    items = chain_service.list_chains()
    return ChainListResponse(chains=items, total=len(items))


@router.post("", response_model=Chain, status_code=201)
def create_chain(payload: ChainCreate) -> Chain:
    try:
        return chain_service.create_chain(
            name=payload.name,
            stage=payload.stage,
            description=payload.description,
            steps=[s.model_dump() for s in payload.steps],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="recipe not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/runs/{run_id}", response_model=ChainRunStatusResponse)
def run_status(run_id: str) -> ChainRunStatusResponse:
    try:
        return chain_service.get_run_status(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="chain run not found") from exc


@router.get("/{chain_id}", response_model=Chain)
def get_chain(chain_id: str) -> Chain:
    try:
        return chain_service.get_chain(chain_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="chain not found") from exc


@router.post("/{chain_id}/run", response_model=ChainRunStartResponse, status_code=202)
def run_chain(chain_id: str) -> ChainRunStartResponse:
    try:
        run_id = chain_service.start_chain_run(chain_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="chain not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChainRunStartResponse(run_id=run_id, status="running")


@router.delete("/{chain_id}", status_code=204)
def delete_chain(chain_id: str) -> None:
    try:
        chain_service.delete_chain(chain_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="chain not found") from exc
