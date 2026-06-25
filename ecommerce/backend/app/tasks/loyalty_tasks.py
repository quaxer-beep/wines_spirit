import asyncio
import logging

from app.core.database import get_session
from app.services.loyalty_service import LoyaltyService

logger = logging.getLogger(__name__)


def expire_loyalty_points():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_expire_points())


async def _expire_points():
    async for session in get_session():
        service = LoyaltyService(session)
        total_expired = await service.expire_points()
        await session.commit()
        if total_expired > 0:
            logger.info(f"Expired {total_expired} loyalty points")
