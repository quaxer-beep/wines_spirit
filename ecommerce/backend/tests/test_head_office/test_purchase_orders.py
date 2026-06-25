import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import PurchaseOrder, PurchaseOrderItem, GoodsReceivedNote
from app.schemas.head_office import PurchaseOrderCreate, PurchaseOrderItemCreate, GoodsReceivedNoteCreate, GoodsReceivedItemCreate
from app.services.head_office.purchase_order_service import PurchaseOrderService
from app.services.head_office.grn_service import GRNService


class TestPurchaseOrderService:
    async def test_create(self, db_session: AsyncSession, sample_supplier, sample_branch):
        service = PurchaseOrderService(db_session)
        data = PurchaseOrderCreate(
            supplier_id=sample_supplier.id,
            branch_id=sample_branch,
            notes="Test PO",
            items=[
                PurchaseOrderItemCreate(product_name="Item A", quantity_ordered=10, unit_price=500.0),
                PurchaseOrderItemCreate(product_name="Item B", quantity_ordered=5, unit_price=1000.0),
            ],
        )
        po = await service.create(data, user_id=1)
        await db_session.commit()

        result = await db_session.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == po.id)
        )
        items = result.scalars().all()

        assert po.id is not None
        assert po.po_number.startswith("PO-")
        assert po.status == "draft"
        assert po.subtotal == 10000.0
        assert po.grand_total == 10000.0
        assert len(items) == 2

    async def test_submit(self, db_session: AsyncSession, sample_purchase_order: PurchaseOrder):
        service = PurchaseOrderService(db_session)
        po = await service.submit(sample_purchase_order.id)
        await db_session.commit()
        assert po is not None
        assert po.status == "submitted"

    async def test_approve(self, db_session: AsyncSession, sample_purchase_order: PurchaseOrder):
        service = PurchaseOrderService(db_session)
        po = await service.submit(sample_purchase_order.id)
        await db_session.flush()
        po = await service.approve(sample_purchase_order.id, user_id=1)
        await db_session.commit()
        assert po is not None
        assert po.status == "approved"
        assert po.approved_by == 1

    async def test_cancel(self, db_session: AsyncSession, sample_purchase_order: PurchaseOrder):
        service = PurchaseOrderService(db_session)
        po = await service.cancel(sample_purchase_order.id)
        await db_session.commit()
        assert po is not None
        assert po.status == "cancelled"

    async def test_receive_full_flow(self, db_session: AsyncSession, sample_purchase_order: PurchaseOrder, sample_supplier, sample_branch, sample_products):
        po_service = PurchaseOrderService(db_session)
        grn_service = GRNService(db_session)

        po = await po_service.submit(sample_purchase_order.id)
        await db_session.flush()
        po = await po_service.approve(sample_purchase_order.id, user_id=1)
        await db_session.flush()

        grn_data = GoodsReceivedNoteCreate(
            purchase_order_id=po.id,
            supplier_id=sample_supplier.id,
            branch_id=sample_branch,
            notes="All good",
            items=[
                GoodsReceivedItemCreate(product_id=sample_products[0].id, product_name="Test Wine", quantity_received=10, unit_cost=600.0),
                GoodsReceivedItemCreate(product_id=sample_products[1].id, product_name="Test Whisky", quantity_received=5, unit_cost=1500.0),
            ],
        )
        grn = await grn_service.create(grn_data, user_id=1)
        await db_session.commit()

        assert grn.id is not None
        assert grn.status == "completed"

        result = await db_session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po.id)
        )
        updated_po = result.scalar_one()
        assert updated_po.status == "received"

    async def test_list(self, db_session: AsyncSession, sample_purchase_order: PurchaseOrder):
        service = PurchaseOrderService(db_session)
        items, total = await service.list(page=1, page_size=20)
        assert total >= 1
