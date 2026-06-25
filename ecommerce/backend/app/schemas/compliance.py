from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampMixin


class ComplianceIncidentResponse(TimestampMixin):
    id: int
    incident_type: str
    customer_id: int | None = None
    rider_id: int | None = None
    order_id: int | None = None
    branch_id: int | None = None
    description: str
    rider_notes: str | None = None
    resolution_status: str = "open"
    resolved_by: int | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ComplianceIncidentCreate(BaseModel):
    incident_type: str
    customer_id: int | None = None
    rider_id: int | None = None
    order_id: int | None = None
    branch_id: int | None = None
    description: str
    rider_notes: str | None = None


class ComplianceIncidentResolve(BaseModel):
    resolution_status: str = "resolved"
    notes: str | None = None


class ComplianceAuditLogResponse(BaseModel):
    id: int
    customer_id: int | None = None
    event_type: str
    description: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
