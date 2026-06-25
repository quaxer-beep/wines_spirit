from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.customer import Promotion
from app.schemas.promotion import (
    PromotionResponse,
    PromotionValidateRequest,
    PromotionValidateResponse,
)

router = APIRouter()


@router.get("", response_model=list[PromotionResponse])
async def list_active_promotions(
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Promotion).where(
            Promotion.is_active == True,
            Promotion.start_date <= now,
            Promotion.end_date >= now,
        )
    )
    return list(result.scalars().all())


@router.get("/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Promotion).where(Promotion.id == promotion_id)
    )
    promotion = result.scalar_one_or_none()
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
    return promotion


@router.post("/validate", response_model=PromotionValidateResponse)
async def validate_promotion(
    data: PromotionValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Promotion).where(Promotion.id == data.promotion_id)
    )
    promotion = result.scalar_one_or_none()
    if not promotion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")

    now = datetime.now(timezone.utc)
    if not (promotion.start_date <= now <= promotion.end_date):
        return PromotionValidateResponse(
            is_applicable=False,
            description="Promotion has expired or is not yet active",
        )

    discount_amount = 0.0
    if promotion.min_order_amount and data.order_subtotal < promotion.min_order_amount:
        return PromotionValidateResponse(
            is_applicable=False,
            description=f"Minimum order amount of KES {promotion.min_order_amount:.2f} required",
        )

    if promotion.promotion_type == "percentage" and promotion.discount_value:
        discount_amount = data.order_subtotal * (promotion.discount_value / 100)
        if promotion.max_discount:
            discount_amount = min(discount_amount, promotion.max_discount)
    elif promotion.promotion_type == "fixed" and promotion.discount_value:
        discount_amount = promotion.discount_value

    return PromotionValidateResponse(
        is_applicable=discount_amount > 0,
        discount_amount=round(discount_amount, 2),
        discount_type=promotion.discount_type,
        description=promotion.description,
    )
