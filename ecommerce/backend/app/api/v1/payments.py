import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer, Order, Payment
from app.schemas.payment import (
    MpesaCallbackResponse,
    PaymentInitiateResponse,
    PaymentResponse,
)
from app.services.notification_service import NotificationService
from app.services.payment_service import MpesaService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/mpesa/stk-push", response_model=PaymentInitiateResponse)
async def initiate_mpesa_payment(
    phone: str,
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.customer_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.payment_status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already paid")

    service = MpesaService(db)
    try:
        response = await service.stk_push(
            phone=phone or current_user.phone,
            amount=order.grand_total,
            order_id=order_id,
        )

        if response.get("ResponseCode") != "0":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=response.get("ResponseDescription", "M-Pesa request failed"),
            )

        await db.commit()

        return PaymentInitiateResponse(
            checkout_request_id=response.get("CheckoutRequestID"),
            merchant_request_id=response.get("MerchantRequestID"),
            amount=order.grand_total,
            phone=phone or current_user.phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/mpesa/callback")
async def mpesa_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
        logger.info(f"M-Pesa callback received: {body}")

        service = MpesaService(db)
        await service.handle_callback(body)

        stk_callback = body.get("Body", {}).get("stkCallback", {})
        result_code = stk_callback.get("ResultCode")

        if result_code == 0:
            callback_metadata = stk_callback.get("CallbackMetadata", {})
            items = callback_metadata.get("Item", [])
            checkout_id = stk_callback.get("CheckoutRequestID")

            from sqlalchemy import select
            result = await db.execute(
                select(Payment).where(Payment.checkout_request_id == checkout_id)
            )
            payment = result.scalar_one_or_none()
            if payment:
                order_result = await db.execute(
                    select(Order).where(Order.id == payment.order_id)
                )
                order = order_result.scalar_one_or_none()
                if order:
                    notif_service = NotificationService(db)
                    await notif_service.send_payment_received(
                        order.customer_id, order.order_number, payment.amount
                    )

        await db.commit()
        return MpesaCallbackResponse(ResultCode=0, ResultDesc="Success")
    except Exception as e:
        logger.error(f"Callback processing error: {e}")
        return MpesaCallbackResponse(ResultCode=1, ResultDesc=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(
        select(Payment)
        .join(Order)
        .where(
            Payment.id == payment_id,
            Order.customer_id == current_user.id,
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
