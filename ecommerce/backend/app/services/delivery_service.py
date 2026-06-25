from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.customer import (
    Delivery,
    DeliveryAgeVerification,
    DeliveryFee,
    Order,
    Rider,
)

logger = logging.getLogger(__name__)


class DeliveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_fee_config(self) -> DeliveryFee | None:
        result = await self.db.execute(
            select(DeliveryFee).where(DeliveryFee.is_active == True).order_by(DeliveryFee.id.desc())
        )
        return result.scalar_one_or_none()

    async def calculate_delivery_fee(
        self,
        distance_km: float | None = None,
    ) -> dict:
        config = await self.get_active_fee_config()
        if not config:
            base_fee = settings.BASE_DELIVERY_FEE
            per_km_rate = settings.DELIVERY_PER_KM_RATE
            fuel_pct = settings.FUEL_ADJUSTMENT_PCT
        else:
            base_fee = config.base_fee
            per_km_rate = config.per_km_rate
            fuel_pct = config.fuel_adjustment_pct

        distance = distance_km or 1.0

        if config and config.min_distance_km and distance < config.min_distance_km:
            distance = config.min_distance_km
        if config and config.max_distance_km and distance > config.max_distance_km:
            raise ValueError(f"Delivery distance {distance:.1f}km exceeds maximum allowed {config.max_distance_km}km")

        base_fee_charged = base_fee
        distance_fee = distance * per_km_rate
        fuel_surcharge = (base_fee_charged + distance_fee) * (fuel_pct / 100)
        total_fee = base_fee_charged + distance_fee + fuel_surcharge

        return {
            "distance_km": distance,
            "base_fee": round(base_fee_charged, 2),
            "distance_fee": round(distance_fee, 2),
            "fuel_surcharge": round(fuel_surcharge, 2),
            "total_fee": round(total_fee, 2),
        }

    async def create_delivery(self, order_id: int, address: str, delivery_fee: float) -> Delivery:
        delivery = Delivery(
            order_id=order_id,
            address=address,
            delivery_fee=delivery_fee,
            status="pending",
        )
        self.db.add(delivery)
        await self.db.flush()
        return delivery

    async def assign_rider(self, delivery_id: int, rider_id: int) -> Delivery:
        result = await self.db.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        if not delivery:
            raise ValueError("Delivery not found")

        rider_result = await self.db.execute(
            select(Rider).where(Rider.id == rider_id, Rider.is_active == True)
        )
        rider = rider_result.scalar_one_or_none()
        if not rider:
            raise ValueError("Rider not found or inactive")

        delivery.rider_id = rider_id
        delivery.status = "assigned"
        rider.status = "on_delivery"
        await self.db.flush()
        return delivery

    async def update_delivery_status(
        self, delivery_id: int, status: str, notes: str | None = None
    ) -> Delivery:
        result = await self.db.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        if not delivery:
            raise ValueError("Delivery not found")

        now = datetime.now(timezone.utc)
        delivery.status = status
        if notes:
            delivery.notes = notes

        if status == "picked_up":
            delivery.picked_up_at = now
        elif status == "in_transit":
            if not delivery.started_at:
                delivery.started_at = now
        elif status == "delivered":
            delivery.delivered_at = now

        await self.db.flush()

        order_result = await self.db.execute(
            select(Order).where(Order.id == delivery.order_id)
        )
        order = order_result.scalar_one_or_none()
        if order:
            order.delivery_status = status
            if status == "delivered":
                order.status = "delivered"
            await self.db.flush()

        return delivery

    async def get_available_riders(self, branch_id: int | None = None) -> list[Rider]:
        query = select(Rider).where(
            Rider.is_active == True,
            Rider.status == "available",
        )
        if branch_id:
            query = query.where(Rider.branch_id == branch_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_rider_deliveries(
        self, rider_id: int, status: str | None = None
    ) -> list[Delivery]:
        query = select(Delivery).where(Delivery.rider_id == rider_id)
        if status:
            query = query.where(Delivery.status == status)
        query = query.order_by(Delivery.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def verify_delivery(
        self, delivery_id: int, order_id: int, rider_id: int,
        document_type: str, document_number: str,
    ) -> DeliveryAgeVerification:
        existing = await self.db.execute(
            select(DeliveryAgeVerification).where(
                DeliveryAgeVerification.order_id == order_id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Delivery already verified")

        verification = DeliveryAgeVerification(
            order_id=order_id,
            rider_id=rider_id,
            document_type=document_type,
            document_number=document_number,
        )
        self.db.add(verification)
        await self.db.flush()

        await self.update_delivery_status(delivery_id, "age_verified")

        return verification

    async def get_delivery_for_order(self, order_id: int) -> Delivery | None:
        result = await self.db.execute(
            select(Delivery)
            .where(Delivery.order_id == order_id)
            .options(
                selectinload(Delivery.rider),
            )
        )
        return result.scalar_one_or_none()
