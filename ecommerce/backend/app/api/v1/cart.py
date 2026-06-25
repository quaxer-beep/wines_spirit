from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)
from app.schemas.common import MessageResponse
from app.services.cart_service import CartService

router = APIRouter()


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    items = await service.get_cart(current_user.id)

    cart_items = []
    subtotal = 0.0
    for item in items:
        if item.product:
            unit_price = item.product.selling_price
            item_subtotal = unit_price * item.quantity
            subtotal += item_subtotal
            primary_image = next(
                (img.url for img in item.product.images if img.is_primary),
                item.product.images[0].url if item.product.images else None,
            )
            cart_items.append(
                CartItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    product_image=primary_image,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    subtotal=item_subtotal,
                    is_alcoholic=item.product.is_alcoholic,
                )
            )

    return CartResponse(
        customer_id=current_user.id,
        items=cart_items,
        total_items=sum(i.quantity for i in items),
        subtotal=round(subtotal, 2),
    )


@router.post("/add", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreate,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    try:
        cart_item = await service.add_item(current_user.id, data.product_id, data.quantity)
        await db.commit()
        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=cart_item.product.name,
            unit_price=cart_item.product.selling_price,
            quantity=cart_item.quantity,
            subtotal=cart_item.product.selling_price * cart_item.quantity,
            is_alcoholic=cart_item.product.is_alcoholic,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    try:
        cart_item = await service.update_item_quantity(current_user.id, item_id, data.quantity)
        await db.commit()
        if data.quantity == 0:
            return CartItemResponse(
                id=item_id, product_id=0, product_name="", quantity=0,
                unit_price=0, subtotal=0, is_alcoholic=False,
            )
        return CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=cart_item.product.name,
            unit_price=cart_item.product.selling_price,
            quantity=cart_item.quantity,
            subtotal=cart_item.product.selling_price * cart_item.quantity,
            is_alcoholic=cart_item.product.is_alcoholic,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/items/{item_id}", response_model=MessageResponse)
async def remove_cart_item(
    item_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    try:
        await service.remove_item(current_user.id, item_id)
        await db.commit()
        return MessageResponse(message="Item removed from cart")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("", response_model=MessageResponse)
async def clear_cart(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CartService(db)
    await service.clear_cart(current_user.id)
    await db.commit()
    return MessageResponse(message="Cart cleared")
