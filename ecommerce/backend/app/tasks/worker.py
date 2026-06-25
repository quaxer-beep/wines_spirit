import logging

import redis
from rq import Connection, Worker

from app.core.config import settings

logger = logging.getLogger(__name__)


def run_worker():
    redis_conn = redis.from_url(settings.REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(["default", "sync", "loyalty", "notifications"])
        worker.work()


if __name__ == "__main__":
    run_worker()
