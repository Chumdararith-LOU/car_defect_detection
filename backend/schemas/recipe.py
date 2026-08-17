"""Pydantic schemas for training recipes (Stage 2 Training Platform, Phase D)."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

BaseStrategy = Literal["native_coco", "from_checkpoint", "from_previous_step"]
FreezeMode = Literal["none", "freeze_n", "head_only"]
LrMode = Literal["uniform", "differential"]
LossType = Literal["bce", "focal", "ce"]


class RecipeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    taxonomy_id: str
    description: Optional[str] = None
    base_strategy: BaseStrategy = "from_checkpoint"
    base_checkpoint_id: Optional[str] = None
    freeze_mode: FreezeMode = "none"
    freeze_layers: Optional[int] = None
    lr_mode: LrMode = "uniform"
    split_layer_idx: Optional[int] = None
    backbone_lr_mult: Optional[float] = None
    loss_type: LossType = "bce"
    fl_gamma: float = 2.0
    fl_alpha: float = 0.5
    fl_scale: float = 1.0
    imgsz: int = 640
    batch_size: int = 8
    epochs: int = 100
    optimizer: str = "SGD"
    lr0: float = 0.01
    lrf: float = 0.01
    patience: int = 20
    augmentations: Optional[dict] = None


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_strategy: Optional[BaseStrategy] = None
    base_checkpoint_id: Optional[str] = None
    freeze_mode: Optional[FreezeMode] = None
    freeze_layers: Optional[int] = None
    lr_mode: Optional[LrMode] = None
    split_layer_idx: Optional[int] = None
    backbone_lr_mult: Optional[float] = None
    loss_type: Optional[LossType] = None
    fl_gamma: Optional[float] = None
    fl_alpha: Optional[float] = None
    fl_scale: Optional[float] = None
    imgsz: Optional[int] = None
    batch_size: Optional[int] = None
    epochs: Optional[int] = None
    optimizer: Optional[str] = None
    lr0: Optional[float] = None
    lrf: Optional[float] = None
    patience: Optional[int] = None
    augmentations: Optional[dict] = None


class Recipe(RecipeBase):
    id: str
    stage: str
    is_preset: bool
    created_at: str


class RecipeListResponse(BaseModel):
    recipes: list[Recipe]
    total: int
