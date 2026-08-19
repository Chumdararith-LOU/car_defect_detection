import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import services.batch_registry as registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["batches"])


class BatchCreateRequest(BaseModel):
    inspection_ids: list[str]
    name: Optional[str] = None
    settings: Optional[dict] = None


class BatchRenameRequest(BaseModel):
    name: str


@router.get("/batches")
def api_list_batches():
    return {"batches": registry.list_batches()}


@router.post("/batches", status_code=201)
def api_create_batch(body: BatchCreateRequest):
    try:
        return registry.create_batch(
            inspection_ids=body.inspection_ids,
            name=body.name,
            settings=body.settings,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/batches/{batch_id}")
def api_get_batch(batch_id: str):
    batch = registry.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.patch("/batches/{batch_id}")
def api_rename_batch(batch_id: str, body: BatchRenameRequest):
    try:
        return registry.rename_batch(batch_id, body.name)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.delete("/batches/{batch_id}")
def api_delete_batch(batch_id: str):
    try:
        registry.delete_batch(batch_id)
        return {"success": True, "message": f"Batch '{batch_id}' deleted"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
