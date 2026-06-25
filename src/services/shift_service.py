import logging
from datetime import datetime

from sqlalchemy.orm import joinedload

from src.database.connection import db_manager
from src.database.models import AuditLog, Payment, Sale, Shift, User
from src.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ShiftService:
    def open_shift(self, user, branch_id, opening_cash):
        user_id = user.id if hasattr(user, "id") else user
        if opening_cash < 0:
            raise ValidationError("Opening cash cannot be negative.")

        with db_manager.get_session() as session:
            active = (
                session.query(Shift)
                .filter(
                    Shift.branch_id == branch_id,
                    Shift.user_id == user_id,
                    Shift.status == "OPEN",
                )
                .first()
            )
            if active:
                raise ValidationError("You already have an open shift. Close it before opening a new one.")
            shift = Shift(
                user_id=user_id,
                branch_id=branch_id,
                opening_cash=opening_cash,
                opened_at=datetime.now(),
                status="OPEN",
            )
            session.add(shift)
            session.flush()

            session.add(AuditLog(
                user_id=user_id,
                branch_id=branch_id,
                action="OPEN_SHIFT",
                resource="shifts",
                resource_id=shift.id,
                details=f"Shift opened with opening cash {opening_cash}",
            ))

            return {
                "id": shift.id,
                "user_id": shift.user_id,
                "branch_id": shift.branch_id,
                "opened_at": shift.opened_at.isoformat() if shift.opened_at else None,
                "opening_cash": shift.opening_cash,
                "status": shift.status,
            }

    def close_shift(self, user, shift_id, closing_cash, notes=None):
        user_id = user.id if hasattr(user, "id") else user

        with db_manager.get_session() as session:
            shift = session.query(Shift).filter_by(id=shift_id).first()
            if not shift:
                raise NotFoundError("Shift not found.")
            if shift.status == "CLOSED":
                raise ValidationError("Shift is already closed.")
            if shift.branch_id != (user.branch_id if hasattr(user, "branch_id") else None):
                if not self._is_admin(user):
                    raise ValidationError("You can only close shifts in your own branch.")

            if closing_cash < 0:
                raise ValidationError("Closing cash cannot be negative.")

            sales_data = self._calculate_shift_sales(session, shift.id)
            expected = shift.opening_cash + sales_data["total_sales"]

            shift.closing_cash = closing_cash
            shift.expected_cash = expected
            shift.cash_sales = sales_data["cash_sales"]
            shift.mpesa_sales = sales_data["mpesa_sales"]
            shift.card_sales = sales_data["card_sales"]
            shift.other_sales = sales_data["other_sales"]
            shift.total_sales = sales_data["total_sales"]
            shift.status = "CLOSED"
            shift.closed_at = datetime.now()
            shift.notes = notes
            session.flush()

            session.add(AuditLog(
                user_id=user_id,
                branch_id=shift.branch_id,
                action="CLOSE_SHIFT",
                resource="shifts",
                resource_id=shift.id,
                details=(
                    f"Shift closed. Opening: {shift.opening_cash}, "
                    f"Sales: {shift.total_sales}, Expected: {expected}, "
                    f"Closing: {closing_cash}, "
                    f"Difference: {round(closing_cash - expected, 2)}"
                ),
            ))

            return self._shift_to_dict(shift)

    def get_active_shift(self, branch_id, user_id=None):
        with db_manager.get_session() as session:
            q = session.query(Shift).options(
                joinedload(Shift.user), joinedload(Shift.branch)
            ).filter(
                Shift.branch_id == branch_id,
                Shift.status == "OPEN",
            )
            if user_id:
                q = q.filter(Shift.user_id == user_id)
            shift = q.first()
            if not shift:
                return None
            return self._shift_to_dict(shift)

    def get_shift(self, shift_id):
        with db_manager.get_session() as session:
            shift = session.query(Shift).options(
                joinedload(Shift.user), joinedload(Shift.branch)
            ).filter_by(id=shift_id).first()
            if not shift:
                raise NotFoundError("Shift not found.")
            return self._shift_to_dict(shift)

    def get_shifts(self, branch_id=None, user_id=None, start_date=None, end_date=None, limit=100):
        with db_manager.get_session() as session:
            q = session.query(Shift).options(
                joinedload(Shift.user), joinedload(Shift.branch)
            )
            if branch_id:
                q = q.filter(Shift.branch_id == branch_id)
            if user_id:
                q = q.filter(Shift.user_id == user_id)
            if start_date:
                q = q.filter(Shift.opened_at >= start_date)
            if end_date:
                q = q.filter(Shift.opened_at <= end_date)
            shifts = q.order_by(Shift.opened_at.desc()).limit(limit).all()
            return [self._shift_to_dict(s) for s in shifts]

    def get_shift_summary(self, shift_id):
        with db_manager.get_session() as session:
            shift = session.query(Shift).options(
                joinedload(Shift.user), joinedload(Shift.branch)
            ).filter_by(id=shift_id).first()
            if not shift:
                raise NotFoundError("Shift not found.")

            sales_data = self._calculate_shift_sales(session, shift.id)
            sales = (
                session.query(Sale)
                .filter(Sale.shift_id == shift.id, Sale.status == "COMPLETED")
                .count()
            )
            voided = (
                session.query(Sale)
                .filter(Sale.shift_id == shift.id, Sale.voided == 1)
                .count()
            )

            result = self._shift_to_dict(shift)
            result["sales_count"] = sales
            result["voided_count"] = voided
            result["difference"] = round(
                (shift.closing_cash or 0) - (shift.expected_cash or 0), 2
            )
            return result

    def _calculate_shift_sales(self, session, shift_id):
        payments = (
            session.query(Payment.method, Payment.amount)
            .join(Sale, Payment.sale_id == Sale.id)
            .filter(
                Sale.shift_id == shift_id,
                Sale.status == "COMPLETED",
                Sale.voided == 0,
            )
            .all()
        )

        cash_sales = sum(p.amount for p in payments if p.method == "CASH")
        mpesa_sales = sum(p.amount for p in payments if p.method == "MPESA")
        card_sales = sum(p.amount for p in payments if p.method in ("CARD", "BANK_TRANSFER"))
        other_sales = sum(p.amount for p in payments if p.method not in ("CASH", "MPESA", "CARD", "BANK_TRANSFER"))
        total_sales = sum(p.amount for p in payments)

        return {
            "cash_sales": cash_sales,
            "mpesa_sales": mpesa_sales,
            "card_sales": card_sales,
            "other_sales": other_sales,
            "total_sales": total_sales,
        }

    def _shift_to_dict(self, shift):
        user_name = None
        if shift.user:
            user_name = shift.user.full_name or shift.user.username
        branch_name = None
        if shift.branch:
            branch_name = shift.branch.name

        return {
            "id": shift.id,
            "user_id": shift.user_id,
            "user_name": user_name,
            "branch_id": shift.branch_id,
            "branch_name": branch_name,
            "opened_at": shift.opened_at.isoformat() if shift.opened_at else None,
            "closed_at": shift.closed_at.isoformat() if shift.closed_at else None,
            "opening_cash": shift.opening_cash,
            "closing_cash": shift.closing_cash,
            "expected_cash": shift.expected_cash,
            "cash_sales": shift.cash_sales,
            "mpesa_sales": shift.mpesa_sales,
            "card_sales": shift.card_sales,
            "other_sales": shift.other_sales,
            "total_sales": shift.total_sales,
            "status": shift.status,
            "notes": shift.notes,
        }

    def _is_admin(self, user):
        if hasattr(user, "role") and user.role:
            return user.role.name == "Admin"
        return False
