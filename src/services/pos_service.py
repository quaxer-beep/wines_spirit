import logging
from datetime import date, datetime, timedelta

from sqlalchemy import Date, cast, func

from src.database.connection import db_manager
from src.database.models import Branch, Payment, Product, Sale, SaleItem, StockMovement
from src.utils.exceptions import (
    AuthorizationError,
    InsufficientStockError,
    NotFoundError,
    ValidationError,
)
from src.utils.helpers import calculate_tax, generate_receipt_number
from src.utils.validators import validate_positive_number, validate_required
from src.repositories import (
    AuditLogRepository,
    InventoryRepository,
    ProductRepository,
    SaleRepository,
)
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class PosService:
    def __init__(self):
        self.sale_repo = SaleRepository()
        self.product_repo = ProductRepository()
        self.inventory_repo = InventoryRepository()
        self.audit_repo = AuditLogRepository()
        self.auth_service = AuthService()

    # ------------------------------------------------------------------
    # Checkout / Sale Creation
    # ------------------------------------------------------------------

    def create_sale(self, user, branch_id, cart_items, payment_data):
        validate_required(cart_items, "Cart items")
        if not cart_items:
            raise ValidationError("Cannot create a sale with an empty cart.")

        with db_manager.get_session() as session:
            branch = session.query(Branch).filter_by(id=branch_id).first()
            if not branch:
                raise NotFoundError(f"Branch with ID {branch_id} not found.")

            items_data = []
            subtotal = 0.0

            for idx, item in enumerate(cart_items):
                product_id = item.get("product_id")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price")

                if not product_id:
                    raise ValidationError(f"Cart item {idx}: product_id is required.")

                product = self.product_repo.get_by_id(product_id, session=session)
                if not product:
                    raise NotFoundError(f"Cart item {idx}: product ID {product_id} not found.")
                if not product.is_active:
                    raise ValidationError(f"Product '{product.name}' is inactive and cannot be sold.")

                quantity = validate_positive_number(quantity, f"Quantity for '{product.name}'")
                unit_price = float(unit_price) if unit_price is not None else product.selling_price
                if unit_price <= 0:
                    raise ValidationError(f"Unit price for '{product.name}' must be positive.")

                line_subtotal = round(quantity * unit_price, 2)
                subtotal += line_subtotal

                inventory = self.inventory_repo.get_by_product_and_branch(product_id, branch_id, session=session)
                if not inventory or inventory.quantity_on_hand < quantity:
                    available = inventory.quantity_on_hand if inventory else 0
                    raise InsufficientStockError(
                        f"Insufficient stock for '{product.name}': "
                        f"requested {quantity}, available {available}."
                    )

                items_data.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "subtotal": line_subtotal,
                    }
                )

            subtotal = round(subtotal, 2)
            discount = round(float(payment_data.get("discount", 0)), 2)
            if discount < 0:
                raise ValidationError("Discount cannot be negative.")
            if discount > subtotal:
                raise ValidationError("Discount cannot exceed subtotal.")

            tax = round(calculate_tax(subtotal), 2)
            grand_total = round(subtotal + tax - discount, 2)

            receipt_number = generate_receipt_number(branch.code, session=session)

            sale = self.sale_repo.create(
                session,
                receipt_number=receipt_number,
                branch_id=branch_id,
                user_id=user.id if hasattr(user, "id") else user,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                grand_total=grand_total,
                payment_method=payment_data.get("method", "CASH"),
                status="COMPLETED",
                voided=0,
                void_reason=None,
            )

            created_items = []
            for item_data in items_data:
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    subtotal=item_data["subtotal"],
                )
                session.add(sale_item)
                created_items.append(
                    {
                        "id": sale_item.id,
                        "product_id": item_data["product_id"],
                        "product_name": item_data["product_name"],
                        "quantity": item_data["quantity"],
                        "unit_price": item_data["unit_price"],
                        "subtotal": item_data["subtotal"],
                    }
                )

                inventory = self.inventory_repo.get_by_product_and_branch(
                    item_data["product_id"], branch_id, session=session
                )
                if inventory:
                    inventory.quantity_on_hand -= item_data["quantity"]

            session.flush()

            created_payments = self._process_payments(
                session, sale.id, payment_data, branch_id, user
            )

            self.audit_repo.create(
                session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=branch_id,
                action="SALE_CREATED",
                resource="sales",
                resource_id=sale.id,
                details=f"Sale #{receipt_number}: KES {grand_total} ({payment_data.get('method', 'CASH')})",
            )

            return {
                "id": sale.id,
                "receipt_number": receipt_number,
                "branch_id": branch_id,
                "branch_name": branch.name,
                "user_id": sale.user_id,
                "subtotal": subtotal,
                "discount": discount,
                "tax": tax,
                "grand_total": grand_total,
                "payment_method": payment_data.get("method", "CASH"),
                "status": "COMPLETED",
                "items": created_items,
                "payments": created_payments,
                "created_at": sale.created_at.isoformat() if sale.created_at else None,
            }

    def _process_payments(self, session, sale_id, payment_data, branch_id, user):
        method = payment_data.get("method", "CASH")
        created_payments = []

        if method == "MIXED":
            sub_payments = payment_data.get("payments", [])
            if not sub_payments:
                raise ValidationError("MIXED payment requires at least one sub-payment.")

            for sub in sub_payments:
                sub_method = sub.get("method", "CASH")
                sub_amount = float(sub.get("amount", 0))
                if sub_amount <= 0:
                    raise ValidationError(f"{sub_method} payment amount must be positive.")

                payment = Payment(
                    sale_id=sale_id,
                    method=sub_method,
                    amount=sub_amount,
                    reference=sub.get("reference"),
                    mpesa_code=sub.get("mpesa_code") if sub_method == "MPESA" else None,
                    status="COMPLETED",
                )
                session.add(payment)
                created_payments.append(
                    {
                        "id": payment.id,
                        "method": sub_method,
                        "amount": sub_amount,
                        "reference": sub.get("reference"),
                        "mpesa_code": sub.get("mpesa_code"),
                        "status": "COMPLETED",
                    }
                )
        else:
            amount = float(payment_data.get("amount", 0))
            if amount <= 0:
                raise ValidationError(f"{method} payment amount must be positive.")

            mpesa_code = payment_data.get("mpesa_code") if method == "MPESA" else None

            payment = Payment(
                sale_id=sale_id,
                method=method,
                amount=amount,
                reference=payment_data.get("reference"),
                mpesa_code=mpesa_code,
                status="COMPLETED",
            )
            session.add(payment)
            created_payments.append(
                {
                    "id": payment.id,
                    "method": method,
                    "amount": amount,
                    "reference": payment_data.get("reference"),
                    "mpesa_code": mpesa_code,
                    "status": "COMPLETED",
                }
            )

        return created_payments

    # ------------------------------------------------------------------
    # Sale Queries
    # ------------------------------------------------------------------

    def get_sale(self, sale_id):
        with db_manager.get_session() as session:
            sale = self.sale_repo.get_by_id(sale_id, session=session)
            if not sale:
                raise NotFoundError(f"Sale with ID {sale_id} not found.")
            return self._sale_to_dict(sale)

    def get_daily_sales(self, branch_id):
        today = date.today()
        with db_manager.get_session() as session:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    cast(Sale.created_at, Date) == today,
                    Sale.voided == 0,
                )
                .order_by(Sale.created_at.desc())
                .all()
            )
            return [self._sale_to_dict(s) for s in sales]

    def get_branch_sales(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.branch_id == branch_id,
                    cast(Sale.created_at, Date) >= start_date,
                    cast(Sale.created_at, Date) <= end_date,
                    Sale.voided == 0,
                )
                .order_by(Sale.created_at.desc())
                .all()
            )
            return [self._sale_to_dict(s) for s in sales]

    def get_cashier_sales(self, user_id, start_date, end_date):
        with db_manager.get_session() as session:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.user_id == user_id,
                    cast(Sale.created_at, Date) >= start_date,
                    cast(Sale.created_at, Date) <= end_date,
                    Sale.voided == 0,
                )
                .order_by(Sale.created_at.desc())
                .all()
            )
            return [self._sale_to_dict(s) for s in sales]

    # ------------------------------------------------------------------
    # Void Sale
    # ------------------------------------------------------------------

    def void_sale(self, user, sale_id, reason):
        validate_required(reason, "Void reason")

        with db_manager.get_session() as session:
            sale = self.sale_repo.get_by_id(sale_id, session=session)
            if not sale:
                raise NotFoundError(f"Sale with ID {sale_id} not found.")

            if sale.voided:
                raise ValidationError(f"Sale #{sale.receipt_number} is already voided.")

            sale_date = sale.created_at.date() if hasattr(sale.created_at, "date") else sale.created_at
            if isinstance(sale_date, str):
                sale_date = datetime.fromisoformat(sale_date).date()

            if sale_date != date.today():
                raise ValidationError("Only today's sales can be voided.")

            sale.voided = 1
            sale.void_reason = reason
            sale.status = "CANCELLED"

            for item in sale.items:
                inventory = self.inventory_repo.get_by_product_and_branch(
                    item.product_id, sale.branch_id, session=session
                )
                if inventory:
                    inventory.quantity_on_hand += item.quantity

                movement = StockMovement(
                    product_id=item.product_id,
                    branch_id=sale.branch_id,
                    movement_type="IN",
                    quantity=item.quantity,
                    reference_type="VOID",
                    reference_id=sale.id,
                    notes=f"Restored from voided sale #{sale.receipt_number}: {item.quantity} x {item.product.name if item.product else 'Unknown'}",
                    created_by=user.id if hasattr(user, "id") else user,
                )
                session.add(movement)

            self.audit_repo.create(
                session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=sale.branch_id,
                action="SALE_VOIDED",
                resource="sales",
                resource_id=sale.id,
                details=f"Sale #{sale.receipt_number} voided. Reason: {reason}",
            )

            return {
                "id": sale.id,
                "receipt_number": sale.receipt_number,
                "voided": 1,
                "status": "CANCELLED",
                "void_reason": reason,
            }

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def get_brand_profit_report(self, branch_id, start_date, end_date):
        with db_manager.get_session() as session:
            results = (
                session.query(
                    Product.brand,
                    func.sum(SaleItem.quantity).label("total_qty"),
                    func.sum(Product.cost_price * SaleItem.quantity).label("total_cost"),
                    func.sum(SaleItem.subtotal).label("total_revenue"),
                )
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .filter(
                    Sale.branch_id == branch_id,
                    cast(Sale.created_at, Date) >= start_date,
                    cast(Sale.created_at, Date) <= end_date,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                    Product.brand.isnot(None),
                    Product.brand != "",
                )
                .group_by(Product.brand)
                .order_by(Product.brand)
                .all()
            )

            report = []
            for r in results:
                total_qty = float(r.total_qty)
                total_cost = float(r.total_cost or 0)
                total_revenue = float(r.total_revenue or 0)
                gross_profit = round(total_revenue - total_cost, 2)
                margin_pct = round((gross_profit / total_revenue * 100), 2) if total_revenue else 0.0

                report.append(
                    {
                        "brand": r.brand,
                        "total_qty": total_qty,
                        "total_cost": round(total_cost, 2),
                        "total_revenue": total_revenue,
                        "gross_profit": gross_profit,
                        "margin_pct": margin_pct,
                    }
                )

            return report

    # ------------------------------------------------------------------
    # POS Helpers
    # ------------------------------------------------------------------

    def search_products_for_pos(self, query, branch_id, limit=20):
        with db_manager.get_session() as session:
            products = self.product_repo.search(query, limit=limit, session=session)
            results = []
            for p in products:
                if not p.is_active:
                    continue
                inventory = self.inventory_repo.get_by_product_and_branch(p.id, branch_id, session=session)
                qty = inventory.quantity_on_hand if inventory else 0
                results.append(
                    {
                        "id": p.id,
                        "barcode": p.barcode,
                        "name": p.name,
                        "brand": p.brand,
                        "category_id": p.category_id,
                        "category_name": p.category.name if p.category else None,
                        "selling_price": p.selling_price,
                        "cost_price": p.cost_price,
                        "unit": p.unit,
                        "quantity_on_hand": qty,
                        "is_active": p.is_active,
                    }
                )
            return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sale_to_dict(sale):
        user_name = sale.user.full_name if sale.user else None
        branch_name = sale.branch.name if sale.branch else None

        items = []
        if sale.items:
            for item in sale.items:
                items.append(
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_name": item.product.name if item.product else None,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "subtotal": item.subtotal,
                    }
                )

        payments = []
        if sale.payments:
            for pmt in sale.payments:
                payments.append(
                    {
                        "id": pmt.id,
                        "method": pmt.method,
                        "amount": pmt.amount,
                        "reference": pmt.reference,
                        "mpesa_code": pmt.mpesa_code,
                        "status": pmt.status,
                    }
                )

        return {
            "id": sale.id,
            "receipt_number": sale.receipt_number,
            "branch_id": sale.branch_id,
            "branch_name": branch_name,
            "user_id": sale.user_id,
            "cashier_name": user_name,
            "subtotal": sale.subtotal,
            "discount": sale.discount,
            "tax": sale.tax,
            "grand_total": sale.grand_total,
            "payment_method": sale.payment_method,
            "status": sale.status,
            "voided": sale.voided,
            "void_reason": sale.void_reason,
            "items": items,
            "payments": payments,
            "created_at": sale.created_at.isoformat() if sale.created_at else None,
        }
