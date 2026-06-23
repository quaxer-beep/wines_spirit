import json

import httpx
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.config.logging_config import setup_logging
from src.config.settings import Settings
from src.database.connection import db_manager
from src.database.models import SyncQueue
from src.utils.exceptions import SyncError

logger = setup_logging(__name__)


class SyncQueueRepository:
    def get_pending(self):
        from src.database.connection import db_manager as dm
        with dm.get_session() as session:
            return (
                session.query(SyncQueue)
                .filter_by(status="PENDING")
                .order_by(SyncQueue.created_at.asc())
                .all()
            )

    def mark_synced(self, record_id: int):
        from src.database.connection import db_manager as dm
        with dm.get_session() as session:
            session.query(SyncQueue).filter_by(id=record_id).update(
                {
                    "status": "SYNCED",
                    "synced_at": __import__("datetime").datetime.now(),
                }
            )

    def mark_failed(self, record_id: int, error_message: str):
        from src.database.connection import db_manager as dm
        with dm.get_session() as session:
            session.query(SyncQueue).filter_by(id=record_id).update(
                {"status": "FAILED", "error_message": error_message}
            )

    def add(self, branch_id, table_name, record_id, action, payload):
        from src.database.connection import db_manager as dm
        with dm.get_session() as session:
            record = SyncQueue(
                branch_id=branch_id,
                table_name=table_name,
                record_id=record_id,
                action=action,
                payload=json.dumps(payload) if payload else None,
                status="PENDING",
            )
            session.add(record)
            return record

    def get_status_summary(self):
        from src.database.connection import db_manager as dm
        with dm.get_session() as session:
            total = session.query(SyncQueue).count()
            pending = session.query(SyncQueue).filter_by(status="PENDING").count()
            synced = session.query(SyncQueue).filter_by(status="SYNCED").count()
            failed = session.query(SyncQueue).filter_by(status="FAILED").count()
            return {
                "total": total,
                "pending": pending,
                "synced": synced,
                "failed": failed,
            }


class SyncService(QObject):
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(dict)
    sync_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sync_repo = SyncQueueRepository()
        self._running = False
        self._timer = None

    def start(self):
        if self._running:
            logger.warning("Sync service is already running.")
            return

        self._running = True
        interval = max((Settings.SYNC_INTERVAL_SECONDS or 300) * 1000, 10000)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_queue)
        self._timer.start(interval)

        logger.info("Sync service started (interval=%dms).", interval)

    def stop(self):
        if not self._running:
            return

        self._running = False
        if self._timer:
            self._timer.stop()
            self._timer = None

        logger.info("Sync service stopped.")

    def sync_now(self):
        self._process_queue()

    def _process_queue(self):
        self.sync_started.emit()
        logger.info("Sync queue processing started.")

        pending = self.sync_repo.get_pending()
        if not pending:
            logger.info("No pending sync records.")
            self.sync_completed.emit({"synced": 0, "failed": 0, "total": 0})
            return

        api_url = Settings.SYNC_API_URL
        api_key = Settings.SYNC_API_KEY

        synced_count = 0
        failed_count = 0

        for record in pending:
            if not self._running:
                logger.info("Sync service stopped during processing.")
                break

            try:
                payload = json.loads(record.payload) if record.payload else {}
                sync_data = {
                    "id": record.id,
                    "branch_id": record.branch_id,
                    "table_name": record.table_name,
                    "record_id": record.record_id,
                    "action": record.action,
                    "payload": payload,
                    "queued_at": record.created_at.isoformat() if record.created_at else None,
                }

                if api_url:
                    headers = {"Content-Type": "application/json"}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"

                    try:
                        with httpx.Client(timeout=30) as client:
                            response = client.post(
                                api_url.rstrip("/") + "/sync",
                                json=sync_data,
                                headers=headers,
                            )
                            response.raise_for_status()
                            self.sync_repo.mark_synced(record.id)
                            synced_count += 1
                            logger.debug("Synced record %d (%s.%s)", record.id, record.table_name, record.record_id)
                    except httpx.TimeoutException:
                        logger.warning("Sync timeout for record %d; will retry.", record.id)
                        self.sync_repo.mark_failed(record.id, "Timeout")
                        failed_count += 1
                    except httpx.HTTPStatusError as e:
                        msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                        logger.warning("Sync failed for record %d: %s", record.id, msg)
                        self.sync_repo.mark_failed(record.id, msg)
                        failed_count += 1
                    except httpx.RequestError as e:
                        msg = f"Connection error: {e}"
                        logger.warning("Sync failed for record %d: %s", record.id, msg)
                        self.sync_repo.mark_failed(record.id, msg)
                        failed_count += 1
                else:
                    logger.info(
                        "No SYNC_API_URL configured. Record %d (%s.%s) left as PENDING.",
                        record.id, record.table_name, record.record_id,
                    )
                    synced_count += 1

            except Exception as e:
                logger.error("Unexpected error processing sync record %d: %s", record.id, e)
                self.sync_repo.mark_failed(record.id, str(e)[:500])
                failed_count += 1

        summary = {
            "synced": synced_count,
            "failed": failed_count,
            "total": len(pending),
        }

        logger.info("Sync processing complete: %s", summary)

        if failed_count > 0:
            self.sync_error.emit(f"{failed_count} of {len(pending)} records failed to sync.")
        else:
            self.sync_completed.emit(summary)

    def queue_record(self, branch_id: int | None, action: str, table_name: str, record_id: int, payload: dict | None = None):
        self.sync_repo.add(branch_id, table_name, record_id, action, payload)
        logger.info("Queued sync: %s %s.%s (branch=%s)", action, table_name, record_id, branch_id)

    def get_sync_status(self) -> dict:
        return self.sync_repo.get_status_summary()
