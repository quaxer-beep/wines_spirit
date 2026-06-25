from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import (
    ComplianceAuditLog,
    ComplianceIncident,
    Order,
)
from app.schemas.compliance import ComplianceIncidentCreate


class ComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_incident(
        self, data: ComplianceIncidentCreate
    ) -> ComplianceIncident:
        incident = ComplianceIncident(
            incident_type=data.incident_type,
            customer_id=data.customer_id,
            rider_id=data.rider_id,
            order_id=data.order_id,
            branch_id=data.branch_id,
            description=data.description,
            rider_notes=data.rider_notes,
            resolution_status="open",
        )
        self.db.add(incident)
        await self.db.flush()
        return incident

    async def resolve_incident(
        self, incident_id: int, resolved_by: int,
        resolution_status: str = "resolved",
        notes: str | None = None
    ) -> ComplianceIncident:
        result = await self.db.execute(
            select(ComplianceIncident).where(ComplianceIncident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            raise ValueError("Incident not found")

        incident.resolution_status = resolution_status
        incident.resolved_by = resolved_by
        incident.resolved_at = datetime.now(timezone.utc)
        if notes:
            incident.description = f"{incident.description}\n\nResolution notes: {notes}"

        await self.db.flush()
        return incident

    async def get_incidents(
        self, status: str | None = None, incident_type: str | None = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[ComplianceIncident], int]:
        query = select(ComplianceIncident)
        if status:
            query = query.where(ComplianceIncident.resolution_status == status)
        if incident_type:
            query = query.where(ComplianceIncident.incident_type == incident_type)
        query = query.order_by(ComplianceIncident.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def log_audit_event(
        self,
        event_type: str,
        description: str,
        customer_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata_json: str | None = None,
    ) -> ComplianceAuditLog:
        audit = ComplianceAuditLog(
            customer_id=customer_id,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=metadata_json,
        )
        self.db.add(audit)
        await self.db.flush()
        return audit

    async def get_audit_logs(
        self, event_type: str | None = None,
        customer_id: int | None = None,
        page: int = 1, page_size: int = 20
    ) -> tuple[list[ComplianceAuditLog], int]:
        query = select(ComplianceAuditLog)
        if event_type:
            query = query.where(ComplianceAuditLog.event_type == event_type)
        if customer_id:
            query = query.where(ComplianceAuditLog.customer_id == customer_id)
        query = query.order_by(ComplianceAuditLog.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
