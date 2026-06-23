import logging
from datetime import date, datetime
from decimal import Decimal

from src.database.connection import db_manager
from src.database.models import Product, StockMovement
from src.utils.exceptions import InsufficientStockError, NotFoundError, ValidationError
from src.utils.validators import validate_non_negative, validate_positive_number, validate_required
from src.repositories import (
    AuditLogRepository,
    InventoryRepository,
    ProductRepository,
)
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.inventory_repo = InventoryRepository()
        self.audit_repo = AuditLogRepository()
        self.auth_service = AuthService()

    # ------------------------------------------------------------------
    # Product CRUD
    # ------------------------------------------------------------------

    def add_product(self, user, **product_data):
        validate_required(product_data.get("name"), "Product name")
        selling_price = product_data.get("selling_price", 0)
        if selling_price is not None:
            validate_non_negative(selling_price, "Selling price")

        with db_manager.get_session() as session:
            product = self.product_repo.create(
                session=session,
                barcode=product_data.get("barcode"),
                name=product_data["name"],
                brand=product_data.get("brand"),
                category_id=product_data.get("category_id"),
                cost_price=float(product_data.get("cost_price", 0)),
                selling_price=float(selling_price),
                unit=product_data.get("unit", "pcs"),
                reorder_level=float(product_data.get("reorder_level", 0)),
                is_active=1,
            )

            self.audit_repo.create(
                session=session,
                user_id=user.id if hasattr(user, "id") else user,
                action="CREATE",
                resource="products",
                resource_id=product.id,
                details=f"Created product '{product.name}' (barcode={product.barcode})",
            )

            return {
                "id": product.id,
                "barcode": product.barcode,
                "name": product.name,
                "brand": product.brand,
                "category_id": product.category_id,
                "cost_price": product.cost_price,
                "selling_price": product.selling_price,
                "unit": product.unit,
                "reorder_level": product.reorder_level,
                "is_active": product.is_active,
            }

    def update_product(self, user, product_id, **data):
        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")

            old_price = product.selling_price

            update_fields = {}
            for field in ("name", "barcode", "brand", "category_id", "unit", "is_active"):
                if field in data:
                    update_fields[field] = data[field]
            if "cost_price" in data:
                update_fields["cost_price"] = float(data["cost_price"])
            if "selling_price" in data:
                update_fields["selling_price"] = float(data["selling_price"])
            if "reorder_level" in data:
                update_fields["reorder_level"] = float(data["reorder_level"])

            if "name" in update_fields:
                validate_required(update_fields["name"], "Product name")

            self.product_repo.update(session=session, entity_id=product_id, **update_fields)
            session.flush()

            price_changed = (
                "selling_price" in update_fields
                and abs(float(update_fields["selling_price"]) - old_price) > 0.001
            )

            if price_changed:
                self.audit_repo.create(
                    session=session,
                    user_id=user.id if hasattr(user, "id") else user,
                    action="PRICE_CHANGE",
                    resource="products",
                    resource_id=product_id,
                    details=f"Price changed for product '{product.name}': {old_price} -> {update_fields['selling_price']}",
                )
            else:
                self.audit_repo.create(
                    session=session,
                    user_id=user.id if hasattr(user, "id") else user,
                    action="UPDATE",
                    resource="products",
                    resource_id=product_id,
                    details=f"Updated product '{product.name}' fields: {', '.join(update_fields.keys())}",
                )

            updated = self.product_repo.get_by_id(product_id, session=session)
            return {
                "id": updated.id,
                "barcode": updated.barcode,
                "name": updated.name,
                "brand": updated.brand,
                "category_id": updated.category_id,
                "cost_price": updated.cost_price,
                "selling_price": updated.selling_price,
                "unit": updated.unit,
                "reorder_level": updated.reorder_level,
                "is_active": updated.is_active,
            }

    def get_product(self, product_id):
        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")
            return self._product_to_dict(product)

    def search_products(self, query, branch_id=None):
        with db_manager.get_session() as session:
            products = self.product_repo.search_by_name(query, session=session)
            results = []
            for p in products:
                data = self._product_to_dict(p)
                if branch_id:
                    inv = self.inventory_repo.get_by_product_and_branch(p.id, branch_id, session=session)
                    data["quantity_on_hand"] = inv.quantity_on_hand if inv else 0
                results.append(data)
            return results

    def get_product_by_barcode(self, barcode):
        with db_manager.get_session() as session:
            product = self.product_repo.get_by_barcode(barcode, session=session)
            if not product:
                raise NotFoundError(f"Product with barcode '{barcode}' not found.")
            return self._product_to_dict(product)

    # ------------------------------------------------------------------
    # Stock Operations
    # ------------------------------------------------------------------

    def stock_in(self, user, branch_id, product_id, quantity, unit_cost=None, notes=""):
        quantity = validate_positive_number(quantity, "Quantity")

        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")

            inventory = self.inventory_repo.get_by_product_and_branch(product_id, branch_id, session=session)
            if inventory:
                inventory.quantity_on_hand += quantity
            else:
                self.inventory_repo.create(
                    session=session,
                    product_id=product_id,
                    branch_id=branch_id,
                    quantity_on_hand=quantity,
                )

            movement = StockMovement(
                product_id=product_id,
                branch_id=branch_id,
                movement_type="IN",
                quantity=quantity,
                reference_type="STOCK_IN",
                notes=notes or f"Stock in: {quantity} units",
                created_by=user.id if hasattr(user, "id") else user,
            )
            session.add(movement)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=branch_id,
                action="STOCK_IN",
                resource="inventory",
                resource_id=product_id,
                details=f"Stocked in {quantity} units of '{product.name}' at branch_id={branch_id}. Notes: {notes}",
            )

            return {
                "movement_id": movement.id,
                "product_id": product_id,
                "product_name": product.name,
                "branch_id": branch_id,
                "quantity": quantity,
                "movement_type": "IN",
            }

    def stock_out(self, user, branch_id, product_id, quantity, reason, notes=""):
        quantity = validate_positive_number(quantity, "Quantity")
        validate_required(reason, "Reason")

        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")

            inventory = self.inventory_repo.get_by_product_and_branch(product_id, branch_id, session=session)
            if not inventory or inventory.quantity_on_hand < quantity:
                current_qty = inventory.quantity_on_hand if inventory else 0
                raise InsufficientStockError(
                    f"Insufficient stock for '{product.name}': "
                    f"requested {quantity}, available {current_qty}."
                )

            inventory.quantity_on_hand -= quantity

            movement = StockMovement(
                product_id=product_id,
                branch_id=branch_id,
                movement_type="OUT",
                quantity=quantity,
                reference_type="STOCK_OUT",
                notes=notes or f"Stock out: {quantity} units. Reason: {reason}",
                created_by=user.id if hasattr(user, "id") else user,
            )
            session.add(movement)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=branch_id,
                action="STOCK_OUT",
                resource="inventory",
                resource_id=product_id,
                details=f"Stocked out {quantity} units of '{product.name}'. Reason: {reason}",
            )

            return {
                "movement_id": movement.id,
                "product_id": product_id,
                "product_name": product.name,
                "branch_id": branch_id,
                "quantity": quantity,
                "reason": reason,
                "movement_type": "OUT",
            }

    def adjust_stock(self, user, branch_id, product_id, new_quantity, reason):
        validate_required(reason, "Reason")

        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")

            inventory = self.inventory_repo.get_by_product_and_branch(product_id, branch_id, session=session)
            old_qty = inventory.quantity_on_hand if inventory else 0
            difference = round(new_quantity - old_qty, 4)

            if inventory:
                inventory.quantity_on_hand = new_quantity
            else:
                self.inventory_repo.create(
                    session=session,
                    product_id=product_id,
                    branch_id=branch_id,
                    quantity_on_hand=new_quantity,
                )

            movement = StockMovement(
                product_id=product_id,
                branch_id=branch_id,
                movement_type="ADJUSTMENT",
                quantity=new_quantity,
                reference_type="STOCK_ADJUST",
                notes=f"Adjustment: {old_qty} -> {new_quantity} ({difference:+.2f}). Reason: {reason}",
                created_by=user.id if hasattr(user, "id") else user,
            )
            session.add(movement)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=branch_id,
                action="STOCK_ADJUST",
                resource="inventory",
                resource_id=product_id,
                details=f"Stock adjusted for '{product.name}': {old_qty} -> {new_quantity}. Reason: {reason}",
            )

            return {
                "movement_id": movement.id,
                "product_id": product_id,
                "product_name": product.name,
                "branch_id": branch_id,
                "old_quantity": old_qty,
                "new_quantity": new_quantity,
                "difference": difference,
                "reason": reason,
                "movement_type": "ADJUSTMENT",
            }

    def transfer_stock(self, user, from_branch, to_branch, product_id, quantity):
        quantity = validate_positive_number(quantity, "Quantity")

        with db_manager.get_session() as session:
            product = self.product_repo.get_by_id(product_id, session=session)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")

            source_inv = self.inventory_repo.get_by_product_and_branch(product_id, from_branch, session=session)
            if not source_inv or source_inv.quantity_on_hand < quantity:
                current_qty = source_inv.quantity_on_hand if source_inv else 0
                raise InsufficientStockError(
                    f"Insufficient stock for transfer: requested {quantity}, available {current_qty}."
                )

            source_inv.quantity_on_hand -= quantity

            dest_inv = self.inventory_repo.get_by_product_and_branch(product_id, to_branch, session=session)
            if dest_inv:
                dest_inv.quantity_on_hand += quantity
            else:
                self.inventory_repo.create(
                    session=session,
                    product_id=product_id,
                    branch_id=to_branch,
                    quantity_on_hand=quantity,
                )

            movement = StockMovement(
                product_id=product_id,
                branch_id=from_branch,
                movement_type="TRANSFER",
                quantity=-quantity,
                reference_type="TRANSFER",
                notes=f"Transfer {quantity} units from branch {from_branch} to {to_branch}",
                created_by=user.id if hasattr(user, "id") else user,
            )
            session.add(movement)
            session.flush()

            self.audit_repo.create(
                session=session,
                user_id=user.id if hasattr(user, "id") else user,
                branch_id=from_branch,
                action="TRANSFER_OUT",
                resource="inventory",
                resource_id=product_id,
                details=f"Transferred {quantity} units of '{product.name}' from branch {from_branch} to {to_branch}",
            )

            return {
                "movement_id": movement.id,
                "product_id": product_id,
                "product_name": product.name,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "quantity": quantity,
                "movement_type": "TRANSFER",
            }

    # ------------------------------------------------------------------
    # Inventory Queries
    # ------------------------------------------------------------------

    def get_branch_inventory(self, branch_id):
        with db_manager.get_session() as session:
            records = self.inventory_repo.get_branch_inventory(branch_id, session=session)
            results = []
            for inv in records:
                product = inv.product
                results.append(
                    {
                        "inventory_id": inv.id,
                        "product_id": product.id,
                        "barcode": product.barcode,
                        "product_name": product.name,
                        "brand": product.brand,
                        "category_id": product.category_id,
                        "cost_price": product.cost_price,
                        "selling_price": product.selling_price,
                        "unit": product.unit,
                        "reorder_level": product.reorder_level,
                        "quantity_on_hand": inv.quantity_on_hand,
                        "last_count_date": inv.last_count_date.isoformat() if inv.last_count_date else None,
                    }
                )
            return results

    def get_low_stock_alerts(self, branch_id):
        with db_manager.get_session() as session:
            records = self.inventory_repo.get_branch_inventory(branch_id, session=session)
            alerts = []
            for inv in records:
                product = inv.product
                if product.reorder_level > 0 and inv.quantity_on_hand <= product.reorder_level:
                    alerts.append(
                        {
                            "product_id": product.id,
                            "product_name": product.name,
                            "barcode": product.barcode,
                            "quantity_on_hand": inv.quantity_on_hand,
                            "reorder_level": product.reorder_level,
                            "shortage": product.reorder_level - inv.quantity_on_hand,
                            "unit": product.unit,
                        }
                    )
            return alerts

    def get_inventory_valuation(self, branch_id):
        with db_manager.get_session() as session:
            records = self.inventory_repo.get_branch_inventory(branch_id, session=session)
            total_value = 0.0
            items = []
            for inv in records:
                product = inv.product
                value = round(inv.quantity_on_hand * product.cost_price, 2)
                total_value += value
                items.append(
                    {
                        "product_id": product.id,
                        "product_name": product.name,
                        "brand": product.brand,
                        "quantity_on_hand": inv.quantity_on_hand,
                        "cost_price": product.cost_price,
                        "valuation": value,
                    }
                )
            return {"items": items, "total_valuation": round(total_value, 2)}

    def get_stock_movements(self, branch_id, start_date=None, end_date=None):
        with db_manager.get_session() as session:
            movements = self.inventory_repo.get_stock_movements(
                branch_id, start_date, end_date, session=session
            )
            results = []
            for m in movements:
                product_name = m.product.name if m.product else "Unknown"
                created_by_name = m.created_by_user.full_name if m.created_by_user else None
                results.append(
                    {
                        "id": m.id,
                        "product_id": m.product_id,
                        "product_name": product_name,
                        "branch_id": m.branch_id,
                        "movement_type": m.movement_type,
                        "quantity": m.quantity,
                        "reference_type": m.reference_type,
                        "reference_id": m.reference_id,
                        "notes": m.notes,
                        "created_by": m.created_by,
                        "created_by_name": created_by_name,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                )
            return results

    def get_fast_moving(self, branch_id, limit=10):
        with db_manager.get_session() as session:
            from sqlalchemy import desc, func
            from src.database.models import Sale, SaleItem

            results = (
                session.query(
                    Product.id,
                    Product.name,
                    Product.brand,
                    func.sum(SaleItem.quantity).label("total_qty"),
                    func.sum(SaleItem.subtotal).label("total_revenue"),
                )
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .filter(
                    Sale.branch_id == branch_id,
                    Sale.status == "COMPLETED",
                    Sale.voided == 0,
                )
                .group_by(Product.id)
                .order_by(desc("total_qty"))
                .limit(limit)
                .all()
            )

            return [
                {
                    "product_id": r.id,
                    "product_name": r.name,
                    "brand": r.brand,
                    "total_qty": float(r.total_qty),
                    "total_revenue": float(r.total_revenue),
                }
                for r in results
            ]

    def get_slow_moving(self, branch_id, limit=10):
        with db_manager.get_session() as session:
            from sqlalchemy import asc, func
            from src.database.models import Sale, SaleItem

            results = (
                session.query(
                    Product.id,
                    Product.name,
                    Product.brand,
                    func.coalesce(func.sum(SaleItem.quantity), 0).label("total_qty"),
                    func.coalesce(func.sum(SaleItem.subtotal), 0).label("total_revenue"),
                )
                .outerjoin(SaleItem, SaleItem.product_id == Product.id)
                .outerjoin(
                    Sale,
                    (Sale.id == SaleItem.sale_id)
                    & (Sale.branch_id == branch_id)
                    & (Sale.status == "COMPLETED")
                    & (Sale.voided == 0),
                )
                .group_by(Product.id)
                .order_by(asc("total_qty"), Product.name)
                .limit(limit)
                .all()
            )

            return [
                {
                    "product_id": r.id,
                    "product_name": r.name,
                    "brand": r.brand,
                    "total_qty": float(r.total_qty),
                    "total_revenue": float(r.total_revenue),
                }
                for r in results
            ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _product_to_dict(product):
        return {
            "id": product.id,
            "barcode": product.barcode,
            "name": product.name,
            "brand": product.brand,
            "category_id": product.category_id,
            "category_name": product.category.name if product.category else None,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "unit": product.unit,
            "reorder_level": product.reorder_level,
            "is_active": product.is_active,
            "created_at": product.created_at.isoformat() if hasattr(product, "created_at") and product.created_at else None,
            "updated_at": product.updated_at.isoformat() if hasattr(product, "updated_at") and product.updated_at else None,
        }
