from typing import List

from fastapi import APIRouter, HTTPException, status

from schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from services.review_db import review_db

router = APIRouter(prefix="/api", tags=["reviews"])


@router.post(
    "/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED
)
def create_review(payload: ReviewCreate) -> ReviewResponse:
    saved = review_db.insert_review(payload.model_dump())
    return ReviewResponse(**saved)


@router.get("/reviews", response_model=List[ReviewResponse])
def list_reviews() -> List[ReviewResponse]:
    return [ReviewResponse(**row) for row in review_db.list_reviews()]


@router.get("/review-queue", response_model=List[ReviewResponse])
def get_review_queue() -> List[ReviewResponse]:
    # Pending-review queue: latest 50 reviews for now; refine logic later.
    return [ReviewResponse(**row) for row in review_db.list_reviews(limit=50)]


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int) -> ReviewResponse:
    row = review_db.get_review(review_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(**row)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(review_id: int, payload: ReviewUpdate) -> ReviewResponse:
    # Only include fields that were explicitly provided (not None)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    row = review_db.update_review(review_id, updates)
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse(**row)
