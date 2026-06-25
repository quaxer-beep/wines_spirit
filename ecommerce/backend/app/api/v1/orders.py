from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[OrderListResponse])
async def list_orders(
    page: int = 1,
    page_size: int = 20,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    orders, total = await service.get_customer_orders(
        current_user.id, page, page_size
    )

    items = [
        OrderListResponse(
            id=o.id,
            order_number=o.order_number,
            grand_total=o.grand_total,
            status=o.status,
            payment_status=o.payment_status,
            delivery_status=o.delivery_status,
            item_count=len(o.items),
            created_at=o.created_at,
        )
        for o in orders
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    order = await service.get_order(order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.status}' status",
        )

    data = OrderStatusUpdate(status="cancelled")
    cancelled = await service.update_order_status(order_id, data, current_user.id)
    await db.commit()
    return cancelled
