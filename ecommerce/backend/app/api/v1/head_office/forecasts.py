from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.head_office import Forecast
from app.services.head_office.forecasting_engine import ForecastingEngine

router = APIRouter(prefix="/forecasts", tags=["Head Office - Forecasting"])


@router.post("/demand")
async def forecast_demand(
    product_id: int | None = Query(None),
    branch_id: int | None = Query(None),
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    engine = ForecastingEngine(db)
    forecasts = await engine.predict_demand(product_id, branch_id, days_ahead)
    await db.commit()
    return [
        {
            "forecast_date": str(f.forecast_date),
            "predicted_value": f.predicted_value,
            "confidence_lower": f.confidence_lower,
            "confidence_upper": f.confidence_upper,
        }
        for f in forecasts
    ]


@router.post("/revenue")
async def forecast_revenue(
    branch_id: int | None = Query(None),
    days_ahead: int = Query(90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    engine = ForecastingEngine(db)
    forecasts = await engine.predict_revenue(branch_id, days_ahead)
    await db.commit()
    return [
        {
            "forecast_date": str(f.forecast_date),
            "predicted_value": f.predicted_value,
            "confidence_lower": f.confidence_lower,
            "confidence_upper": f.confidence_upper,
        }
        for f in forecasts
    ]


@router.get("/history")
async def forecast_history(
    forecast_type: str = Query("demand"),
    branch_id: int | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    query = select(Forecast).where(Forecast.forecast_type == forecast_type)
    if branch_id:
        query = query.where(Forecast.branch_id == branch_id)
    query = query.order_by(Forecast.forecast_date.desc()).limit(limit)
    result = await db.execute(query)
    forecasts = result.scalars().all()
    return [
        {
            "id": f.id,
            "forecast_date": str(f.forecast_date),
            "predicted_value": f.predicted_value,
            "actual_value": f.actual_value,
            "model_used": f.model_used,
            "created_at": f.created_at.isoformat(),
        }
        for f in forecasts
    ]
