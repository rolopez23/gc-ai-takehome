import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import ContractReview
from schemas import ReviewDetailOut
from services.orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/reviews", tags=["reviews"])

TERMINAL_STATUSES = {"completed", "failed", "rejected"}


@router.get("/{review_id}", response_model=ReviewDetailOut)
async def get_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContractReview)
        .options(selectinload(ContractReview.clauses))
        .where(ContractReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.get("/{review_id}/stream")
async def stream_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    review = await db.get(ContractReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail="Review already completed")

    if review.status != "pending":
        raise HTTPException(status_code=409, detail="Review already in progress")

    orchestrator = PipelineOrchestrator(
        review_id=review.id,
        contract_id=review.contract_id,
        instructions=review.review_instructions,
    )
    return StreamingResponse(orchestrator.run(), media_type="application/x-ndjson")
