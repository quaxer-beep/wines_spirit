from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.head_office import AlertResponse, PaginatedResponse
from app.services.head_office.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Head Office - Alerts"])


@router.get("", response_model=PaginatedResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    branch_id: int | None = Query(None),
    severity: str | None = Query(None),
    unresolved: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    service = AlertService(db)
    alerts, total = await service.list_alerts(page, page_size, branch_id, severity, unresolved)
    return {
        "items": [AlertResponse.model_validate(a).model_dump() for a in alerts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(alert_id: int, db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    alert = await service.mark_read(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.commit()
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    alert = await service.mark_resolved(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.commit()
    return alert


@router.post("/check")
async def run_alert_checks(db: AsyncSession = Depends(get_db)):
    service = AlertService(db)
    await service.check_and_generate_alerts()
    await db.commit()
    return {"message": "Alert checks completed"}
