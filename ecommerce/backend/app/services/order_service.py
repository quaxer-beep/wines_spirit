from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.customer import (
    CartItem,
    Customer,
    CustomerAddress,
    LoyaltyAccount,
    Order,
    OrderItem,
    Product,
    Promotion,
)
from app.schemas.order import CheckoutRequest, OrderStatusUpdate


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_order_number(self, branch_id: int | None = None) -> str:
        today = datetime.now(timezone.utc)
        date_str = today.strftime("%Y%m%d")

        result = await self.db.execute(
            select(func.count())
            .select_from(Order)
            .where(
                func.date(Order.created_at) == today.date()
            )
        )
        count = (result.scalar() or 0) + 1
        branch_part = f"{branch_id or 0:02d}"
        return f"ORD-{date_str}-{branch_part}-{count:04d}"

    async def create_order(
        self, customer_id: int, data: CheckoutRequest
    ) -> Order:
        result = await self.db.execute(
            select(Customer)
            .where(Customer.id == customer_id)
            .options(selectinload(Customer.cart_items).selectinload(CartItem.product))
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError("Customer not found")

        if not customer.cart_items:
            raise ValueError("Cart is empty")

        if data.age_consent:
            for item in customer.cart_items:
                if item.product.is_alcoholic and not customer.age_verified:
                    customer.age_verified = True
                    customer.verification_date = datetime.now(timezone.utc)

        address = None
        if data.address_id:
            addr_result = await self.db.execute(
                select(CustomerAddress).where(
                    CustomerAddress.id == data.address_id,
                    CustomerAddress.customer_id == customer_id,
                )
            )
            address = addr_result.scalar_one_or_none()
            if not address:
                raise ValueError("Address not found")

        subtotal = sum(
            item.product.selling_price * item.quantity
            for item in customer.cart_items
            if item.product
        )

        order_number = await self.generate_order_number(data.branch_id)

        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            branch_id=data.branch_id,
            address_id=data.address_id,
            subtotal=subtotal,
            delivery_fee=0.0,
            discount=0.0,
            tax=0.0,
            grand_total=subtotal,
            status="pending",
            payment_status="pending",
            delivery_status="pending",
            age_verified_at_checkout=customer.age_verified,
            age_consent_timestamp=datetime.now(timezone.utc) if data.age_consent else None,
            age_consent_ip=None,
            age_consent_device=None,
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        for cart_item in customer.cart_items:
            product = cart_item.product
            item_subtotal = product.selling_price * cart_item.quantity
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=cart_item.quantity,
                unit_price=product.selling_price,
                subtotal=item_subtotal,
            )
            self.db.add(order_item)

            product.stock_quantity -= cart_item.quantity

        await self.db.flush()

        await self.db.execute(
            select(CartItem).where(CartItem.customer_id == customer_id)
        )
        for ci in customer.cart_items:
            await self.db.delete(ci)
        await self.db.flush()

        return order

    async def get_order(self, order_id: int, customer_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id, Order.customer_id == customer_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.delivery),
            )
        )
        return result.scalar_one_or_none()

    async def get_order_by_number(
        self, order_number: str
    ) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .where(Order.order_number == order_number)
            .options(
                selectinload(Order.items),
                selectinload(Order.payments),
                selectinload(Order.delivery),
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_orders(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[Order], int]:
        query = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).options(selectinload(Order.items))
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_order_status(
        self, order_id: int, data: OrderStatusUpdate, customer_id: int | None = None
    ) -> Order:
        query = select(Order).where(Order.id == order_id)
        if customer_id:
            query = query.where(Order.customer_id == customer_id)

        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("Order not found")

        order.status = data.status
        await self.db.flush()
        return order

    async def get_all_orders(
        self, page: int = 1, page_size: int = 20, status: str | None = None
    ) -> tuple[list[Order], int]:
        query = select(Order)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            query.offset(offset)
            .limit(page_size)
            .options(selectinload(Order.items), selectinload(Order.customer))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
