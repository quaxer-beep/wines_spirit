from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer, Order
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderAdminUpdate, OrderListResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[OrderListResponse])
async def list_all_orders(
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    orders, total = await service.get_all_orders(page, page_size, status_filter)
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
async def get_order_detail(
    order_id: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrderService(db)
    from sqlalchemy import select
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order_with_items = await service.get_order(order_id, order.customer_id)
    if not order_with_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order_with_items


@router.put("/{order_id}", response_model=OrderResponse)
async def admin_update_order(
    order_id: int,
    data: OrderAdminUpdate,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    await db.flush()
    await db.commit()

    service = OrderService(db)
    updated = await service.get_order(order_id, order.customer_id)
    return updated
