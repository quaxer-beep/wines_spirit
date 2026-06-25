from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, Rider
from app.schemas.delivery import RiderCreate, RiderResponse, RiderUpdate
from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("", response_model=list[RiderResponse])
async def list_riders(
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rider).order_by(Rider.name))
    return list(result.scalars().all())


@router.post("", response_model=RiderResponse, status_code=status.HTTP_201_CREATED)
async def create_rider(
    data: RiderCreate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    rider = Rider(**data.model_dump())
    db.add(rider)
    await db.commit()
    await db.refresh(rider)
    return rider


@router.get("/{rider_id}", response_model=RiderResponse)
async def get_rider(
    rider_id: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rider).where(Rider.id == rider_id))
    rider = result.scalar_one_or_none()
    if not rider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider not found")
    return rider


@router.put("/{rider_id}", response_model=RiderResponse)
async def update_rider(
    rider_id: int,
    data: RiderUpdate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rider).where(Rider.id == rider_id))
    rider = result.scalar_one_or_none()
    if not rider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rider, field, value)

    await db.commit()
    return rider


@router.delete("/{rider_id}", response_model=MessageResponse)
async def delete_rider(
    rider_id: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rider).where(Rider.id == rider_id))
    rider = result.scalar_one_or_none()
    if not rider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider not found")

    rider.is_active = False
    await db.commit()
    return MessageResponse(message="Rider deactivated")
