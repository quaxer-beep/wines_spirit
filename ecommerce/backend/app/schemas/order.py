from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampMixin


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)


class CheckoutRequest(BaseModel):
    address_id: int
    branch_id: int | None = None
    notes: str | None = None
    use_loyalty_points: bool = False
    loyalty_points_to_redeem: int | None = None
    age_consent: bool = False


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(TimestampMixin):
    id: int
    order_number: str
    customer_id: int
    branch_id: int | None = None
    address_id: int | None = None
    subtotal: float
    delivery_fee: float
    discount: float
    loyalty_used: int | None = None
    tax: float
    grand_total: float
    status: str
    payment_status: str
    delivery_status: str
    notes: str | None = None
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    id: int
    order_number: str
    grand_total: float
    status: str
    payment_status: str
    delivery_status: str
    item_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str


class OrderAdminUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    delivery_status: str | None = None
    branch_id: int | None = None
    notes: str | None = None
