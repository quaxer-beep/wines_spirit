from datetime import datetime

from sqlalchemy import func, or_, select, desc
from sqlalchemy.orm import joinedload, selectinload

from src.database.connection import db_manager
from src.database.models import Payment, Product, Sale, SaleItem, User
from src.repositories.base import BaseRepository


class SaleRepository(BaseRepository):
    def __init__(self):
        super().__init__(Sale)

    def _generate_receipt(self, branch_id):
        now = datetime.now()
        return f"RCP-{branch_id:03d}-{now.strftime('%Y%m%d%H%M%S')}"

    def get_by_branch(self, branch_id, start_date=None, end_date=None, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Sale).where(Sale.branch_id == branch_id)
                if start_date:
                    stmt = stmt.where(Sale.created_at >= start_date)
                if end_date:
                    stmt = stmt.where(Sale.created_at <= end_date)
                stmt = stmt.order_by(Sale.created_at.desc())
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(Sale).where(Sale.branch_id == branch_id)
            if start_date:
                stmt = stmt.where(Sale.created_at >= start_date)
            if end_date:
                stmt = stmt.where(Sale.created_at <= end_date)
            stmt = stmt.order_by(Sale.created_at.desc())
            return session.execute(stmt).scalars().all()

    def get_by_user(self, user_id, start_date=None, end_date=None, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(Sale).where(Sale.user_id == user_id)
                if start_date:
                    stmt = stmt.where(Sale.created_at >= start_date)
                if end_date:
                    stmt = stmt.where(Sale.created_at <= end_date)
                stmt = stmt.order_by(Sale.created_at.desc())
                return session.execute(stmt).scalars().all()
        else:
            stmt = select(Sale).where(Sale.user_id == user_id)
            if start_date:
                stmt = stmt.where(Sale.created_at >= start_date)
            if end_date:
                stmt = stmt.where(Sale.created_at <= end_date)
            stmt = stmt.order_by(Sale.created_at.desc())
            return session.execute(stmt).scalars().all()

    def get_daily_sales(self, branch_id, date=None, session=None):
        if date is None:
            date = datetime.now().date()
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        return self.get_by_branch(branch_id, start, end, session=session)

    def get_sales_summary(self, branch_id, start_date, end_date, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = select(
                    func.count(Sale.id).label("total_count"),
                    func.sum(Sale.grand_total).label("total_sales"),
                    func.avg(Sale.grand_total).label("average_sale"),
                ).where(
                    Sale.branch_id == branch_id,
                    Sale.created_at.between(start_date, end_date),
                    Sale.voided == 0,
                )
                return session.execute(stmt).one()
        else:
            stmt = select(
                func.count(Sale.id).label("total_count"),
                func.sum(Sale.grand_total).label("total_sales"),
                func.avg(Sale.grand_total).label("average_sale"),
            ).where(
                Sale.branch_id == branch_id,
                Sale.created_at.between(start_date, end_date),
                Sale.voided == 0,
            )
            return session.execute(stmt).one()

    def create_sale(
        self,
        session,
        branch_id,
        user_id,
        items_data,
        payment_data,
    ):
        subtotal = sum(item["subtotal"] for item in items_data)
        discount = payment_data.get("discount", 0)
        tax = payment_data.get("tax", 0)
        grand_total = subtotal - discount + tax

        sale = Sale(
            receipt_number=self._generate_receipt(branch_id),
            branch_id=branch_id,
            user_id=user_id,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            grand_total=grand_total,
            payment_method=payment_data["method"],
            status="COMPLETED",
        )
        session.add(sale)
        session.flush()

        for item in items_data:
            session.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"],
                )
            )

        session.add(
            Payment(
                sale_id=sale.id,
                method=payment_data["method"],
                amount=payment_data["amount"],
                reference=payment_data.get("reference"),
                mpesa_code=payment_data.get("mpesa_code"),
                status="COMPLETED",
            )
        )
        session.flush()

        return sale

    def get_sale_with_details(self, sale_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Sale)
                    .options(
                        selectinload(Sale.items),
                        selectinload(Sale.payments),
                        joinedload(Sale.etims_invoice),
                    )
                    .where(Sale.id == sale_id)
                )
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = (
                select(Sale)
                .options(
                    selectinload(Sale.items),
                    selectinload(Sale.payments),
                    joinedload(Sale.etims_invoice),
                )
                .where(Sale.id == sale_id)
            )
            return session.execute(stmt).scalar_one_or_none()

    def search_sales(self, query, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                pattern = f"%{query}%"
                stmt = (
                    select(Sale)
                    .join(User, User.id == Sale.user_id)
                    .where(Sale.branch_id == branch_id)
                    .where(
                        or_(
                            Sale.receipt_number.like(pattern),
                            User.full_name.like(pattern),
                        )
                    )
                    .order_by(Sale.created_at.desc())
                    .limit(50)
                )
                return session.execute(stmt).scalars().all()
        else:
            pattern = f"%{query}%"
            stmt = (
                select(Sale)
                .join(User, User.id == Sale.user_id)
                .where(Sale.branch_id == branch_id)
                .where(
                    or_(
                        Sale.receipt_number.like(pattern),
                        User.full_name.like(pattern),
                    )
                )
                .order_by(Sale.created_at.desc())
                .limit(50)
            )
            return session.execute(stmt).scalars().all()

    def get_cashier_performance(
        self, branch_id, start_date, end_date, session=None
    ):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(
                        User.id,
                        User.full_name,
                        func.count(Sale.id).label("sale_count"),
                        func.sum(Sale.grand_total).label("total_sales"),
                        func.avg(Sale.grand_total).label("average_sale"),
                    )
                    .join(User, User.id == Sale.user_id)
                    .where(Sale.branch_id == branch_id)
                    .where(Sale.created_at.between(start_date, end_date))
                    .where(Sale.voided == 0)
                    .group_by(User.id)
                    .order_by(desc(func.sum(Sale.grand_total)))
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(
                    User.id,
                    User.full_name,
                    func.count(Sale.id).label("sale_count"),
                    func.sum(Sale.grand_total).label("total_sales"),
                    func.avg(Sale.grand_total).label("average_sale"),
                )
                .join(User, User.id == Sale.user_id)
                .where(Sale.branch_id == branch_id)
                .where(Sale.created_at.between(start_date, end_date))
                .where(Sale.voided == 0)
                .group_by(User.id)
                .order_by(desc(func.sum(Sale.grand_total)))
            )
            return session.execute(stmt).all()

    def get_brand_sales_report(
        self, branch_id, start_date, end_date, session=None
    ):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(
                        Product.brand,
                        func.count(SaleItem.id).label("items_sold"),
                        func.sum(SaleItem.subtotal).label("total_sales"),
                        func.sum(
                            SaleItem.subtotal
                            - Product.cost_price * SaleItem.quantity
                        ).label("total_profit"),
                    )
                    .join(Product, Product.id == SaleItem.product_id)
                    .join(Sale, Sale.id == SaleItem.sale_id)
                    .where(Sale.branch_id == branch_id)
                    .where(Sale.created_at.between(start_date, end_date))
                    .where(Sale.voided == 0)
                    .where(Product.brand.isnot(None))
                    .where(Product.brand != "")
                    .group_by(Product.brand)
                    .order_by(desc(func.sum(SaleItem.subtotal)))
                )
                return session.execute(stmt).all()
        else:
            stmt = (
                select(
                    Product.brand,
                    func.count(SaleItem.id).label("items_sold"),
                    func.sum(SaleItem.subtotal).label("total_sales"),
                    func.sum(
                        SaleItem.subtotal
                        - Product.cost_price * SaleItem.quantity
                    ).label("total_profit"),
                )
                .join(Product, Product.id == SaleItem.product_id)
                .join(Sale, Sale.id == SaleItem.sale_id)
                .where(Sale.branch_id == branch_id)
                .where(Sale.created_at.between(start_date, end_date))
                .where(Sale.voided == 0)
                .where(Product.brand.isnot(None))
                .where(Product.brand != "")
                .group_by(Product.brand)
                .order_by(desc(func.sum(SaleItem.subtotal)))
            )
            return session.execute(stmt).all()
