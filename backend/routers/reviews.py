import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import ContractReview
from schemas import ReviewDetailOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


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


@router.get("/contracts/{contract_id}/review", response_model=ReviewDetailOut)
async def get_review_by_contract(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContractReview)
        .options(selectinload(ContractReview.clauses))
        .where(ContractReview.contract_id == contract_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
