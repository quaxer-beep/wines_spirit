from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import Supplier, SupplierRating, PurchaseOrder
from app.schemas.head_office import SupplierCreate, SupplierUpdate, SupplierRatingCreate, SupplierPerformance

logger = logging.getLogger(__name__)


class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SupplierCreate) -> Supplier:
        supplier = Supplier(
            name=data.name,
            contact_person=data.contact_person,
            phone=data.phone,
            email=data.email,
            physical_address=data.physical_address,
            tax_info=data.tax_info,
        )
        self.db.add(supplier)
        await self.db.flush()
        await self._log_audit("supplier", "CREATE", supplier.id, f"Supplier created: {supplier.name}")
        return supplier

    async def get(self, supplier_id: int) -> Supplier | None:
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, active_only: bool = False
    ) -> tuple[list[Supplier], int]:
        query = select(Supplier)
        if active_only:
            query = query.where(Supplier.is_active == True)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Supplier.name).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, supplier_id: int, data: SupplierUpdate) -> Supplier | None:
        supplier = await self.get(supplier_id)
        if not supplier:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        supplier.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self._log_audit("supplier", "UPDATE", supplier_id, f"Supplier updated: {supplier.name}")
        return supplier

    async def delete(self, supplier_id: int) -> bool:
        supplier = await self.get(supplier_id)
        if not supplier:
            return False
        await self.db.delete(supplier)
        await self.db.flush()
        await self._log_audit("supplier", "DELETE", supplier_id, f"Supplier deleted: {supplier.name}")
        return True

    async def add_rating(self, data: SupplierRatingCreate) -> SupplierRating:
        scores = [data.delivery_accuracy, data.delivery_timeliness, data.product_quality, data.order_fulfillment_rate]
        valid = [s for s in scores if s is not None]
        overall = sum(valid) / len(valid) if valid else 0

        rating = SupplierRating(
            supplier_id=data.supplier_id,
            delivery_accuracy=data.delivery_accuracy,
            delivery_timeliness=data.delivery_timeliness,
            product_quality=data.product_quality,
            order_fulfillment_rate=data.order_fulfillment_rate,
            overall_score=overall,
            notes=data.notes,
        )
        self.db.add(rating)
        await self.db.flush()

        result = await self.db.execute(
            select(func.avg(SupplierRating.overall_score)).where(
                SupplierRating.supplier_id == data.supplier_id
            )
        )
        avg_rating = result.scalar() or 0
        supplier = await self.get(data.supplier_id)
        if supplier:
            supplier.rating = round(avg_rating, 2)
            await self.db.flush()

        return rating

    async def get_performance(self, supplier_id: int) -> SupplierPerformance | None:
        supplier = await self.get(supplier_id)
        if not supplier:
            return None

        orders_query = select(func.count(), func.coalesce(func.sum(PurchaseOrder.grand_total), 0)).where(
            PurchaseOrder.supplier_id == supplier_id
        )
        orders_result = await self.db.execute(orders_query)
        total_orders, total_value = orders_result.first() or (0, 0)

        rating_result = await self.db.execute(
            select(func.avg(SupplierRating.overall_score)).where(
                SupplierRating.supplier_id == supplier_id
            )
        )
        avg_rating = rating_result.scalar() or 0

        return SupplierPerformance(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            total_orders=total_orders or 0,
            total_value=float(total_value or 0),
            overall_rating=round(float(avg_rating), 2),
        )

    async def get_all_performance(self) -> list[SupplierPerformance]:
        result = await self.db.execute(select(Supplier).where(Supplier.is_active == True))
        suppliers = result.scalars().all()
        performances = []
        for supplier in suppliers:
            perf = await self.get_performance(supplier.id)
            if perf:
                performances.append(perf)
        return sorted(performances, key=lambda x: x.overall_rating, reverse=True)

    async def _log_audit(self, resource_type: str, event_type: str, resource_id: int, description: str):
        from app.models.head_office import AuditEvent
        event = AuditEvent(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
        )
        self.db.add(event)
