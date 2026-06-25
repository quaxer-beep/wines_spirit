from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import (
    GoodsReceivedNote,
    GoodsReceivedItem,
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.schemas.head_office import GoodsReceivedNoteCreate

logger = logging.getLogger(__name__)


class GRNService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_grn_number(self) -> str:
        result = await self.db.execute(select(func.count()).select_from(GoodsReceivedNote))
        count = result.scalar() or 0
        return f"GRN-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"

    async def create(self, data: GoodsReceivedNoteCreate, user_id: int | None = None) -> GoodsReceivedNote:
        grn_number = await self._generate_grn_number()

        grn = GoodsReceivedNote(
            grn_number=grn_number,
            purchase_order_id=data.purchase_order_id,
            supplier_id=data.supplier_id,
            branch_id=data.branch_id,
            received_by=user_id,
            delivery_note_number=data.delivery_note_number,
            invoice_reference=data.invoice_reference,
            status="completed",
            notes=data.notes,
        )
        self.db.add(grn)
        await self.db.flush()

        total_cost = 0
        for item_data in data.items:
            item_total = item_data.quantity_received * item_data.unit_cost
            total_cost += item_total
            item = GoodsReceivedItem(
                grn_id=grn.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity_received=item_data.quantity_received,
                unit_cost=item_data.unit_cost,
                total_cost=item_total,
            )
            self.db.add(item)

            po_item_result = await self.db.execute(
                select(PurchaseOrderItem).where(
                    PurchaseOrderItem.purchase_order_id == data.purchase_order_id,
                    PurchaseOrderItem.product_id == item_data.product_id,
                )
            )
            po_item = po_item_result.scalar_one_or_none()
            if po_item:
                po_item.quantity_received = (po_item.quantity_received or 0) + item_data.quantity_received

        await self.db.flush()

        po_result = await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.id == data.purchase_order_id)
        )
        po = po_result.scalar_one_or_none()
        if po:
            po.status = "received"
            po.actual_delivery_date = datetime.now(timezone.utc).date()
            po.received_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self._log_audit("grn", "CREATE", grn.id, f"GRN created: {grn_number}")
        return grn

    async def get(self, grn_id: int) -> GoodsReceivedNote | None:
        result = await self.db.execute(
            select(GoodsReceivedNote).where(GoodsReceivedNote.id == grn_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, supplier_id: int | None = None
    ) -> tuple[list[GoodsReceivedNote], int]:
        query = select(GoodsReceivedNote)
        if supplier_id:
            query = query.where(GoodsReceivedNote.supplier_id == supplier_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(GoodsReceivedNote.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def _log_audit(self, resource_type: str, event_type: str, resource_id: int, description: str):
        from app.models.head_office import AuditEvent
        event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
        )
        self.db.add(event)
