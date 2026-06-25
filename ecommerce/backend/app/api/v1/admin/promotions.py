from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, Promotion
from app.schemas.common import MessageResponse
from app.schemas.promotion import PromotionCreate, PromotionResponse, PromotionUpdate

router = APIRouter()


@router.get("", response_model=list[PromotionResponse])
async def list_all_promotions(
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Promotion).order_by(Promotion.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
async def create_promotion(
    data: PromotionCreate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    promotion = Promotion(**data.model_dump())
    db.add(promotion)
    await db.commit()
    await db.refresh(promotion)
    return promotion


@router.put("/{promotion_id}", response_model=PromotionResponse)
async def update_promotion(
    promotion_id: int,
    data: PromotionUpdate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Promotion).where(Promotion.id == promotion_id))
    promotion = result.scalar_one_or_none()
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(promotion, field, value)

    await db.commit()
    return promotion


@router.delete("/{promotion_id}", response_model=MessageResponse)
async def delete_promotion(
    promotion_id: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Promotion).where(Promotion.id == promotion_id))
    promotion = result.scalar_one_or_none()
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")

    promotion.is_active = False
    await db.commit()
    return MessageResponse(message="Promotion deactivated")
