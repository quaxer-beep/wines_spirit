from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Order, Payment

logger = logging.getLogger(__name__)


class MpesaService:
    SANDBOX_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_URL = "https://api.safaricom.co.ke"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_url = self.SANDBOX_URL if settings.MPESA_ENV == "sandbox" else self.PRODUCTION_URL

    async def _get_access_token(self) -> str:
        auth = base64.b64encode(
            f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={"Authorization": f"Basic {auth}"},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def stk_push(
        self, phone: str, amount: float, order_id: int
    ) -> dict:
        access_token = await self._get_access_token()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()

        clean_phone = phone.replace("+", "")
        if clean_phone.startswith("0"):
            clean_phone = "254" + clean_phone[1:]
        elif clean_phone.startswith("7"):
            clean_phone = "254" + clean_phone

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": clean_phone,
            "PartyB": settings.MPESA_SHORTCODE,
            "PhoneNumber": clean_phone,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": f"ORDER{order_id}",
            "TransactionDesc": "Wines & Spirits Purchase",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

        payment = Payment(
            order_id=order_id,
            method="MPESA",
            amount=amount,
            merchant_request_id=result.get("MerchantRequestID"),
            checkout_request_id=result.get("CheckoutRequestID"),
            phone_number=clean_phone,
            status="pending",
        )
        self.db.add(payment)
        await self.db.flush()

        return result

    async def handle_callback(self, callback_data: dict) -> None:
        try:
            body = callback_data.get("Body", {})
            stk_callback = body.get("stkCallback", {})
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            result_code = stk_callback.get("ResultCode")
            result_desc = stk_callback.get("ResultDesc")

            result = await self.db.execute(
                select(Payment).where(
                    Payment.checkout_request_id == checkout_request_id
                )
            )
            payment = result.scalar_one_or_none()
            if not payment:
                logger.error(f"Payment not found for {checkout_request_id}")
                return

            payment.result_desc = result_desc
            payment.updated_at = datetime.now(timezone.utc)

            if result_code == 0:
                callback_metadata = stk_callback.get("CallbackMetadata", {})
                items = callback_metadata.get("Item", [])
                for item in items:
                    if item.get("Name") == "MpesaReceiptNumber":
                        payment.receipt_number = item.get("Value")
                    elif item.get("Name") == "PhoneNumber":
                        payment.phone_number = str(item.get("Value"))
                    elif item.get("Name") == "Amount":
                        payment.amount = float(item.get("Value"))

                payment.status = "completed"

                order_result = await self.db.execute(
                    select(Order).where(Order.id == payment.order_id)
                )
                order = order_result.scalar_one_or_none()
                if order:
                    order.payment_status = "paid"
                    order.status = "confirmed"
            else:
                payment.status = "failed"

            await self.db.flush()

        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {e}")
            raise

    async def query_status(self, checkout_request_id: str) -> dict:
        access_token = await self._get_access_token()

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}".encode()
        ).decode()

        payload = {
            "BusinessShortCode": settings.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()
