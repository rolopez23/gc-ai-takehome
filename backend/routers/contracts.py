import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, Form
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Contract, ContractReview
from schemas import ContractDetailOut, ContractListOut, ContractOut, ReviewDetailOut, UploadResponse
from services.conversion import process_upload
from services.evaluation import evaluate_contract_task

router = APIRouter(prefix="/contracts", tags=["contracts"])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_contract(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    instructions: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        result = process_upload(file.filename or "unknown", file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=str(e))

    contract = Contract(
        name=file.filename or "unknown",
        upload_type=result.upload_type,
        original_blob=result.original_blob,
        pdf_blob=result.pdf_blob,
        text=result.text,
    )
    db.add(contract)
    await db.flush()

    review = ContractReview(
        contract_id=contract.id,
        status="pending",
        review_instructions=instructions,
    )
    db.add(review)
    await db.commit()

    background_tasks.add_task(evaluate_contract_task, review.id, contract.id)

    return UploadResponse(contract_id=contract.id, review_id=review.id, status="pending")


@router.get("/", response_model=list[ContractListOut])
async def list_contracts(db: AsyncSession = Depends(get_db)):
    latest_review = (
        select(
            ContractReview.contract_id,
            func.max(ContractReview.created_at).label("max_created_at"),
        )
        .group_by(ContractReview.contract_id)
        .subquery()
    )

    stmt = (
        select(
            Contract.id,
            Contract.name,
            Contract.upload_type,
            Contract.created_at,
            ContractReview.status.label("review_status"),
            ContractReview.overall_fairness,
            ContractReview.failure_code,
        )
        .outerjoin(
            latest_review,
            Contract.id == latest_review.c.contract_id,
        )
        .outerjoin(
            ContractReview,
            (ContractReview.contract_id == latest_review.c.contract_id)
            & (ContractReview.created_at == latest_review.c.max_created_at),
        )
        .order_by(Contract.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.mappings().all()


@router.get("/{contract_id}", response_model=ContractDetailOut)
async def get_contract(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.get("/{contract_id}/review", response_model=ReviewDetailOut)
async def get_contract_review(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContractReview)
        .options(selectinload(ContractReview.clauses))
        .where(ContractReview.contract_id == contract_id)
    )
    review = result.scalars().first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review
