from __future__ import annotations

import csv
import io
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_csv(self, report_type: str, period_start: date, period_end: date) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "sales":
            writer.writerow(["Date", "Order Number", "Branch", "Customer", "Items", "Subtotal", "Discount", "Tax", "Total", "Status"])
            result = await self.db.execute(
                text("""
                    SELECT o.created_at, o.order_number, o.branch_id,
                           c.full_name AS customer,
                           COUNT(oi.id) AS items,
                           o.subtotal, o.discount, o.tax, o.grand_total, o.status
                    FROM orders o
                    LEFT JOIN customers c ON c.id = o.customer_id
                    LEFT JOIN order_items oi ON oi.order_id = o.id
                    WHERE DATE(o.created_at) BETWEEN :start AND :end
                    GROUP BY o.id, o.order_number, o.branch_id, c.full_name,
                             o.subtotal, o.discount, o.tax, o.grand_total, o.status, o.created_at
                    ORDER BY o.created_at
                """),
                {"start": period_start, "end": period_end},
            )
            for row in result.all():
                writer.writerow([str(r) if r is not None else "" for r in row])

        elif report_type == "inventory":
            writer.writerow(["Product", "Brand", "Category", "Branch", "Quantity On Hand", "Cost Price", "Selling Price", "Stock Value"])
            result = await self.db.execute(
                text("""
                    SELECT p.name, p.brand, p.category, i.branch_id,
                           i.quantity_on_hand, p.cost_price, p.selling_price,
                           i.quantity_on_hand * p.cost_price AS stock_value
                    FROM inventory i
                    JOIN products p ON p.id = i.product_id
                    WHERE p.is_active = 1
                    ORDER BY stock_value DESC
                """)
            )
            for row in result.all():
                writer.writerow([str(r) if r is not None else "" for r in row])

        elif report_type == "expenses":
            writer.writerow(["Date", "Branch", "Category", "Description", "Amount", "Recorded By"])
            result = await self.db.execute(
                text("""
                    SELECT e.expense_date, e.branch_id, e.category,
                           e.description, e.amount, e.recorded_by
                    FROM expenses e
                    WHERE DATE(e.expense_date) BETWEEN :start AND :end
                    ORDER BY e.expense_date
                """),
                {"start": period_start, "end": period_end},
            )
            for row in result.all():
                writer.writerow([str(r) if r is not None else "" for r in row])

        elif report_type == "branch_summary":
            writer.writerow(["Branch", "Total Sales", "Total Orders", "Gross Profit", "Expenses", "Net Profit"])
            result = await self.db.execute(
                text("""
                    SELECT
                        b.name,
                        COALESCE(SUM(s.grand_total), 0) AS total_sales,
                        COUNT(DISTINCT s.id) AS total_orders,
                        COALESCE(SUM(s.grand_total) - SUM(si.quantity * p.cost_price), 0) AS gross_profit,
                        COALESCE((SELECT SUM(amount) FROM expenses e WHERE e.branch_id = b.id), 0) AS expenses,
                        COALESCE(SUM(s.grand_total) - SUM(si.quantity * p.cost_price), 0) -
                            COALESCE((SELECT SUM(amount) FROM expenses e WHERE e.branch_id = b.id), 0) AS net_profit
                    FROM branches b
                    LEFT JOIN sales s ON s.branch_id = b.id AND s.status = 'COMPLETED'
                        AND DATE(s.created_at) BETWEEN :start AND :end
                    LEFT JOIN sale_items si ON si.sale_id = s.id
                    LEFT JOIN products p ON p.id = si.product_id
                    WHERE b.is_active = 1
                    GROUP BY b.id, b.name
                    ORDER BY total_sales DESC
                """),
                {"start": period_start, "end": period_end},
            )
            for row in result.all():
                writer.writerow([str(r) if r is not None else "" for r in row])

        elif report_type == "supplier_performance":
            writer.writerow(["Supplier", "Total Orders", "Total Value", "Avg Delay (Days)", "Overall Rating"])
            result = await self.db.execute(
                text("""
                    SELECT
                        s.name,
                        COUNT(po.id) AS total_orders,
                        COALESCE(SUM(po.grand_total), 0) AS total_value,
                        COALESCE(AVG(
                            CASE WHEN po.actual_delivery_date IS NOT NULL AND po.expected_delivery_date IS NOT NULL
                            THEN po.actual_delivery_date - po.expected_delivery_date
                            ELSE NULL END
                        ), 0) AS avg_delay,
                        COALESCE(AVG(sr.overall_score), 0) AS avg_rating
                    FROM suppliers s
                    LEFT JOIN purchase_orders po ON po.supplier_id = s.id
                    LEFT JOIN supplier_ratings sr ON sr.supplier_id = s.id
                    WHERE s.is_active = 1
                    GROUP BY s.id, s.name
                    ORDER BY avg_rating DESC
                """)
            )
            for row in result.all():
                writer.writerow([str(r) if r is not None else "" for r in row])

        return output.getvalue()

    async def generate_pdf_html(self, report_type: str, period_start: date, period_end: date) -> str:
        csv_data = await self.generate_csv(report_type, period_start, period_end)
        lines = csv_data.strip().split("\n")
        if not lines:
            return "<p>No data available.</p>"

        headers = lines[0].split(",")
        rows = [line.split(",") for line in lines[1:]]

        html = [
            "<html><head><style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #1a237e; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 20px; }",
            "th { background: #1a237e; color: white; padding: 8px; text-align: left; }",
            "td { padding: 6px; border-bottom: 1px solid #ddd; }",
            "tr:nth-child(even) { background: #f5f5f5; }",
            f"<h1>Report: {report_type.replace('_', ' ').title()}</h1>",
            f"<p>Period: {period_start} to {period_end}</p>",
            f"<p>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>",
            "<table><tr>",
        ]
        for h in headers:
            html.append(f"<th>{h.strip()}</th>")
        html.append("</tr>")
        for row in rows:
            html.append("<tr>")
            for cell in row:
                html.append(f"<td>{cell.strip()}</td>")
            html.append("</tr>")
        html.append("</table></body></html>")
        return "\n".join(html)
