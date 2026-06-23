from datetime import datetime

from sqlalchemy import func, select

from src.database.connection import db_manager
from src.database.models import AuditLog, SyncQueue
from src.repositories.base import BaseRepository


class SyncQueueRepository(BaseRepository):
    def __init__(self):
        super().__init__(SyncQueue)

    def get_pending_syncs(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(SyncQueue)
                    .where(SyncQueue.branch_id == branch_id)
                    .where(SyncQueue.status == "PENDING")
                    .order_by(SyncQueue.created_at)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(SyncQueue)
                .where(SyncQueue.branch_id == branch_id)
                .where(SyncQueue.status == "PENDING")
                .order_by(SyncQueue.created_at)
            )
            return session.execute(stmt).scalars().all()

    def get_failed_syncs(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(SyncQueue)
                    .where(SyncQueue.branch_id == branch_id)
                    .where(SyncQueue.status == "FAILED")
                    .order_by(SyncQueue.created_at.desc())
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(SyncQueue)
                .where(SyncQueue.branch_id == branch_id)
                .where(SyncQueue.status == "FAILED")
                .order_by(SyncQueue.created_at.desc())
            )
            return session.execute(stmt).scalars().all()

    def add_to_queue(
        self, session, branch_id, action, table_name, record_id, payload
    ):
        entry = SyncQueue(
            branch_id=branch_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            payload=payload,
            status="PENDING",
        )
        session.add(entry)
        session.flush()
        return entry

    def mark_synced(self, session, queue_id):
        stmt = select(SyncQueue).where(SyncQueue.id == queue_id)
        entry = session.execute(stmt).scalar_one_or_none()
        if entry is None:
            return None
        entry.status = "SYNCED"
        entry.synced_at = datetime.now()
        session.flush()
        return entry

    def mark_failed(self, session, queue_id, error_message):
        stmt = select(SyncQueue).where(SyncQueue.id == queue_id)
        entry = session.execute(stmt).scalar_one_or_none()
        if entry is None:
            return None
        entry.status = "FAILED"
        entry.error_message = error_message
        session.flush()
        return entry

    def get_unsynced_count(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(func.count()).select_from(SyncQueue).where(
                    SyncQueue.branch_id == branch_id,
                    SyncQueue.status == "PENDING",
                )
                return session.execute(stmt).scalar()
        else:
            stmt = select(func.count()).select_from(SyncQueue).where(
                SyncQueue.branch_id == branch_id,
                SyncQueue.status == "PENDING",
            )
            return session.execute(stmt).scalar()


class AuditLogRepository(BaseRepository):
    def __init__(self):
        super().__init__(AuditLog)

    def log_action(
        self,
        session,
        user_id,
        branch_id,
        action,
        resource,
        resource_id,
        details,
        ip_address=None,
    ):
        log = AuditLog(
            user_id=user_id,
            branch_id=branch_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        session.add(log)
        session.flush()
        return log

    def get_logs(
        self,
        branch_id,
        start_date=None,
        end_date=None,
        action=None,
        session=None,
    ):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(AuditLog).where(
                    AuditLog.branch_id == branch_id
                )
                if start_date:
                    stmt = stmt.where(
                        AuditLog.created_at >= start_date
                    )
                if end_date:
                    stmt = stmt.where(
                        AuditLog.created_at <= end_date
                    )
                if action:
                    stmt = stmt.where(AuditLog.action == action)
                stmt = stmt.order_by(AuditLog.created_at.desc())
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(AuditLog).where(
                AuditLog.branch_id == branch_id
            )
            if start_date:
                stmt = stmt.where(
                    AuditLog.created_at >= start_date
                )
            if end_date:
                stmt = stmt.where(
                    AuditLog.created_at <= end_date
                )
            if action:
                stmt = stmt.where(AuditLog.action == action)
            stmt = stmt.order_by(AuditLog.created_at.desc())
            return session.execute(stmt).scalars().all()

    def get_user_activity(self, user_id, limit=50, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(AuditLog)
                    .where(AuditLog.user_id == user_id)
                    .order_by(AuditLog.created_at.desc())
                    .limit(limit)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(AuditLog.created_at.desc())
                .limit(limit)
            )
            return session.execute(stmt).scalars().all()
