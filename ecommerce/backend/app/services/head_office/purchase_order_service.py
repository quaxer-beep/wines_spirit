from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import PurchaseOrder, PurchaseOrderItem, Supplier, GoodsReceivedNote
from app.schemas.head_office import PurchaseOrderCreate

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_po_number(self) -> str:
        result = await self.db.execute(select(func.count()).select_from(PurchaseOrder))
        count = result.scalar() or 0
        return f"PO-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"

    async def create(self, data: PurchaseOrderCreate, user_id: int | None = None) -> PurchaseOrder:
        po_number = await self._generate_po_number()
        subtotal = sum(item.quantity_ordered * item.unit_price for item in data.items)

        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=data.supplier_id,
            branch_id=data.branch_id,
            ordered_by=user_id,
            status="draft",
            subtotal=subtotal,
            tax=0,
            grand_total=subtotal,
            notes=data.notes,
            expected_delivery_date=data.expected_delivery_date,
        )
        self.db.add(po)
        await self.db.flush()

        for item_data in data.items:
            item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity_ordered=item_data.quantity_ordered,
                unit_price=item_data.unit_price,
                subtotal=item_data.quantity_ordered * item_data.unit_price,
            )
            self.db.add(item)

        await self.db.flush()
        await self._log_audit("purchase_order", "CREATE", po.id, f"PO created: {po_number}")
        return po

    async def get(self, po_id: int) -> PurchaseOrder | None:
        result = await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, status: str | None = None, supplier_id: int | None = None
    ) -> tuple[list[PurchaseOrder], int]:
        query = select(PurchaseOrder)
        if status:
            query = query.where(PurchaseOrder.status == status)
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(PurchaseOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def approve(self, po_id: int, user_id: int) -> PurchaseOrder | None:
        po = await self.get(po_id)
        if not po or po.status != "submitted":
            return None
        po.status = "approved"
        po.approved_by = user_id
        po.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("purchase_order", "APPROVE", po_id, f"PO approved: {po.po_number}")
        return po

    async def submit(self, po_id: int) -> PurchaseOrder | None:
        po = await self.get(po_id)
        if not po or po.status != "draft":
            return None
        po.status = "submitted"
        await self.db.flush()
        await self._log_audit("purchase_order", "SUBMIT", po_id, f"PO submitted: {po.po_number}")
        return po

    async def receive(self, po_id: int, actual_delivery_date: datetime | None = None) -> PurchaseOrder | None:
        po = await self.get(po_id)
        if not po or po.status not in ("submitted", "approved"):
            return None
        po.status = "received"
        po.actual_delivery_date = actual_delivery_date.date() if actual_delivery_date else datetime.now(timezone.utc).date()
        po.received_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("purchase_order", "RECEIVE", po_id, f"PO received: {po.po_number}")
        return po

    async def cancel(self, po_id: int) -> PurchaseOrder | None:
        po = await self.get(po_id)
        if not po or po.status in ("received", "cancelled"):
            return None
        po.status = "cancelled"
        await self.db.flush()
        await self._log_audit("purchase_order", "CANCEL", po_id, f"PO cancelled: {po.po_number}")
        return po

    async def get_supplier_po_stats(self, supplier_id: int) -> dict:
        result = await self.db.execute(
            select(
                func.count().label("total_orders"),
                func.coalesce(func.sum(PurchaseOrder.grand_total), 0).label("total_value"),
                func.avg(
                    func.julianday(PurchaseOrder.actual_delivery_date) -
                    func.julianday(PurchaseOrder.expected_delivery_date)
                ).label("avg_delay"),
            ).where(PurchaseOrder.supplier_id == supplier_id)
        )
        row = result.first()
        return {
            "total_orders": row[0] or 0,
            "total_value": float(row[1] or 0),
            "avg_delay_days": float(row[2] or 0) if row[2] is not None else 0,
        }

    async def _log_audit(self, resource_type: str, event_type: str, resource_id: int, description: str):
        from app.models.head_office import AuditEvent
        event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
        )
        self.db.add(event)
