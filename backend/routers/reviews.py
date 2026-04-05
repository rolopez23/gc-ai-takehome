import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Contract, ContractReview
from schemas import ReviewDetailOut, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/contracts/{contract_id}/review", response_model=ReviewOut, status_code=201)
async def create_review(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    review = ContractReview(contract_id=contract_id, status="pending")
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


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


@router.get("/contracts/{contract_id}/reviews", response_model=list[ReviewOut])
async def list_reviews_for_contract(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContractReview)
        .where(ContractReview.contract_id == contract_id)
        .order_by(ContractReview.created_at.desc())
    )
    return result.scalars().all()
