from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: str | None = None
    unit_price: float
    quantity: int
    subtotal: float
    is_alcoholic: bool

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    customer_id: int
    items: list[CartItemResponse]
    total_items: int
    subtotal: float


class CartClearRequest(BaseModel):
    pass
