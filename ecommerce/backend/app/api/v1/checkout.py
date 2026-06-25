from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.order import CheckoutRequest, OrderResponse
from app.services.cart_service import CartService
from app.services.delivery_service import DeliveryService
from app.services.notification_service import NotificationService
from app.services.order_service import OrderService
from app.services.payment_service import MpesaService

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    data: CheckoutRequest,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    if not data.age_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm that you are of legal drinking age",
        )

    order_service = OrderService(db)
    cart_service = CartService(db)
    delivery_service = DeliveryService(db)
    notification_service = NotificationService(db)

    try:
        cart_items = await cart_service.get_cart(current_user.id)
        if not cart_items:
            raise ValueError("Cart is empty")

        subtotal = await cart_service.get_cart_subtotal(current_user.id)

        address = None
        if data.address_id:
            from app.services.customer_service import CustomerService
            addr_service = CustomerService(db)
            addresses = await addr_service.get_addresses(current_user.id)
            address = next((a for a in addresses if a.id == data.address_id), None)
            if not address:
                raise ValueError("Address not found")

        delivery_fee = 0
        if address:
            try:
                fee_data = await delivery_service.calculate_delivery_fee()
                delivery_fee = fee_data["total_fee"]
            except ValueError:
                pass

        order = await order_service.create_order(current_user.id, data)

        if delivery_fee > 0 and address:
            delivery = await delivery_service.create_delivery(
                order_id=order.id,
                address=address.address,
                delivery_fee=delivery_fee,
            )

        order.delivery_fee = delivery_fee
        order.grand_total = order.subtotal + delivery_fee
        await db.flush()

        await notification_service.send_order_confirmation(
            current_user.id, order.order_number
        )

        await db.commit()

        result = await order_service.get_order(order.id, current_user.id)
        if not result:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Order creation failed")
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
