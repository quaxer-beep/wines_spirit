import json
from datetime import date, datetime, timedelta

from sqlalchemy import func

from src.config.logging_config import setup_logging
from src.config.settings import settings
from src.database.connection import db_manager
from src.database.models import (
    Expense,
    Inventory,
    Product,
    Sale,
    SaleItem,
    StockMovement,
    SyncQueue,
)
from src.utils.helpers import format_currency

logger = setup_logging(__name__)


class SaleRepository:
    def get_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            return (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) == target_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .all()
            )

    def get_by_branch_date_range(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            return (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) >= start_date,
                    func.date(Sale.created_at) <= end_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .all()
            )

    def get_by_branch_year_week(self, branch_id, year, week):
        with db_manager.get_session() as session:
            return (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    func.strftime("%Y", Sale.created_at) == str(year),
                    func.strftime("%W", Sale.created_at) == f"{int(week):02d}",
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .all()
            )

    def get_by_branch_year_month(self, branch_id, year, month):
        with db_manager.get_session() as session:
            return (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    func.strftime("%Y", Sale.created_at) == str(year),
                    func.strftime("%m", Sale.created_at) == f"{int(month):02d}",
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .all()
            )

    def get_summary_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            row = (
                session.query(
                    func.count(Sale.id).label("sale_count"),
                    func.coalesce(func.sum(Sale.grand_total), 0).label("total_sales"),
                    func.coalesce(func.sum(Sale.subtotal), 0).label("total_subtotal"),
                    func.coalesce(func.sum(Sale.tax), 0).label("total_tax"),
                )
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) == target_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .first()
            )
            return row

    def get_items_count_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            row = (
                session.query(
                    func.coalesce(func.sum(SaleItem.quantity), 0).label("items_sold"),
                )
                .select_from(Sale)
                .join(SaleItem, SaleItem.sale_id == Sale.id)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) == target_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .first()
            )
            return row

    def get_payment_breakdown_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            from src.database.models import Payment
            rows = (
                session.query(
                    Payment.method,
                    func.count(Payment.id).label("count"),
                    func.coalesce(func.sum(Payment.amount), 0).label("total"),
                )
                .select_from(Sale)
                .join(Payment, Payment.sale_id == Sale.id)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) == target_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .group_by(Payment.method)
                .all()
            )
            return rows

    def get_by_cashier_date_range(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    Sale.user_id,
                    func.count(Sale.id).label("sale_count"),
                    func.coalesce(func.sum(Sale.grand_total), 0).label("total_sales"),
                )
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) >= start_date,
                    func.date(Sale.created_at) <= end_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .group_by(Sale.user_id)
                .all()
            )
            return rows


class ExpenseRepository:
    def get_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            return (
                session.query(Expense)
                .filter(
                    Expense.branch_id == branch_id,
                    func.date(Expense.expense_date) == target_date,
                )
                .all()
            )

    def get_by_branch_date_range(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            return (
                session.query(Expense)
                .filter(
                    Expense.branch_id == branch_id,
                    func.date(Expense.expense_date) >= start_date,
                    func.date(Expense.expense_date) <= end_date,
                )
                .all()
            )

    def get_by_branch_year_month(self, branch_id, year, month):
        with db_manager.get_session() as session:
            return (
                session.query(Expense)
                .filter(
                    Expense.branch_id == branch_id,
                    func.strftime("%Y", Expense.expense_date) == str(year),
                    func.strftime("%m", Expense.expense_date) == f"{int(month):02d}",
                )
                .all()
            )

    def get_category_totals_by_branch_date(self, branch_id, target_date):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    Expense.category,
                    func.coalesce(func.sum(Expense.amount), 0).label("total"),
                )
                .filter(
                    Expense.branch_id == branch_id,
                    func.date(Expense.expense_date) == target_date,
                )
                .group_by(Expense.category)
                .all()
            )
            return rows

    def get_category_totals_by_branch_month(self, branch_id, year, month):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    Expense.category,
                    func.coalesce(func.sum(Expense.amount), 0).label("total"),
                )
                .filter(
                    Expense.branch_id == branch_id,
                    func.strftime("%Y", Expense.expense_date) == str(year),
                    func.strftime("%m", Expense.expense_date) == f"{int(month):02d}",
                )
                .group_by(Expense.category)
                .all()
            )
            return rows


class ProductRepository:
    def get_brand_sales(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    Product.brand,
                    func.count(SaleItem.id).label("units_sold"),
                    func.coalesce(func.sum(SaleItem.quantity * Product.cost_price), 0).label("total_cost"),
                    func.coalesce(func.sum(SaleItem.subtotal), 0).label("total_revenue"),
                )
                .select_from(Sale)
                .join(SaleItem, SaleItem.sale_id == Sale.id)
                .join(Product, Product.id == SaleItem.product_id)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) >= start_date,
                    func.date(Sale.created_at) <= end_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                    Product.brand.isnot(None),
                    Product.brand != "",
                )
                .group_by(Product.brand)
                .all()
            )
            return rows


