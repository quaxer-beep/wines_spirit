from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.head_office import (
    HeadOfficeDashboard, BranchSummary, RevenueTrend,
    ProductPerformance, BrandPerformance, ExecutiveKPI,
    PaginatedResponse,
)
from app.services.head_office.analytics_engine import AnalyticsEngine
from app.services.head_office.forecasting_engine import ForecastingEngine

router = APIRouter(prefix="/dashboard", tags=["Head Office - Dashboard"])


@router.get("/overview", response_model=HeadOfficeDashboard)
async def head_office_overview(db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    return await engine.get_dashboard()


@router.get("/branches", response_model=list[BranchSummary])
async def branch_comparison(db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    branches = await engine.get_branch_comparison()
    return [BranchSummary(**b) for b in branches]


@router.get("/revenue-trends", response_model=list[RevenueTrend])
async def revenue_trends(days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    return await engine.get_revenue_trends(days)


@router.get("/products", response_model=PaginatedResponse)
async def product_performance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    engine = AnalyticsEngine(db)
    products, total = await engine.get_product_performance(page, page_size, category)
    return {
        "items": [ProductPerformance.model_validate(p).model_dump() for p in products],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/brands", response_model=list[BrandPerformance])
async def brand_performance(db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    return await engine.get_brand_performance()


@router.get("/executive-kpi", response_model=ExecutiveKPI)
async def executive_kpi(db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    return await engine.get_executive_kpi()


@router.post("/snapshot")
async def take_snapshot(db: AsyncSession = Depends(get_db)):
    engine = AnalyticsEngine(db)
    snapshot = await engine.take_snapshot()
    await db.commit()
    return {"message": "Snapshot taken", "snapshot_date": str(snapshot.snapshot_date)}


@router.get("/stock-classification")
async def stock_classification(db: AsyncSession = Depends(get_db)):
    engine = ForecastingEngine(db)
    return await engine.get_stock_movement_classification()


@router.get("/reorder-recommendations")
async def reorder_recommendations(db: AsyncSession = Depends(get_db)):
    engine = ForecastingEngine(db)
    return await engine.get_reorder_recommendations()


@router.get("/dead-stock")
async def dead_stock(days: int = Query(30, ge=1), db: AsyncSession = Depends(get_db)):
    engine = ForecastingEngine(db)
    return await engine.get_dead_stock(days)
