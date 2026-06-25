from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import StockTransfer, StockTransferItem
from app.schemas.head_office import StockTransferCreate

logger = logging.getLogger(__name__)


class TransferService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_transfer_number(self) -> str:
        result = await self.db.execute(select(func.count()).select_from(StockTransfer))
        count = result.scalar() or 0
        return f"TFR-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"

    async def create(self, data: StockTransferCreate, user_id: int | None = None) -> StockTransfer:
        transfer_number = await self._generate_transfer_number()
        transfer = StockTransfer(
            transfer_number=transfer_number,
            from_branch_id=data.from_branch_id,
            to_branch_id=data.to_branch_id,
            requested_by=user_id,
            status="requested",
            notes=data.notes,
        )
        self.db.add(transfer)
        await self.db.flush()

        for item_data in data.items:
            item = StockTransferItem(
                stock_transfer_id=transfer.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                quantity=item_data.quantity,
                unit_cost=item_data.unit_cost,
            )
            self.db.add(item)

        await self.db.flush()
        await self._log_audit("stock_transfer", "CREATE", transfer.id, f"Transfer created: {transfer_number}")
        return transfer

    async def get(self, transfer_id: int) -> StockTransfer | None:
        result = await self.db.execute(
            select(StockTransfer).where(StockTransfer.id == transfer_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, status: str | None = None, branch_id: int | None = None
    ) -> tuple[list[StockTransfer], int]:
        query = select(StockTransfer)
        if status:
            query = query.where(StockTransfer.status == status)
        if branch_id:
            query = query.where(
                (StockTransfer.from_branch_id == branch_id) | (StockTransfer.to_branch_id == branch_id)
            )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(StockTransfer.requested_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def approve(self, transfer_id: int, user_id: int) -> StockTransfer | None:
        transfer = await self.get(transfer_id)
        if not transfer or transfer.status != "requested":
            return None
        transfer.status = "approved"
        transfer.approved_by = user_id
        transfer.approved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("stock_transfer", "APPROVE", transfer_id, f"Transfer approved: {transfer.transfer_number}")
        return transfer

    async def dispatch(self, transfer_id: int, user_id: int) -> StockTransfer | None:
        transfer = await self.get(transfer_id)
        if not transfer or transfer.status != "approved":
            return None
        transfer.status = "in_transit"
        transfer.dispatched_by = user_id
        transfer.dispatched_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("stock_transfer", "DISPATCH", transfer_id, f"Transfer dispatched: {transfer.transfer_number}")
        return transfer

    async def receive(self, transfer_id: int, user_id: int) -> StockTransfer | None:
        transfer = await self.get(transfer_id)
        if not transfer or transfer.status != "in_transit":
            return None
        transfer.status = "received"
        transfer.received_by = user_id
        transfer.received_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("stock_transfer", "RECEIVE", transfer_id, f"Transfer received: {transfer.transfer_number}")
        return transfer

    async def reject(self, transfer_id: int, user_id: int, reason: str) -> StockTransfer | None:
        transfer = await self.get(transfer_id)
        if not transfer or transfer.status != "requested":
            return None
        transfer.status = "rejected"
        transfer.approved_by = user_id
        transfer.approved_at = datetime.now(timezone.utc)
        transfer.rejection_reason = reason
        await self.db.flush()
        await self._log_audit("stock_transfer", "REJECT", transfer_id, f"Transfer rejected: {transfer.transfer_number}")
        return transfer

    async def get_pending_for_branch(self, branch_id: int) -> list[StockTransfer]:
        result = await self.db.execute(
            select(StockTransfer)
            .where(
                (StockTransfer.to_branch_id == branch_id) | (StockTransfer.from_branch_id == branch_id),
                StockTransfer.status.in_(["requested", "approved", "in_transit"]),
            )
            .order_by(StockTransfer.requested_at.desc())
        )
        return list(result.scalars().all())

    async def _log_audit(self, resource_type: str, event_type: str, resource_id: int, description: str):
        from app.models.head_office import AuditEvent
        event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
        )
        self.db.add(event)
