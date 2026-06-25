from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import Alert

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        branch_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
    ) -> Alert:
        alert = Alert(
            branch_id=branch_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        self.db.add(alert)
        await self.db.flush()
        logger.info("Alert created: [%s] %s", severity, title)
        return alert

    async def list_alerts(
        self,
        page: int = 1,
        page_size: int = 20,
        branch_id: int | None = None,
        severity: str | None = None,
        unresolved: bool = False,
    ) -> tuple[list[Alert], int]:
        query = select(Alert)
        if branch_id:
            query = query.where(Alert.branch_id == branch_id)
        if severity:
            query = query.where(Alert.severity == severity)
        if unresolved:
            query = query.where(Alert.is_resolved == False)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def mark_read(self, alert_id: int) -> Alert | None:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        alert.is_read = True
        await self.db.flush()
        return alert

    async def mark_resolved(self, alert_id: int) -> Alert | None:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return alert

    async def check_and_generate_alerts(self):
        await self._check_low_stock()
        await self._check_dead_stock()
        await self._check_unusual_activity()

    async def _check_low_stock(self):
        result = await self.db.execute(
            select(func.count()).select_from(
                text("""
                    SELECT 1 FROM inventory i
                    JOIN products p ON p.id = i.product_id
                    WHERE i.quantity_on_hand <= p.reorder_level
                      AND i.quantity_on_hand > 0
                """)
            )
        )
        count = result.scalar() or 0
        if count > 0:
            existing = await self.db.execute(
                select(func.count()).where(
                    Alert.alert_type == "low_stock",
                    Alert.is_resolved == False,
                )
            )
            if (existing.scalar() or 0) == 0:
                await self.create_alert(
                    alert_type="low_stock",
                    severity="warning",
                    title="Low Stock Items Detected",
                    message=f"There are {count} products with stock at or below reorder level.",
                )

    async def _check_dead_stock(self):
        result = await self.db.execute(
            select(func.count()).select_from(
                text("""
                    SELECT 1 FROM products p
                    WHERE p.is_active = 1
                      AND p.id NOT IN (
                          SELECT oi.product_id FROM order_items oi
                          JOIN orders o ON o.id = oi.order_id
                          WHERE o.payment_status = 'paid'
                            AND o.created_at >= :since
                      )
                """)
            ),
            {"since": datetime.now(timezone.utc).replace(day=1) - __import__("datetime").timedelta(days=90)},
        )
        count = result.scalar() or 0
        if count > 0:
            existing = await self.db.execute(
                select(func.count()).where(
                    Alert.alert_type == "dead_stock",
                    Alert.is_resolved == False,
                )
            )
            if (existing.scalar() or 0) == 0:
                await self.create_alert(
                    alert_type="dead_stock",
                    severity="info",
                    title="Dead Stock Detected",
                    message=f"There are {count} products with no sales in the past 90 days.",
                )

    async def _check_unusual_activity(self):
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.db.execute(
            select(func.coalesce(func.sum(text("grand_total")), 0)).where(
                text("created_at >= :today AND payment_status = 'paid'"),
                today=today_start,
            )
        )
        today_sales = float(result.scalar() or 0)

        result = await self.db.execute(
            select(func.coalesce(func.avg(text("grand_total")), 0)).where(
                text("""
                    created_at >= :week_ago
                    AND created_at < :today
                    AND payment_status = 'paid'
                """),
                week_ago=today_start - __import__("datetime").timedelta(days=7),
                today=today_start,
            )
        )
        avg_daily = float(result.scalar() or 0)

        if avg_daily > 0 and (today_sales > avg_daily * 2 or today_sales < avg_daily * 0.3):
            direction = "surge" if today_sales > avg_daily * 2 else "drop"
            severity = "warning" if direction == "drop" else "info"
            await self.create_alert(
                alert_type="unusual_activity",
                severity=severity,
                title=f"Unusual Sales Activity: {direction.title()}",
                message=f"Today's sales (KES {today_sales:,.0f}) differ significantly from daily average (KES {avg_daily:,.0f}).",
            )
