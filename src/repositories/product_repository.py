from sqlalchemy import func, or_, select, desc

from src.database.connection import db_manager
from src.database.models import (
    Category,
    Inventory,
    Product,
    Sale,
    SaleItem,
)
from src.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self):
        super().__init__(Product)

    def get_by_barcode(self, barcode, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Product).where(Product.barcode == barcode)
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = select(Product).where(Product.barcode == barcode)
            return session.execute(stmt).scalar_one_or_none()

    def search_by_name(self, query, limit=20, session=None):
        if session is None:
            with db_manager.get_session() as session:
                pattern = f"%{query}%"
                stmt = (
                    select(Product)
                    .where(Product.name.like(pattern))
                    .where(Product.is_active == 1)
                    .order_by(Product.name)
                    .limit(limit)
                )
                return session.execute(stmt).scalars().all()
        else:
            pattern = f"%{query}%"
            stmt = (
                select(Product)
                .where(Product.name.like(pattern))
                .where(Product.is_active == 1)
                .order_by(Product.name)
                .limit(limit)
            )
            return session.execute(stmt).scalars().all()

    def get_by_category(self, category_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product)
                    .where(Product.category_id == category_id)
                    .order_by(Product.name)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(Product)
                .where(Product.category_id == category_id)
                .order_by(Product.name)
            )
            return session.execute(stmt).scalars().all()

    def get_active_products(self, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product)
                    .where(Product.is_active == 1)
                    .order_by(Product.name)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(Product)
                .where(Product.is_active == 1)
                .order_by(Product.name)
            )
            return session.execute(stmt).scalars().all()

    def get_low_stock_products(self, branch_id, threshold=None, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product, Inventory.quantity_on_hand)
                    .join(Inventory, Inventory.product_id == Product.id)
                    .where(Inventory.branch_id == branch_id)
                    .where(Product.is_active == 1)
                )
                if threshold is not None:
                    stmt = stmt.where(
                        Inventory.quantity_on_hand <= threshold
                    )
                else:
                    stmt = stmt.where(
                        Inventory.quantity_on_hand <= Product.reorder_level
                    )
                stmt = stmt.order_by(Inventory.quantity_on_hand)
                return session.execute(stmt).all()
        else:
            stmt = (
                select(Product, Inventory.quantity_on_hand)
                .join(Inventory, Inventory.product_id == Product.id)
                .where(Inventory.branch_id == branch_id)
                .where(Product.is_active == 1)
            )
            if threshold is not None:
                stmt = stmt.where(
                    Inventory.quantity_on_hand <= threshold
                )
            else:
                stmt = stmt.where(
                    Inventory.quantity_on_hand <= Product.reorder_level
                )
            stmt = stmt.order_by(Inventory.quantity_on_hand)
            return session.execute(stmt).all()

    def get_out_of_stock_products(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product, Inventory.quantity_on_hand)
                    .join(Inventory, Inventory.product_id == Product.id)
                    .where(Inventory.branch_id == branch_id)
                    .where(Inventory.quantity_on_hand == 0)
                    .where(Product.is_active == 1)
                    .order_by(Product.name)
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(Product, Inventory.quantity_on_hand)
                .join(Inventory, Inventory.product_id == Product.id)
                .where(Inventory.branch_id == branch_id)
                .where(Inventory.quantity_on_hand == 0)
                .where(Product.is_active == 1)
                .order_by(Product.name)
            )
            return session.execute(stmt).all()

    def search_products(self, query, branch_id, limit=20, session=None):
        if session is None:
            with db_manager.get_session() as session:
                pattern = f"%{query}%"
                stmt = (
                    select(Product, Inventory.quantity_on_hand)
                    .join(Inventory, Inventory.product_id == Product.id)
                    .where(Inventory.branch_id == branch_id)
                    .where(
                        or_(
                            Product.name.like(pattern),
                            Product.barcode.like(pattern),
                        )
                    )
                    .where(Product.is_active == 1)
                    .order_by(Product.name)
                    .limit(limit)
                )
                return session.execute(stmt).all()
        else:
            pattern = f"%{query}%"
            stmt = (
                select(Product, Inventory.quantity_on_hand)
                .join(Inventory, Inventory.product_id == Product.id)
                .where(Inventory.branch_id == branch_id)
                .where(
                    or_(
                        Product.name.like(pattern),
                        Product.barcode.like(pattern),
                    )
                )
                .where(Product.is_active == 1)
                .order_by(Product.name)
                .limit(limit)
            )
            return session.execute(stmt).all()

    def search(self, query, limit=20, session=None):
        if session is None:
            with db_manager.get_session() as session:
                pattern = f"%{query}%"
                stmt = (
                    select(Product)
                    .where(
                        or_(Product.name.like(pattern), Product.barcode.like(pattern))
                    )
                    .where(Product.is_active == 1)
                    .order_by(Product.name)
                    .limit(limit)
                )
                return session.execute(stmt).scalars().all()
        else:
            pattern = f"%{query}%"
            stmt = (
                select(Product)
                .where(
                    or_(Product.name.like(pattern), Product.barcode.like(pattern))
                )
                .where(Product.is_active == 1)
                .order_by(Product.name)
                .limit(limit)
            )
            return session.execute(stmt).scalars().all()

    def get_fast_moving(self, branch_id, limit=10, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product, func.count(SaleItem.id).label("sale_count"))
                    .join(SaleItem, SaleItem.product_id == Product.id)
                    .join(Sale, Sale.id == SaleItem.sale_id)
                    .where(Sale.branch_id == branch_id)
                    .where(Sale.voided == 0)
                    .group_by(Product.id)
                    .order_by(desc(func.count(SaleItem.id)))
                    .limit(limit)
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(Product, func.count(SaleItem.id).label("sale_count"))
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .where(Sale.branch_id == branch_id)
                .where(Sale.voided == 0)
                .group_by(Product.id)
                .order_by(desc(func.count(SaleItem.id)))
                .limit(limit)
            )
            return session.execute(stmt).all()

    def get_slow_moving(self, branch_id, limit=10, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Product, func.count(SaleItem.id).label("sale_count"))
                    .join(SaleItem, SaleItem.product_id == Product.id)
                    .join(Sale, Sale.id == SaleItem.sale_id)
                    .where(Sale.branch_id == branch_id)
                    .where(Sale.voided == 0)
                    .group_by(Product.id)
                    .order_by(func.count(SaleItem.id))
                    .limit(limit)
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(Product, func.count(SaleItem.id).label("sale_count"))
                .join(SaleItem, SaleItem.product_id == Product.id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .where(Sale.branch_id == branch_id)
                .where(Sale.voided == 0)
                .group_by(Product.id)
                .order_by(func.count(SaleItem.id))
                .limit(limit)
            )
            return session.execute(stmt).all()

    def get_inventory_valuation(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(
                    func.sum(
                        Product.cost_price * Inventory.quantity_on_hand
                    )
                ).select_from(Product).join(
                    Inventory, Inventory.product_id == Product.id
                ).where(
                    Inventory.branch_id == branch_id
                )
                return session.execute(stmt).scalar() or 0
        else:
            stmt = select(
                func.sum(
                    Product.cost_price * Inventory.quantity_on_hand
                )
            ).select_from(Product).join(
                Inventory, Inventory.product_id == Product.id
            ).where(
                Inventory.branch_id == branch_id
            )
            return session.execute(stmt).scalar() or 0
