import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import StockTransfer, StockTransferItem
from app.schemas.head_office import StockTransferCreate, StockTransferItemCreate
from app.services.head_office.transfer_service import TransferService


class TestTransferService:
    async def test_create(self, db_session: AsyncSession, sample_products, sample_branch):
        service = TransferService(db_session)
        data = StockTransferCreate(
            from_branch_id=sample_branch,
            to_branch_id=2,
            notes="Stock rebalance",
            items=[
                StockTransferItemCreate(product_id=sample_products[0].id, product_name=sample_products[0].name, quantity=5, unit_cost=600.0),
                StockTransferItemCreate(product_id=sample_products[1].id, product_name=sample_products[1].name, quantity=3, unit_cost=1500.0),
            ],
        )
        transfer = await service.create(data, user_id=1)
        await db_session.commit()

        result = await db_session.execute(
            select(StockTransferItem).where(StockTransferItem.stock_transfer_id == transfer.id)
        )
        items = result.scalars().all()

        assert transfer.id is not None
        assert transfer.transfer_number.startswith("TFR-")
        assert transfer.status == "requested"
        assert len(items) == 2

    async def test_approve(self, db_session: AsyncSession, sample_transfer: StockTransfer):
        service = TransferService(db_session)
        transfer = await service.approve(sample_transfer.id, user_id=2)
        await db_session.commit()
        assert transfer is not None
        assert transfer.status == "approved"
        assert transfer.approved_by == 2

    async def test_dispatch(self, db_session: AsyncSession, sample_transfer: StockTransfer):
        service = TransferService(db_session)
        t = await service.approve(sample_transfer.id, user_id=2)
        await db_session.flush()
        t = await service.dispatch(sample_transfer.id, user_id=3)
        await db_session.commit()
        assert t is not None
        assert t.status == "in_transit"
        assert t.dispatched_by == 3

    async def test_receive_full_flow(self, db_session: AsyncSession, sample_transfer: StockTransfer):
        service = TransferService(db_session)
        t = await service.approve(sample_transfer.id, user_id=2)
        await db_session.flush()
        t = await service.dispatch(sample_transfer.id, user_id=3)
        await db_session.flush()
        t = await service.receive(sample_transfer.id, user_id=4)
        await db_session.commit()
        assert t is not None
        assert t.status == "received"
        assert t.received_by == 4

    async def test_reject(self, db_session: AsyncSession, sample_transfer: StockTransfer):
        service = TransferService(db_session)
        transfer = await service.reject(sample_transfer.id, user_id=2, reason="Stock not available")
        await db_session.commit()
        assert transfer is not None
        assert transfer.status == "rejected"
        assert transfer.rejection_reason == "Stock not available"

    async def test_list(self, db_session: AsyncSession, sample_transfer: StockTransfer):
        service = TransferService(db_session)
        items, total = await service.list(page=1, page_size=20)
        assert total >= 1
