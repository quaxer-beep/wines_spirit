from datetime import datetime

from sqlalchemy import select, and_

from src.database.connection import db_manager
from src.database.models import Inventory, Product, StockMovement
from src.repositories.base import BaseRepository


class InventoryRepository(BaseRepository):
    def __init__(self):
        super().__init__(Inventory)

    def get_by_product_and_branch(self, product_id, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Inventory)
                    .where(Inventory.product_id == product_id)
                    .where(Inventory.branch_id == branch_id)
                )
                return session.execute(stmt).scalar_one_or_none()
        else:
            stmt = (
                select(Inventory)
                .where(Inventory.product_id == product_id)
                .where(Inventory.branch_id == branch_id)
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_by_branch(self, branch_id, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(Inventory)
                    .where(Inventory.branch_id == branch_id)
                    .order_by(Inventory.product_id)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(Inventory)
                .where(Inventory.branch_id == branch_id)
                .order_by(Inventory.product_id)
            )
            return session.execute(stmt).scalars().all()

    def get_branch_inventory(self, branch_id, session=None):
        return self.get_by_branch(branch_id, session=session)

    def adjust_quantity(
        self,
        session,
        inventory_id,
        quantity_change,
        movement_type,
        user_id,
        reference,
        notes,
    ):
        stmt = select(Inventory).where(Inventory.id == inventory_id)
        inv = session.execute(stmt).scalar_one_or_none()
        if inv is None:
            raise ValueError(f"Inventory record {inventory_id} not found")

        inv.quantity_on_hand += quantity_change

        movement = StockMovement(
            product_id=inv.product_id,
            branch_id=inv.branch_id,
            movement_type=movement_type,
            quantity=quantity_change,
            reference_type=reference,
            notes=notes,
            created_by=user_id,
        )
        session.add(movement)
        session.flush()

        return inv

    def transfer_stock(
        self,
        session,
        from_branch_id,
        to_branch_id,
        product_id,
        quantity,
        user_id,
    ):
        from_inv = session.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .where(Inventory.branch_id == from_branch_id)
        ).scalar_one_or_none()
        if from_inv is None or from_inv.quantity_on_hand < quantity:
            raise ValueError("Insufficient stock at source branch")

        to_inv = session.execute(
            select(Inventory)
            .where(Inventory.product_id == product_id)
            .where(Inventory.branch_id == to_branch_id)
        ).scalar_one_or_none()
        if to_inv is None:
            to_inv = Inventory(
                product_id=product_id,
                branch_id=to_branch_id,
                quantity_on_hand=0,
            )
            session.add(to_inv)

        from_inv.quantity_on_hand -= quantity
        to_inv.quantity_on_hand += quantity

        session.add(
            StockMovement(
                product_id=product_id,
                branch_id=from_branch_id,
                movement_type="TRANSFER",
                quantity=-quantity,
                reference_type="TRANSFER_OUT",
                notes=f"Transfer out to branch {to_branch_id}",
                created_by=user_id,
            )
        )
        session.add(
            StockMovement(
                product_id=product_id,
                branch_id=to_branch_id,
                movement_type="TRANSFER",
                quantity=quantity,
                reference_type="TRANSFER_IN",
                notes=f"Transfer in from branch {from_branch_id}",
                created_by=user_id,
            )
        )
        session.flush()

        return from_inv, to_inv

    def get_stock_movements(self, branch_id, start_date, end_date, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(StockMovement)
                    .where(StockMovement.branch_id == branch_id)
                    .where(
                        StockMovement.created_at.between(start_date, end_date)
                    )
                    .order_by(StockMovement.created_at.desc())
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(StockMovement)
                .where(StockMovement.branch_id == branch_id)
                .where(
                    StockMovement.created_at.between(start_date, end_date)
                )
                .order_by(StockMovement.created_at.desc())
            )
            return session.execute(stmt).scalars().all()

    def get_movement_history(self, product_id, branch_id, limit=50, session=None):
        if session is None:
            with db_manager.get_session() as session:
                stmt = (
                    select(StockMovement)
                    .where(StockMovement.product_id == product_id)
                    .where(StockMovement.branch_id == branch_id)
                    .order_by(StockMovement.created_at.desc())
                    .limit(limit)
                )
                return session.execute(stmt).scalars().all()
        else:
            stmt = (
                select(StockMovement)
                .where(StockMovement.product_id == product_id)
                .where(StockMovement.branch_id == branch_id)
                .order_by(StockMovement.created_at.desc())
                .limit(limit)
            )
            return session.execute(stmt).scalars().all()
