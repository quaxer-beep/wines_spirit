from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer
from app.schemas.common import MessageResponse
from app.services.compliance_service import ComplianceService

router = APIRouter()


@router.get("/incidents")
async def list_incidents(
    status_filter: str | None = None,
    incident_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    incidents, total = await service.get_incidents(
        status=status_filter,
        incident_type=incident_type,
        page=page,
        page_size=page_size,
    )
    return {
        "items": incidents,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.put("/incidents/{incident_id}/resolve", response_model=MessageResponse)
async def resolve_incident(
    incident_id: int,
    notes: str | None = None,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    try:
        await service.resolve_incident(incident_id, admin.id, notes=notes)
        await db.commit()
        return MessageResponse(message="Incident resolved")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/audit-logs")
async def list_audit_logs(
    event_type: str | None = None,
    customer_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = ComplianceService(db)
    logs, total = await service.get_audit_logs(
        event_type=event_type,
        customer_id=customer_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }
