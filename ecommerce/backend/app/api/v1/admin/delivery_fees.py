from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, DeliveryFee
from app.schemas.delivery import DeliveryFeeResponse, DeliveryFeeUpdate

router = APIRouter()


@router.get("", response_model=list[DeliveryFeeResponse])
async def list_fee_configs(
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeliveryFee).order_by(DeliveryFee.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=DeliveryFeeResponse, status_code=status.HTTP_201_CREATED)
async def create_fee_config(
    data: DeliveryFeeUpdate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    config = DeliveryFee(
        base_fee=data.base_fee or 100.0,
        per_km_rate=data.per_km_rate or 30.0,
        fuel_adjustment_pct=data.fuel_adjustment_pct or 5.0,
        min_distance_km=data.min_distance_km or 0.0,
        max_distance_km=data.max_distance_km,
        is_active=True,
    )
    db.add(config)

    if config.is_active:
        result = await db.execute(
            select(DeliveryFee).where(DeliveryFee.is_active == True)
        )
        for fee in result.scalars().all():
            if fee.id != config.id:
                fee.is_active = False

    await db.commit()
    await db.refresh(config)
    return config


@router.put("/{fee_id}", response_model=DeliveryFeeResponse)
async def update_fee_config(
    fee_id: int,
    data: DeliveryFeeUpdate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DeliveryFee).where(DeliveryFee.id == fee_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery fee config not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    return config
