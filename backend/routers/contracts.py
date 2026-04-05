import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Contract
from schemas import ContractDetailOut, ContractOut

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/", response_model=list[ContractOut])
async def list_contracts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contract).order_by(Contract.created_at.desc()))
    return result.scalars().all()


@router.get("/{contract_id}", response_model=ContractDetailOut)
async def get_contract(contract_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    contract = await db.get(Contract, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
