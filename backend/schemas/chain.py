"""Pydantic schemas for chains (Stage 2 Training Platform, Phase F)."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

BaseSource = Literal["recipe_default", "previous_step_best", "specific_checkpoint"]


class ChainStepCreate(BaseModel):
    order_index: int = 0
    recipe_id: str
    dataset_id: str
    base_source: BaseSource = "recipe_default"
    base_checkpoint_id: Optional[str] = None


class ChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    stage: str = "stage2"
    description: Optional[str] = None
    steps: List[ChainStepCreate] = []


class ChainStep(BaseModel):
    id: str
    chain_id: str
    order_index: int
    recipe_id: str
    dataset_id: str
    base_source: str
    base_checkpoint_id: Optional[str] = None


class Chain(BaseModel):
    id: str
    name: str
    stage: str
    description: Optional[str] = None
    created_at: str
    steps: List[ChainStep] = []


class ChainListResponse(BaseModel):
    chains: List[Chain]
    total: int


class ChainRunStartResponse(BaseModel):
    run_id: str
    status: str


class ChainRunJobStatus(BaseModel):
    step_index: int
    job_id: str
    status: str


class ChainRunStatusResponse(BaseModel):
    run_id: str
    chain_id: str
    status: str
    current_step: int
    jobs: List[ChainRunJobStatus]
    error: Optional[str] = None
