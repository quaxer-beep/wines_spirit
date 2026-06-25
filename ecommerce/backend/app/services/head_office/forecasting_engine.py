from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Order, OrderItem
from app.models.head_office import Forecast, AnalyticsSnapshot

logger = logging.getLogger(__name__)


class ForecastingEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_demand(
        self, product_id: int | None = None, branch_id: int | None = None, days_ahead: int = 30
    ) -> list[Forecast]:
        today = date.today()
        lookback = 90
        since = today - timedelta(days=lookback)

        query = text("""
            SELECT
                DATE(o.created_at) AS sale_date,
                COALESCE(SUM(oi.quantity), 0) AS daily_quantity,
                COUNT(DISTINCT o.id) AS daily_orders
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.payment_status = 'paid'
              AND o.created_at >= :since
              AND (:product_id IS NULL OR oi.product_id = :product_id)
              AND (:branch_id IS NULL OR o.branch_id = :branch_id)
            GROUP BY DATE(o.created_at)
            ORDER BY sale_date
        """)

        result = await self.db.execute(
            query,
            {"since": since, "product_id": product_id, "branch_id": branch_id},
        )
        rows = result.all()

        if not rows:
            avg_daily = 0
            trend = 0
        else:
            quantities = [float(r[1]) for r in rows]
            avg_daily = sum(quantities) / len(quantities) if quantities else 0

            if len(quantities) > 1:
                x = list(range(len(quantities)))
                n = len(quantities)
                x_mean = sum(x) / n
                y_mean = sum(quantities) / n
                num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, quantities))
                den = sum((xi - x_mean) ** 2 for xi in x)
                trend = num / den if den != 0 else 0
            else:
                trend = 0

        forecasts = []
        for day_offset in range(1, days_ahead + 1):
            forecast_date = today + timedelta(days=day_offset)
            predicted = max(avg_daily + (trend * day_offset), 0)
            std = avg_daily * 0.2 if avg_daily > 0 else 0

            forecast = Forecast(
                forecast_date=forecast_date,
                branch_id=branch_id,
                product_id=product_id,
                forecast_type="demand",
                predicted_value=round(predicted, 2),
                confidence_lower=round(max(predicted - 1.96 * std, 0), 2),
                confidence_upper=round(predicted + 1.96 * std, 2),
                model_used="linear_trend",
            )
            self.db.add(forecast)
            forecasts.append(forecast)

        await self.db.flush()
        return forecasts

    async def predict_revenue(
        self, branch_id: int | None = None, days_ahead: int = 90
    ) -> list[Forecast]:
        today = date.today()
        lookback = 180
        since = today - timedelta(days=lookback)

        result = await self.db.execute(
            select(
                func.date(Order.created_at).label("sale_date"),
                func.coalesce(func.sum(Order.grand_total), 0).label("daily_revenue"),
            )
            .where(
                Order.payment_status == "paid",
                Order.created_at >= since,
                branch_id is None or Order.branch_id == branch_id,
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        rows = result.all()

        if not rows:
            avg_daily = 0
            trend = 0
        else:
            revenues = [float(r[1]) for r in rows]
            avg_daily = sum(revenues) / len(revenues) if revenues else 0

            if len(revenues) > 1:
                x = list(range(len(revenues)))
                n = len(revenues)
                x_mean = sum(x) / n
                y_mean = sum(revenues) / n
                num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, revenues))
                den = sum((xi - x_mean) ** 2 for xi in x)
                trend = num / den if den != 0 else 0
            else:
                trend = 0

        forecasts = []
        for day_offset in range(1, days_ahead + 1):
            forecast_date = today + timedelta(days=day_offset)
            predicted = max(avg_daily + (trend * day_offset), 0)
            std = avg_daily * 0.15 if avg_daily > 0 else 0

            forecast = Forecast(
                forecast_date=forecast_date,
                branch_id=branch_id,
                forecast_type="revenue",
                predicted_value=round(predicted, 2),
                confidence_lower=round(max(predicted - 1.96 * std, 0), 2),
                confidence_upper=round(predicted + 1.96 * std, 2),
                model_used="linear_trend",
            )
            self.db.add(forecast)
            forecasts.append(forecast)

        await self.db.flush()
        return forecasts

    async def get_stock_movement_classification(self) -> list[dict]:
        today = date.today()
        result = await self.db.execute(
            text("""
                SELECT
                    p.id AS product_id,
                    p.name AS product_name,
                    p.brand,
                    COALESCE(SUM(oi.quantity), 0) AS total_sold_90d,
                    COUNT(DISTINCT oi.id) AS sale_events,
                    MAX(o.created_at) AS last_sold_date
                FROM products p
                LEFT JOIN order_items oi ON oi.product_id = p.id
                LEFT JOIN orders o ON o.id = oi.order_id AND o.payment_status = 'paid'
                    AND o.created_at >= :since
                WHERE p.is_active = 1
                GROUP BY p.id, p.name, p.brand
                ORDER BY total_sold_90d DESC
            """),
            {"since": today - timedelta(days=90)},
        )
        rows = result.all()
        classifications = []
        for row in rows:
            last_sold = row[4]
            days_since_sale = (today - last_sold.date()).days if last_sold else 999
            qty = float(row[3] or 0)

            if qty == 0 and days_since_sale > 90:
                classification = "dead_stock"
            elif qty <= 5 or days_since_sale > 60:
                classification = "slow_moving"
            elif qty <= 20 or days_since_sale > 30:
                classification = "medium_moving"
            else:
                classification = "fast_moving"

            classifications.append({
                "product_id": row[0],
                "product_name": row[1],
                "brand": row[2],
                "total_sold_90d": qty,
                "last_sold_date": last_sold.isoformat() if last_sold else None,
                "days_since_sale": days_since_sale,
                "classification": classification,
            })
        return classifications

    async def get_reorder_recommendations(self) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    p.id AS product_id,
                    p.name AS product_name,
                    p.brand,
                    p.reorder_level,
                    COALESCE(i.quantity_on_hand, 0) AS current_stock,
                    COALESCE(AVG(ds.daily_qty), 0) AS avg_daily_sales
                FROM products p
                LEFT JOIN inventory i ON i.product_id = p.id
                LEFT JOIN (
                    SELECT oi.product_id,
                           SUM(oi.quantity) / 90.0 AS daily_qty
                    FROM order_items oi
                    JOIN orders o ON o.id = oi.order_id
                    WHERE o.payment_status = 'paid'
                      AND o.created_at >= :since
                    GROUP BY oi.product_id
                ) ds ON ds.product_id = p.id
                WHERE p.is_active = 1
                GROUP BY p.id, p.name, p.brand, p.reorder_level, i.quantity_on_hand
                HAVING current_stock <= p.reorder_level
                ORDER BY (p.reorder_level - current_stock) DESC
            """),
            {"since": datetime.now(timezone.utc) - timedelta(days=90)},
        )
        rows = result.all()
        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "brand": row[2],
                "reorder_level": float(row[3] or 0),
                "current_stock": float(row[4] or 0),
                "avg_daily_sales": round(float(row[5] or 0), 2),
                "recommended_order_qty": max(
                    int(float(row[3]) - float(row[4]) + (float(row[5] or 0) * 7)),
                    0,
                ),
            }
            for row in rows
        ]

    async def get_dead_stock(self, days_threshold: int = 30) -> list[dict]:
        classifications = await self.get_stock_movement_classification()
        return [
            c for c in classifications
            if c["days_since_sale"] >= days_threshold
        ]
