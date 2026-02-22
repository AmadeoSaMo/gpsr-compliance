"""Responsible Person API — EU legal representative (Art. 4 GPSR)."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.models import ResponsiblePerson

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RPBase(BaseModel):
    name: str
    trade_name: str | None = None
    address: str
    country: str
    email: str
    phone: str | None = None
    logo_data: str | None = None
    is_self: bool = True


class RPOut(RPBase):
    id: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[RPOut])
async def list_responsible_persons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResponsiblePerson))
    return [
        RPOut(id=str(rp.id), **{k: getattr(rp, k) for k in RPBase.model_fields})
        for rp in result.scalars().all()
    ]


@router.post("/", response_model=RPOut, status_code=201)
async def create_responsible_person(payload: RPBase, db: AsyncSession = Depends(get_db)):
    rp = ResponsiblePerson(id=uuid.uuid4(), **payload.model_dump())
    db.add(rp)
    await db.flush()
    await db.refresh(rp)
    return RPOut(id=str(rp.id), **payload.model_dump())


@router.put("/{rp_id}", response_model=RPOut)
async def update_responsible_person(rp_id: str, payload: RPBase, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResponsiblePerson).where(ResponsiblePerson.id == rp_id))
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(status_code=404, detail="ResponsiblePerson not found")
    for field, value in payload.model_dump().items():
        setattr(rp, field, value)
    await db.flush()
    return RPOut(id=str(rp.id), **payload.model_dump())


@router.delete("/{rp_id}", status_code=204)
async def delete_responsible_person(rp_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ResponsiblePerson).where(ResponsiblePerson.id == rp_id))
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(status_code=404, detail="ResponsiblePerson not found")
    await db.delete(rp)
