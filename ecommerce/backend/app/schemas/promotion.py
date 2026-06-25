from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampMixin


class PromotionBase(BaseModel):
    name: str
    description: str | None = None
    promotion_type: str
    discount_type: str | None = None
    discount_value: float | None = None
    product_id: int | None = None
    category: str | None = None
    min_quantity: int | None = None
    free_product_id: int | None = None
    min_order_amount: float | None = None
    max_discount: float | None = None
    loyalty_multiplier: float | None = None
    start_date: datetime
    end_date: datetime
    is_active: bool = True


class PromotionCreate(PromotionBase):
    pass


class PromotionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    promotion_type: str | None = None
    discount_type: str | None = None
    discount_value: float | None = None
    product_id: int | None = None
    category: str | None = None
    min_quantity: int | None = None
    free_product_id: int | None = None
    min_order_amount: float | None = None
    max_discount: float | None = None
    loyalty_multiplier: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None


class PromotionResponse(PromotionBase, TimestampMixin):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PromotionValidateRequest(BaseModel):
    promotion_id: int
    order_subtotal: float
    product_ids: list[int] | None = None


class PromotionValidateResponse(BaseModel):
    is_applicable: bool
    discount_amount: float = 0
    discount_type: str | None = None
    description: str | None = None
