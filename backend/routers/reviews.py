import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import AsyncSessionLocal, get_db
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
async def stream_review(review_id: uuid.UUID):
    # Use a short-lived session for pre-flight checks only — don't hold a connection
    # from the pool for the entire streaming duration (which can be minutes).
    async with AsyncSessionLocal() as db:
        review = await db.get(ContractReview, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        if review.status in TERMINAL_STATUSES:
            raise HTTPException(status_code=409, detail="Review already completed")

        # Catches intermediate states (verifying, splitting, evaluating)
        if review.status != "pending":
            raise HTTPException(status_code=409, detail="Review already in progress")

        # Compare-and-swap: atomically set status to "verifying" only if still "pending".
        # Prevents race condition where two /stream requests pass the guard simultaneously.
        result = await db.execute(
            update(ContractReview)
            .where(ContractReview.id == review_id, ContractReview.status == "pending")
            .values(status="verifying")
        )
        await db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=409, detail="Review already in progress")

        review_data = (review.id, review.contract_id, review.review_instructions)

    orchestrator = PipelineOrchestrator(
        review_id=review_data[0],
        contract_id=review_data[1],
        instructions=review_data[2],
    )
    return StreamingResponse(orchestrator.run(), media_type="application/x-ndjson")
