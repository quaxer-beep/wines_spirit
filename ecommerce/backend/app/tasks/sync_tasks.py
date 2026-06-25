import asyncio
import logging

from app.core.database import get_session
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)


def sync_all_branches():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_sync_all())


def sync_branch(branch_id: int, db_path: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_sync_single(branch_id, db_path))


async def _sync_all():
    async for session in get_session():
        service = SyncService(session)
        logs = await service.sync_all_branches()
        await session.commit()
        for log in logs:
            logger.info(
                f"Sync branch {log.branch_id}: {log.status} "
                f"({log.products_added} added, {log.products_updated} updated)"
            )


async def _sync_single(branch_id: int, db_path: str):
    async for session in get_session():
        service = SyncService(session)
        log = await service.sync_from_pos(branch_id, db_path)
        await session.commit()
        logger.info(
            f"Sync branch {branch_id}: {log.status} "
            f"({log.products_added} added, {log.products_updated} updated)"
        )
