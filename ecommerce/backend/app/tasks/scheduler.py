import logging

from redis import Redis
from rq import Queue
from rq.scheduler import RQScheduler

from app.core.config import settings
from app.tasks.cleanup_tasks import cleanup_expired_sessions
from app.tasks.loyalty_tasks import expire_loyalty_points
from app.tasks.notification_tasks import send_pending_notifications
from app.tasks.sync_tasks import sync_all_branches

logger = logging.getLogger(__name__)


def start_scheduler():
    redis_conn = Redis.from_url(settings.REDIS_URL)
    scheduler = RQScheduler(connection=redis_conn)

    scheduler.schedule(
        scheduled_time="2000-01-01 00:00:00",
        func=sync_all_branches,
        interval=settings.SYNC_INTERVAL_SECONDS,
        repeat=None,
        queue_name="sync",
    )

    scheduler.schedule(
        scheduled_time="2000-01-01 00:00:00",
        func=expire_loyalty_points,
        interval=86400,
        repeat=None,
        queue_name="loyalty",
    )

    scheduler.schedule(
        scheduled_time="2000-01-01 00:00:00",
        func=send_pending_notifications,
        interval=300,
        repeat=None,
        queue_name="notifications",
    )

    scheduler.schedule(
        scheduled_time="2000-01-01 00:00:00",
        func=cleanup_expired_sessions,
        interval=86400,
        repeat=None,
        queue_name="default",
    )

    scheduler.run()
    logger.info("Task scheduler started")


if __name__ == "__main__":
    start_scheduler()
