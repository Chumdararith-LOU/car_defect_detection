"""REST API for training recipes (Stage 2 Training Platform, Phase D)."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.recipe import Recipe, RecipeCreate, RecipeListResponse, RecipeUpdate
from services import recipe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.get("", response_model=RecipeListResponse)
def list_recipes(stage: Optional[str] = Query(None)) -> RecipeListResponse:
    items = recipe_service.list_recipes(stage=stage)
    return RecipeListResponse(recipes=items, total=len(items))


@router.get("/presets", response_model=RecipeListResponse)
def list_presets() -> RecipeListResponse:
    items = recipe_service.list_recipes(presets_only=True)
    return RecipeListResponse(recipes=items, total=len(items))


@router.post("", response_model=Recipe, status_code=201)
def create_recipe(payload: RecipeCreate) -> Recipe:
    try:
        return recipe_service.create_recipe(payload.model_dump())
    except (LookupError, KeyError) as exc:
        raise HTTPException(status_code=404, detail="taxonomy not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: str) -> Recipe:
    try:
        return recipe_service.get_recipe(recipe_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="recipe not found") from exc


@router.patch("/{recipe_id}", response_model=Recipe)
def update_recipe(recipe_id: str, payload: RecipeUpdate) -> Recipe:
    try:
        return recipe_service.update_recipe(
            recipe_id, payload.model_dump(exclude_unset=True)
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="recipe not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: str) -> None:
    try:
        recipe_service.delete_recipe(recipe_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="recipe not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
