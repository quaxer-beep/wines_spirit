from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer, Notification
from app.schemas.notification import NotificationSendRequest

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_notification(
        self, data: NotificationSendRequest
    ) -> Notification:
        notification = Notification(
            customer_id=data.customer_id,
            rider_id=data.rider_id,
            branch_id=data.branch_id,
            notification_type=data.notification_type,
            channel=data.channel,
            title=data.title,
            message=data.message,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(notification)
        await self.db.flush()

        await self._send_external(notification)
        return notification

    async def send_order_confirmation(
        self, customer_id: int, order_number: str
    ) -> Notification:
        return await self.send_notification(
            NotificationSendRequest(
                customer_id=customer_id,
                notification_type="order_confirmation",
                channel="in_app",
                title="Order Confirmed",
                message=f"Your order {order_number} has been confirmed and is being processed.",
                reference_type="order",
                reference_id=None,
            )
        )

    async def send_delivery_update(
        self, customer_id: int, order_number: str, status: str
    ) -> Notification:
        return await self.send_notification(
            NotificationSendRequest(
                customer_id=customer_id,
                notification_type="delivery_update",
                channel="in_app",
                title="Delivery Update",
                message=f"Order {order_number}: {status.replace('_', ' ').title()}",
                reference_type="order",
                reference_id=None,
            )
        )

    async def send_payment_received(
        self, customer_id: int, order_number: str, amount: float
    ) -> Notification:
        return await self.send_notification(
            NotificationSendRequest(
                customer_id=customer_id,
                notification_type="payment_received",
                channel="in_app",
                title="Payment Received",
                message=f"Payment of KES {amount:.2f} for order {order_number} received.",
                reference_type="order",
                reference_id=None,
            )
        )

    async def get_customer_notifications(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[Notification], int, int]:
        query = (
            select(Notification)
            .where(
                Notification.customer_id == customer_id,
                Notification.channel == "in_app",
            )
            .order_by(Notification.sent_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        unread_query = select(func.count()).select_from(
            select(Notification)
            .where(
                Notification.customer_id == customer_id,
                Notification.channel == "in_app",
                Notification.is_read == False,
            )
            .subquery()
        )
        unread_count = (await self.db.execute(unread_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total, unread_count

    async def mark_as_read(
        self, customer_id: int, notification_ids: list[int]
    ) -> int:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id.in_(notification_ids),
                Notification.customer_id == customer_id,
            )
        )
        now = datetime.now(timezone.utc)
        count = 0
        for n in result.scalars().all():
            n.is_read = True
            n.read_at = now
            count += 1
        await self.db.flush()
        return count

    async def _send_external(self, notification: Notification) -> None:
        if notification.channel == "sms":
            await self._send_sms(notification)
        elif notification.channel == "whatsapp":
            await self._send_whatsapp(notification)

    async def _send_sms(self, notification: Notification) -> None:
        if not notification.customer_id:
            return
        result = await self.db.execute(
            select(Customer).where(Customer.id == notification.customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    settings.SMS_API_URL,
                    json={
                        "api_key": settings.SMS_API_KEY,
                        "to": customer.phone,
                        "from": settings.SMS_SENDER_ID,
                        "message": f"{notification.title}: {notification.message}",
                    },
                    timeout=10.0,
                )
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

    async def _send_whatsapp(self, notification: Notification) -> None:
        if not notification.customer_id:
            return
        result = await self.db.execute(
            select(Customer).where(Customer.id == notification.customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_BUSINESS_ACCOUNT_ID}/messages",
                    headers={
                        "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": customer.phone,
                        "type": "template",
                        "template": {
                            "name": "order_update",
                            "language": {"code": "en"},
                            "components": [
                                {
                                    "type": "body",
                                    "parameters": [
                                        {"type": "text", "text": notification.title},
                                        {"type": "text", "text": notification.message},
                                    ],
                                }
                            ],
                        },
                    },
                    timeout=10.0,
                )
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")
