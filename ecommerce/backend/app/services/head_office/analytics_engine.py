from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Order, OrderItem, Product, Customer
from app.models.head_office import AnalyticsSnapshot, ExecutiveReport
from app.schemas.head_office import (
    BrandPerformance,
    ExecutiveKPI,
    HeadOfficeDashboard,
    ProductPerformance,
    RevenueTrend,
)
from app.services.head_office.alert_service import AlertService

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.alert_service = AlertService(db)

    async def get_dashboard(self) -> HeadOfficeDashboard:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        year_start = today_start.replace(month=1, day=1)

        today_result = await self.db.execute(
            select(
                func.coalesce(func.count(), 0),
                func.coalesce(func.sum(Order.grand_total), 0),
            ).where(
                Order.created_at >= today_start,
                Order.payment_status == "paid",
            )
        )
        today_orders, today_revenue = today_result.first() or (0, 0)

        week_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.created_at >= week_start,
                Order.payment_status == "paid",
            )
        )
        week_revenue = week_result.scalar() or 0

        month_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.created_at >= month_start,
                Order.payment_status == "paid",
            )
        )
        month_revenue = month_result.scalar() or 0

        year_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.created_at >= year_start,
                Order.payment_status == "paid",
            )
        )
        year_revenue = year_result.scalar() or 0

        branch_revenue = await self.db.execute(
            select(
                Order.branch_id,
                func.coalesce(func.sum(Order.grand_total), 0).label("revenue"),
                func.count().label("orders"),
            )
            .where(
                Order.payment_status == "paid",
                Order.created_at >= month_start,
            )
            .group_by(Order.branch_id)
            .order_by(func.sum(Order.grand_total).desc())
        )
        revenue_by_branch = [
            {"branch_id": row[0], "revenue": float(row[1]), "orders": row[2]}
            for row in branch_revenue.all()
        ]

        category_revenue = await self.db.execute(
            text("""
                SELECT COALESCE(c.name, 'Uncategorized') AS category,
                       SUM(oi.subtotal) AS revenue
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                LEFT JOIN products p ON p.id = oi.product_id
                LEFT JOIN categories c ON c.id = p.category_id
                WHERE o.payment_status = 'paid'
                  AND o.created_at >= :month_start
                GROUP BY c.name
                ORDER BY revenue DESC
            """),
            {"month_start": month_start},
        )
        revenue_by_category = [{"category": row[0], "revenue": float(row[1])} for row in category_revenue.all()]

        brand_revenue = await self.db.execute(
            text("""
                SELECT COALESCE(p.brand, 'Unknown') AS brand,
                       SUM(oi.subtotal) AS revenue
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                LEFT JOIN products p ON p.id = oi.product_id
                WHERE o.payment_status = 'paid'
                  AND o.created_at >= :month_start
                GROUP BY p.brand
                ORDER BY revenue DESC
            """),
            {"month_start": month_start},
        )
        revenue_by_brand = [{"brand": row[0], "revenue": float(row[1])} for row in brand_revenue.all()]

        payment_result = await self.db.execute(
            text("""
                SELECT pm.method, SUM(pm.amount) AS revenue
                FROM payments pm
                JOIN orders o ON o.id = pm.order_id
                WHERE o.payment_status = 'paid'
                  AND o.created_at >= :month_start
                GROUP BY pm.method
                ORDER BY revenue DESC
            """),
            {"month_start": month_start},
        )
        revenue_by_payment = [{"method": row[0], "revenue": float(row[1])} for row in payment_result.all()]

        branch_count_result = await self.db.execute(
            text("SELECT COUNT(*) FROM branches WHERE is_active = 1")
        )
        branch_count = branch_count_result.scalar() or 0

        alert_count_result = await self.db.execute(
            select(func.count()).where(
                text("alerts.is_resolved = false AND alerts.is_read = false")
            )
        )
        active_alerts = alert_count_result.scalar() or 0

        return HeadOfficeDashboard(
            total_sales_today=float(today_revenue),
            total_sales_week=float(week_revenue),
            total_sales_month=float(month_revenue),
            total_sales_year=float(year_revenue),
            total_orders_today=int(today_orders),
            total_orders_week=0,
            revenue_by_branch=revenue_by_branch,
            revenue_by_category=revenue_by_category,
            revenue_by_brand=revenue_by_brand,
            revenue_by_payment_method=revenue_by_payment,
            branch_count=int(branch_count),
            active_alerts=int(active_alerts),
        )

    async def get_revenue_trends(self, days: int = 30) -> list[RevenueTrend]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.date(Order.created_at).label("date"),
                func.coalesce(func.sum(Order.grand_total), 0).label("revenue"),
                func.count().label("orders"),
            )
            .where(
                Order.payment_status == "paid",
                Order.created_at >= since,
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
        )
        return [
            RevenueTrend(date=str(row[0]), revenue=float(row[1]), orders=int(row[2]))
            for row in result.all()
        ]

    async def get_branch_comparison(self) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT
                    b.id, b.name, b.code,
                    COALESCE(SUM(s.grand_total), 0) AS total_sales,
                    COUNT(DISTINCT s.id) AS total_orders,
                    COALESCE(SUM(si.quantity * p.cost_price), 0) AS total_cost,
                    COALESCE(SUM(s.grand_total), 0) - COALESCE(SUM(si.quantity * p.cost_price), 0) AS gross_profit
                FROM branches b
                LEFT JOIN sales s ON s.branch_id = b.id AND s.status = 'COMPLETED'
                LEFT JOIN sale_items si ON si.sale_id = s.id
                LEFT JOIN products p ON p.id = si.product_id
                WHERE b.is_active = 1
                GROUP BY b.id, b.name, b.code
                ORDER BY total_sales DESC
            """)
        )
        return [
            {
                "branch_id": row[0],
                "branch_name": row[1],
                "branch_code": row[2],
                "total_sales": float(row[3]),
                "total_orders": int(row[4]),
                "total_cost": float(row[5]),
                "gross_profit": float(row[6]),
                "profit_margin_pct": round((float(row[6]) / float(row[3]) * 100) if float(row[3]) > 0 else 0, 2),
            }
            for row in result.all()
        ]

    async def get_product_performance(
        self, page: int = 1, page_size: int = 20, category: str | None = None
    ) -> tuple[list[ProductPerformance], int]:
        query = select(
            Product.id,
            Product.name,
            Product.brand,
            Product.category,
            func.coalesce(func.count(OrderItem.id), 0).label("times_sold"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("total_revenue"),
            func.coalesce(func.sum(OrderItem.quantity * Product.cost_price), 0).label("total_cost"),
        ).select_from(Product).outerjoin(
            OrderItem, OrderItem.product_id == Product.id
        ).outerjoin(
            Order, Order.id == OrderItem.order_id
        ).where(
            (Order.payment_status == "paid") | (Order.payment_status.is_(None)),
            Product.is_active == True,
        ).group_by(Product.id, Product.name, Product.brand, Product.category)

        if category:
            query = query.where(Product.category == category)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(func.sum(OrderItem.subtotal).desc().nullslast())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)

        products = []
        for row in result.all():
            revenue = float(row[5]) if row[5] else 0
            cost = float(row[6]) if row[6] else 0
            products.append(ProductPerformance(
                product_id=row[0],
                product_name=row[1],
                brand=row[2],
                category=row[3],
                times_sold=int(row[4] or 0),
                total_quantity=float(row[5] or 0),
                total_revenue=revenue,
                gross_profit=revenue - cost,
                profit_margin_pct=round(((revenue - cost) / revenue * 100) if revenue > 0 else 0, 2),
            ))
        return products, total

    async def get_brand_performance(self) -> list[BrandPerformance]:
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(p.brand, 'Unknown') AS brand,
                    COALESCE(SUM(oi.subtotal), 0) AS total_revenue,
                    COALESCE(SUM(oi.quantity * p.cost_price), 0) AS total_cost,
                    COALESCE(SUM(oi.quantity), 0) AS units_sold
                FROM products p
                LEFT JOIN order_items oi ON oi.product_id = p.id
                LEFT JOIN orders o ON o.id = oi.order_id AND o.payment_status = 'paid'
                GROUP BY p.brand
                ORDER BY total_revenue DESC
            """)
        )
        return [
            BrandPerformance(
                brand=row[0],
                total_revenue=float(row[1]),
                total_cost=float(row[2]),
                gross_profit=float(row[1]) - float(row[2]),
                profit_margin_pct=round(((float(row[1]) - float(row[2])) / float(row[1]) * 100) if float(row[1]) > 0 else 0, 2),
                units_sold=float(row[3]),
            )
            for row in result.all()
        ]

    async def get_executive_kpi(self) -> ExecutiveKPI:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

        revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.payment_status == "paid"
            )
        )
        total_revenue = float(revenue_result.scalar() or 0)

        cost_result = await self.db.execute(
            text("""
                SELECT COALESCE(SUM(oi.quantity * p.cost_price), 0)
                FROM order_items oi
                JOIN orders o ON o.id = oi.order_id
                JOIN products p ON p.id = oi.product_id
                WHERE o.payment_status = 'paid'
            """)
        )
        total_cost = float(cost_result.scalar() or 0)

        expense_result = await self.db.execute(
            text("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        )
        total_expenses = float(expense_result.scalar() or 0)

        customer_result = await self.db.execute(
            select(func.count()).select_from(Customer)
        )
        customer_count = int(customer_result.scalar() or 0)

        customer_last_month = await self.db.execute(
            select(func.count()).where(Customer.registration_date < month_start)
        )
        prev_count = int(customer_last_month.scalar() or 0)
        customer_growth = ((customer_count - prev_count) / prev_count * 100) if prev_count > 0 else 0

        online_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.payment_status == "paid",
                Order.created_at >= month_start,
            )
        )
        online_month = float(online_result.scalar() or 0)

        online_prev = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.payment_status == "paid",
                Order.created_at >= prev_month_start,
                Order.created_at < month_start,
            )
        )
        online_prev_val = float(online_prev.scalar() or 0)
        online_growth = ((online_month - online_prev_val) / online_prev_val * 100) if online_prev_val > 0 else 0

        avg_result = await self.db.execute(
            select(func.coalesce(func.avg(Order.grand_total), 0)).where(
                Order.payment_status == "paid"
            )
        )
        avg_order = float(avg_result.scalar() or 0)

        gross_profit = total_revenue - total_cost
        net_profit = gross_profit - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        return ExecutiveKPI(
            total_revenue=round(total_revenue, 2),
            gross_profit=round(gross_profit, 2),
            net_profit=round(net_profit, 2),
            operating_expenses=round(total_expenses, 2),
            inventory_value=round(total_cost, 2),
            customer_count=customer_count,
            customer_growth_pct=round(customer_growth, 2),
            online_sales=round(online_month, 2),
            online_sales_growth_pct=round(online_growth, 2),
            average_order_value=round(avg_order, 2),
            profit_margin_pct=round(profit_margin, 2),
        )

    async def take_snapshot(self) -> AnalyticsSnapshot:
        kpi = await self.get_executive_kpi()
        today = date.today()

        result = await self.db.execute(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.snapshot_date == today,
                AnalyticsSnapshot.branch_id.is_(None),
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.total_sales = kpi.total_revenue
            existing.gross_profit = kpi.gross_profit
            existing.net_profit = kpi.net_profit
            existing.total_expenses = kpi.operating_expenses
            existing.inventory_value = kpi.inventory_value
            existing.customer_count = kpi.customer_count
            snapshot = existing
        else:
            snapshot = AnalyticsSnapshot(
                snapshot_date=today,
                total_sales=kpi.total_revenue,
                total_orders=0,
                total_cost=0,
                gross_profit=kpi.gross_profit,
                total_expenses=kpi.operating_expenses,
                net_profit=kpi.net_profit,
                inventory_value=kpi.inventory_value,
                customer_count=kpi.customer_count,
            )
            self.db.add(snapshot)

        await self.db.flush()
        return snapshot

    async def generate_executive_report(self, report_type: str, period_start: date, period_end: date) -> ExecutiveReport:
        kpi = await self.get_executive_kpi()
        report = ExecutiveReport(
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_revenue=kpi.total_revenue,
            gross_profit=kpi.gross_profit,
            net_profit=kpi.net_profit,
            operating_expenses=kpi.operating_expenses,
            inventory_value=kpi.inventory_value,
            customer_growth=kpi.customer_growth_pct,
            online_sales_growth=kpi.online_sales_growth_pct,
        )
        self.db.add(report)
        await self.db.flush()
        await self._log_audit("executive_report", "GENERATE", report.id, f"Report generated: {report_type}")
        return report

    async def _log_audit(self, resource_type: str, event_type: str, resource_id: int, description: str):
        from app.models.head_office import AuditEvent
        event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
        )
        self.db.add(event)
