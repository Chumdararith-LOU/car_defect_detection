"""REST API for taxonomy CRUD (Stage 2 Training Platform, Phase A)."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.taxonomy import (
    Taxonomy,
    TaxonomyCreate,
    TaxonomyListResponse,
    TaxonomyUpdate,
)
from services import taxonomy_service
from services.taxonomy_service import (
    TaxonomyInUseError,
    TaxonomyNotFoundError,
    TaxonomyValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/taxonomies", tags=["taxonomies"])


@router.get("", response_model=TaxonomyListResponse)
def list_taxonomies(stage: Optional[str] = Query(None)) -> TaxonomyListResponse:
    items = taxonomy_service.list_taxonomies(stage=stage)
    return TaxonomyListResponse(taxonomies=items, total=len(items))


@router.post("", response_model=Taxonomy, status_code=201)
def create_taxonomy(payload: TaxonomyCreate) -> Taxonomy:
    try:
        return taxonomy_service.create_taxonomy(
            name=payload.name,
            stage=payload.stage,
            class_names=payload.class_names,
            description=payload.description,
        )
    except TaxonomyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{taxonomy_id}", response_model=Taxonomy)
def get_taxonomy(taxonomy_id: str) -> Taxonomy:
    try:
        return taxonomy_service.get_taxonomy(taxonomy_id)
    except TaxonomyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="taxonomy not found") from exc


@router.patch("/{taxonomy_id}", response_model=Taxonomy)
def update_taxonomy(taxonomy_id: str, payload: TaxonomyUpdate) -> Taxonomy:
    try:
        return taxonomy_service.update_taxonomy(
            taxonomy_id,
            name=payload.name,
            class_names=payload.class_names,
            description=payload.description,
        )
    except TaxonomyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="taxonomy not found") from exc
    except TaxonomyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{taxonomy_id}", status_code=204)
def delete_taxonomy(taxonomy_id: str) -> None:
    try:
        taxonomy_service.delete_taxonomy(taxonomy_id)
    except TaxonomyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="taxonomy not found") from exc
    except TaxonomyInUseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
