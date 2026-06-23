from datetime import datetime

from sqlalchemy import func, select

from src.database.connection import db_manager
from src.database.models import Expense
from src.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository):
    def __init__(self):
        super().__init__(Expense)

    def get_by_branch(self, branch_id, start_date=None, end_date=None, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Expense).where(Expense.branch_id == branch_id)
                if start_date:
                    stmt = stmt.where(Expense.expense_date >= start_date)
                if end_date:
                    stmt = stmt.where(Expense.expense_date <= end_date)
                stmt = stmt.order_by(Expense.expense_date.desc())
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(Expense).where(Expense.branch_id == branch_id)
            if start_date:
                stmt = stmt.where(Expense.expense_date >= start_date)
            if end_date:
                stmt = stmt.where(Expense.expense_date <= end_date)
            stmt = stmt.order_by(Expense.expense_date.desc())
            return session.execute(stmt).scalars().all()

    def get_by_category(
        self, category, branch_id, start_date=None, end_date=None, session=None
    ):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Expense)
                    .where(Expense.branch_id == branch_id)
                    .where(Expense.category == category)
                )
                if start_date:
                    stmt = stmt.where(Expense.expense_date >= start_date)
                if end_date:
                    stmt = stmt.where(Expense.expense_date <= end_date)
                stmt = stmt.order_by(Expense.expense_date.desc())
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(Expense)
                .where(Expense.branch_id == branch_id)
                .where(Expense.category == category)
            )
            if start_date:
                stmt = stmt.where(Expense.expense_date >= start_date)
            if end_date:
                stmt = stmt.where(Expense.expense_date <= end_date)
            stmt = stmt.order_by(Expense.expense_date.desc())
            return session.execute(stmt).scalars().all()

    def get_daily_expenses(self, branch_id, date=None, session=None):
        if date is None:
            date = datetime.now().date()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        return self.get_by_branch(branch_id, start, end, session=session)

    def get_monthly_expenses(self, branch_id, year, month, session=None):
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        return self.get_by_branch(branch_id, start, end, session=session)

    def get_expense_summary(self, branch_id, start_date, end_date, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(
                    func.count(Expense.id).label("total_count"),
                    func.sum(Expense.amount).label("total_amount"),
                    func.avg(Expense.amount).label("average_amount"),
                ).where(
                    Expense.branch_id == branch_id,
                    Expense.expense_date.between(start_date, end_date),
                )
                return session.execute(stmt).one()
        else:
            stmt = select(
                func.count(Expense.id).label("total_count"),
                func.sum(Expense.amount).label("total_amount"),
                func.avg(Expense.amount).label("average_amount"),
            ).where(
                Expense.branch_id == branch_id,
                Expense.expense_date.between(start_date, end_date),
            )
            return session.execute(stmt).one()

    def get_category_breakdown(self, branch_id, start_date, end_date, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(
                        Expense.category,
                        func.count(Expense.id).label("count"),
                        func.sum(Expense.amount).label("total_amount"),
                    )
                    .where(
                        Expense.branch_id == branch_id,
                        Expense.expense_date.between(start_date, end_date),
                    )
                    .group_by(Expense.category)
                    .order_by(func.sum(Expense.amount).desc())
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(
                    Expense.category,
                    func.count(Expense.id).label("count"),
                    func.sum(Expense.amount).label("total_amount"),
                )
                .where(
                    Expense.branch_id == branch_id,
                    Expense.expense_date.between(start_date, end_date),
                )
                .group_by(Expense.category)
                .order_by(func.sum(Expense.amount).desc())
            )
            return session.execute(stmt).all()