class InventoryRepository:
    def get_valuation(self, branch_id):
        with db_manager.get_session() as session:
            row = (
                session.query(
                    func.coalesce(func.sum(Inventory.quantity_on_hand * Product.cost_price), 0).label("cost_value"),
                    func.coalesce(func.sum(Inventory.quantity_on_hand * Product.selling_price), 0).label("retail_value"),
                )
                .select_from(Inventory)
                .join(Product, Product.id == Inventory.product_id)
                .filter(Inventory.branch_id == branch_id)
                .first()
            )
            return row

    def get_low_stock(self, branch_id):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    Product.id,
                    Product.name,
                    Product.brand,
                    Product.barcode,
                    Product.reorder_level,
                    Inventory.quantity_on_hand,
                )
                .select_from(Inventory)
                .join(Product, Product.id == Inventory.product_id)
                .filter(
                    Inventory.branch_id == branch_id,
                    Inventory.quantity_on_hand <= Product.reorder_level,
                    Product.is_active == 1,
                )
                .all()
            )
            return rows

    def get_movements(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            rows = (
                session.query(
                    StockMovement.movement_type,
                    func.coalesce(func.sum(StockMovement.quantity), 0).label("total_quantity"),
                    func.count(StockMovement.id).label("count"),
                )
                .filter(
                    StockMovement.branch_id == branch_id,
                    func.date(StockMovement.created_at) >= start_date,
                    func.date(StockMovement.created_at) <= end_date,
                )
                .group_by(StockMovement.movement_type)
                .all()
            )
            return rows


class ReportingService:
    def __init__(self):
        self.sale_repo = SaleRepository()
        self.expense_repo = ExpenseRepository()
        self.product_repo = ProductRepository()
        self.inventory_repo = InventoryRepository()

    def get_daily_sales_report(self, branch_id: int, target_date: date | None = None) -> dict:
        target = target_date or date.today()
        target_str = target.isoformat()

        summary = self.sale_repo.get_summary_by_branch_date(branch_id, target_str)
        items = self.sale_repo.get_items_count_by_branch_date(branch_id, target_str)
        payments = self.sale_repo.get_payment_breakdown_by_branch_date(branch_id, target_str)

        payment_breakdown = {}
        for pm in payments:
            payment_breakdown[pm.method] = {
                "count": pm.count,
                "total": pm.total,
            }

        return {
            "date": target_str,
            "total_sales": float(summary.total_sales),
            "total_subtotal": float(summary.total_subtotal),
            "total_tax": float(summary.total_tax),
            "sale_count": summary.sale_count,
            "items_sold": float(items.items_sold),
            "payment_breakdown": payment_breakdown,
        }

    def get_weekly_sales_report(self, branch_id: int, year: int, week: int) -> dict:
        sales = self.sale_repo.get_by_branch_year_week(branch_id, year, week)
        daily = {}

        total_sales = 0
        total_count = 0

        for sale in sales:
            day_key = sale.created_at.date().isoformat() if hasattr(sale.created_at, "date") else str(sale.created_at)[:10]
            if day_key not in daily:
                daily[day_key] = {"total": 0, "count": 0}
            daily[day_key]["total"] += sale.grand_total
            daily[day_key]["count"] += 1
            total_sales += sale.grand_total
            total_count += 1

        return {
            "year": year,
            "week": week,
            "total_sales": total_sales,
            "sale_count": total_count,
            "daily_breakdown": daily,
        }

    def get_monthly_sales_report(self, branch_id: int, year: int, month: int) -> dict:
        sales = self.sale_repo.get_by_branch_year_month(branch_id, year, month)
        daily = {}

        total_sales = 0
        total_count = 0

        for sale in sales:
            day_key = sale.created_at.date().isoformat() if hasattr(sale.created_at, "date") else str(sale.created_at)[:10]
            if day_key not in daily:
                daily[day_key] = {"total": 0, "count": 0}
            daily[day_key]["total"] += sale.grand_total
            daily[day_key]["count"] += 1
            total_sales += sale.grand_total
            total_count += 1

        return {
            "year": year,
            "month": month,
            "total_sales": total_sales,
            "sale_count": total_count,
            "daily_breakdown": daily,
        }

    def get_sales_by_cashier(self, branch_id: int, start_date: date, end_date: date) -> list:
        rows = self.sale_repo.get_by_cashier_date_range(branch_id, start_date.isoformat(), end_date.isoformat())
        result = []
        for row in rows:
            with db_manager.get_session() as session:
                from src.database.models import User
                user = session.query(User).filter_by(id=row.user_id).first()
                cashier_name = user.full_name if user else f"User #{row.user_id}"

            result.append({
                "user_id": row.user_id,
                "cashier_name": cashier_name,
                "sale_count": row.sale_count,
                "total_sales": float(row.total_sales),
            })
        return result

    def get_daily_expenses_report(self, branch_id: int, target_date: date | None = None) -> dict:
        target = target_date or date.today()
        target_str = target.isoformat()

        expenses = self.expense_repo.get_by_branch_date(branch_id, target_str)
        categories = self.expense_repo.get_category_totals_by_branch_date(branch_id, target_str)

        category_totals = {}
        for cat in categories:
            category_totals[cat.category] = float(cat.total)

        total_expenses = sum(e.amount for e in expenses)

        return {
            "date": target_str,
            "total_expenses": total_expenses,
            "expense_count": len(expenses),
            "category_breakdown": category_totals,
        }

    def get_monthly_expenses_report(self, branch_id: int, year: int, month: int) -> dict:
        expenses = self.expense_repo.get_by_branch_year_month(branch_id, year, month)
        categories = self.expense_repo.get_category_totals_by_branch_month(branch_id, year, month)

        category_totals = {}
        for cat in categories:
            category_totals[cat.category] = float(cat.total)

        daily = {}
        for exp in expenses:
            day_key = exp.expense_date.date().isoformat() if hasattr(exp.expense_date, "date") else str(exp.expense_date)[:10]
            if day_key not in daily:
                daily[day_key] = 0
            daily[day_key] += exp.amount

        return {
            "year": year,
            "month": month,
            "total_expenses": sum(e.amount for e in expenses),
            "expense_count": len(expenses),
            "category_breakdown": category_totals,
            "daily_breakdown": daily,
        }

    def get_profit_report(self, branch_id: int, start_date: date, end_date: date) -> dict:
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()

        sales = self.sale_repo.get_by_branch_date_range(branch_id, start_str, end_str)
        expenses = self.expense_repo.get_by_branch_date_range(branch_id, start_str, end_str)

        total_revenue = sum(s.grand_total for s in sales)
        total_expense_amount = sum(e.amount for e in expenses)

        total_cost_of_goods = 0
        with db_manager.get_session() as session:
            cost_row = (
                session.query(
                    func.coalesce(func.sum(SaleItem.quantity * Product.cost_price), 0).label("cogs")
                )
                .select_from(Sale)
                .join(SaleItem, SaleItem.sale_id == Sale.id)
                .join(Product, Product.id == SaleItem.product_id)
                .filter(
                    Sale.branch_id == branch_id,
                    func.date(Sale.created_at) >= start_str,
                    func.date(Sale.created_at) <= end_str,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .first()
            )
            total_cost_of_goods = float(cost_row.cogs)

        gross_profit = total_revenue - total_cost_of_goods
        net_profit = gross_profit - total_expense_amount
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            "start_date": start_str,
            "end_date": end_str,
            "total_revenue": total_revenue,
            "total_cost_of_goods": total_cost_of_goods,
            "gross_profit": gross_profit,
            "total_expenses": total_expense_amount,
            "net_profit": net_profit,
            "profit_margin_percent": round(profit_margin, 2),
        }

    def get_brand_profit_report(self, branch_id: int, start_date: date, end_date: date) -> list:
        rows = self.product_repo.get_brand_sales(
            branch_id, start_date.isoformat(), end_date.isoformat()
        )
        result = []
        for row in rows:
            total_revenue = float(row.total_revenue)
            total_cost = float(row.total_cost)
            gross_profit = total_revenue - total_cost
            margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            result.append({
                "brand_name": row.brand,
                "units_sold": int(row.units_sold),
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "gross_profit": gross_profit,
                "margin_percent": round(margin, 2),
            })
        return result

    def get_inventory_valuation_report(self, branch_id: int) -> dict:
        valuation = self.inventory_repo.get_valuation(branch_id)
        return {
            "cost_value": float(valuation.cost_value),
            "retail_value": float(valuation.retail_value),
            "potential_markup": float(valuation.retail_value - valuation.cost_value),
        }

    def get_low_stock_report(self, branch_id: int) -> list:
        rows = self.inventory_repo.get_low_stock(branch_id)
        result = []
        for row in rows:
            result.append({
                "product_id": row.id,
                "product_name": row.name,
                "brand": row.brand,
                "barcode": row.barcode,
                "reorder_level": float(row.reorder_level),
                "quantity_on_hand": float(row.quantity_on_hand),
                "shortage": float(row.reorder_level - row.quantity_on_hand),
            })
        return result

    def get_inventory_movement_report(self, branch_id: int, start_date: date, end_date: date) -> dict:
        rows = self.inventory_repo.get_movements(
            branch_id, start_date.isoformat(), end_date.isoformat()
        )
        movements = {}
        for row in rows:
            movements[row.movement_type] = {
                "total_quantity": abs(float(row.total_quantity)),
                "count": row.count,
            }
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "movements": movements,
        }

    def get_summary_dashboard(self, branch_id: int) -> dict:
        today = date.today()
        today_str = today.isoformat()

        daily = self.get_daily_sales_report(branch_id, today)
        low_stock = self.get_low_stock_report(branch_id)
        expenses = self.get_daily_expenses_report(branch_id, today)

        with db_manager.get_session() as session:
            pending_syncs = (
                session.query(func.count(SyncQueue.id))
                .filter_by(status="PENDING")
                .scalar() or 0
            )

        return {
            "today_sales": daily["total_sales"],
            "today_transactions": daily["sale_count"],
            "low_stock_count": len(low_stock),
            "pending_syncs": pending_syncs,
            "today_expenses": expenses["total_expenses"],
            "date": today_str,
        }
