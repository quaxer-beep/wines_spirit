from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.head_office import ExecutiveReport, AuditEvent
from app.schemas.head_office import AuditEventResponse, PaginatedResponse
from app.services.head_office.analytics_engine import AnalyticsEngine
from app.services.head_office.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Head Office - Reports"])


@router.get("/{report_type}/csv")
async def export_csv(
    report_type: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    valid_types = {"sales", "inventory", "expenses", "branch_summary", "supplier_performance"}
    if report_type not in valid_types:
        raise HTTPException(400, f"Invalid report type. Valid: {', '.join(valid_types)}")
    service = ReportService(db)
    csv_data = await service.generate_csv(report_type, period_start, period_end)
    return PlainTextResponse(
        csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}_{period_start}_{period_end}.csv"},
    )


@router.get("/{report_type}/pdf")
async def export_pdf(
    report_type: str,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    valid_types = {"sales", "inventory", "expenses", "branch_summary", "supplier_performance"}
    if report_type not in valid_types:
        raise HTTPException(400, f"Invalid report type. Valid: {', '.join(valid_types)}")
    service = ReportService(db)
    html = await service.generate_pdf_html(report_type, period_start, period_end)
    return HTMLResponse(html)


@router.post("/executive", response_model=dict)
async def generate_executive_report(
    report_type: str = Query("monthly"),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    today = date.today()
    if report_type == "daily":
        period_start = today
        period_end = today
    elif report_type == "weekly":
        period_start = today - timedelta(days=today.weekday())
        period_end = period_start + timedelta(days=6)
    elif report_type == "monthly":
        period_start = today.replace(day=1)
        period_end = today
    elif report_type == "quarterly":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        period_start = today.replace(month=quarter_month, day=1)
        period_end = today
    elif report_type == "annual":
        period_start = today.replace(month=1, day=1)
        period_end = today
    else:
        raise HTTPException(400, "Invalid report type. Use: daily, weekly, monthly, quarterly, annual")

    engine = AnalyticsEngine(db)
    report = await engine.generate_executive_report(report_type, period_start, period_end)
    await db.commit()
    return {
        "id": report.id,
        "report_type": report.report_type,
        "period_start": str(report.period_start),
        "period_end": str(report.period_end),
        "total_revenue": report.total_revenue,
        "gross_profit": report.gross_profit,
        "net_profit": report.net_profit,
        "operating_expenses": report.operating_expenses,
        "inventory_value": report.inventory_value,
        "customer_growth": report.customer_growth,
        "online_sales_growth": report.online_sales_growth,
        "generated_at": report.generated_at.isoformat(),
    }


@router.get("/executive/history", response_model=PaginatedResponse)
async def executive_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(ExecutiveReport).order_by(ExecutiveReport.generated_at.desc())
    count_query = select(__import__("sqlalchemy").func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()
    return {
        "items": [
            {
                "id": r.id,
                "report_type": r.report_type,
                "period_start": str(r.period_start),
                "period_end": str(r.period_end),
                "total_revenue": r.total_revenue,
                "gross_profit": r.gross_profit,
                "net_profit": r.net_profit,
                "generated_at": r.generated_at.isoformat(),
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/audit-log", response_model=PaginatedResponse)
async def audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = Query(None),
    resource_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)
    count_query = select(__import__("sqlalchemy").func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    events = result.scalars().all()
    return {
        "items": [AuditEventResponse.model_validate(e).model_dump() for e in events],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }
