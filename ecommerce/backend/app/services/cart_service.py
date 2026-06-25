from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import CartItem, Product


class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_item(
        self, customer_id: int, product_id: int, quantity: int
    ) -> CartItem:
        product = await self.db.execute(
            select(Product).where(
                Product.id == product_id, Product.is_active == True
            )
        )
        product = product.scalar_one_or_none()
        if not product:
            raise ValueError("Product not found")
        if product.stock_quantity < quantity:
            raise ValueError(f"Insufficient stock. Available: {product.stock_quantity}")

        existing = await self.db.execute(
            select(CartItem).where(
                CartItem.customer_id == customer_id,
                CartItem.product_id == product_id,
            )
        )
        cart_item = existing.scalar_one_or_none()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if product.stock_quantity < new_qty:
                raise ValueError(
                    f"Insufficient stock. Available: {product.stock_quantity}, "
                    f"already in cart: {cart_item.quantity}"
                )
            cart_item.quantity = new_qty
        else:
            cart_item = CartItem(
                customer_id=customer_id,
                product_id=product_id,
                quantity=quantity,
            )
            self.db.add(cart_item)

        await self.db.flush()
        return cart_item

    async def update_item_quantity(
        self, customer_id: int, item_id: int, quantity: int
    ) -> CartItem:
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.customer_id == customer_id)
            .options(selectinload(CartItem.product))
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise ValueError("Cart item not found")

        if quantity == 0:
            await self.db.delete(cart_item)
            await self.db.flush()
            return cart_item

        if cart_item.product.stock_quantity < quantity:
            raise ValueError(
                f"Insufficient stock. Available: {cart_item.product.stock_quantity}"
            )

        cart_item.quantity = quantity
        await self.db.flush()
        return cart_item

    async def remove_item(self, customer_id: int, item_id: int) -> None:
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id, CartItem.customer_id == customer_id
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise ValueError("Cart item not found")

        await self.db.delete(cart_item)
        await self.db.flush()

    async def get_cart(self, customer_id: int) -> list[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.customer_id == customer_id)
            .options(selectinload(CartItem.product).selectinload(Product.images))
        )
        return list(result.scalars().all())

    async def clear_cart(self, customer_id: int) -> None:
        result = await self.db.execute(
            select(CartItem).where(CartItem.customer_id == customer_id)
        )
        for item in result.scalars().all():
            await self.db.delete(item)
        await self.db.flush()

    async def get_cart_subtotal(self, customer_id: int) -> float:
        cart_items = await self.get_cart(customer_id)
        return sum(
            item.product.selling_price * item.quantity for item in cart_items
            if item.product
        )
