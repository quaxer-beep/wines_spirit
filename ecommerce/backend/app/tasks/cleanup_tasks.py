import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.database import get_session
from app.models.customer import WebsiteSession

logger = logging.getLogger(__name__)


def cleanup_expired_sessions():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_cleanup())


async def _cleanup():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    async for session in get_session():
        result = await session.execute(
            select(WebsiteSession).where(
                WebsiteSession.last_activity < cutoff
            )
        )
        expired = result.scalars().all()
        count = len(expired)
        for s in expired:
            await session.delete(s)
        await session.commit()
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
