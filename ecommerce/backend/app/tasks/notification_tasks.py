import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.customer import Notification
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def send_pending_notifications():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_send_pending())


async def _send_pending():
    async for session in get_session():
        result = await session.execute(
            select(Notification).where(Notification.channel.in_(["sms", "whatsapp"]))
        )
        pending = result.scalars().all()
        service = NotificationService(session)

        for notification in pending:
            try:
                await service._send_external(notification)
            except Exception as e:
                logger.error(f"Failed to send notification {notification.id}: {e}")

        await session.commit()
