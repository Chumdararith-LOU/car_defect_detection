from typing import Literal, Optional

from pydantic import BaseModel, Field

OperatorDecision = Literal["confirm", "reject", "reclassify", "unclear"]


class ReviewCreate(BaseModel):
    inspection_id: str = Field(..., min_length=1)
    defect_id: Optional[str] = None
    model_version: Optional[str] = None
    predicted_class: Optional[str] = None
    predicted_panel: Optional[str] = None
    operator_decision: OperatorDecision
    corrected_class: Optional[str] = None
    notes: Optional[str] = None


class ReviewResponse(ReviewCreate):
    id: int
    created_at: str
