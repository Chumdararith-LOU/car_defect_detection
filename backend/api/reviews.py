from typing import List

from fastapi import APIRouter, status

from schemas.review import ReviewCreate, ReviewResponse
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
