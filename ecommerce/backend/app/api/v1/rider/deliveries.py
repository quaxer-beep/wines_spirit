from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.customer import Delivery, Rider
from app.schemas.delivery import (
    DeliveryAgeVerificationRequest,
    DeliveryAgeVerificationResponse,
    DeliveryResponse,
    DeliveryStatusUpdate,
)
from app.services.delivery_service import DeliveryService

router = APIRouter()


async def get_rider_from_phone(
    phone: str, db: AsyncSession
) -> Rider:
    result = await db.execute(
        select(Rider).where(Rider.phone == phone, Rider.is_active == True)
    )
    rider = result.scalar_one_or_none()
    if not rider:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Rider not found")
    return rider


@router.get("/my-deliveries", response_model=list[DeliveryResponse])
async def my_deliveries(
    phone: str,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rider = await get_rider_from_phone(phone, db)
    service = DeliveryService(db)
    deliveries = await service.get_rider_deliveries(rider.id, status_filter)

    return [
        DeliveryResponse(
            id=d.id,
            order_id=d.order_id,
            rider_id=d.rider_id,
            rider_name=rider.name,
            rider_phone=rider.phone,
            address=d.address,
            latitude=d.latitude,
            longitude=d.longitude,
            distance_km=d.distance_km,
            estimated_duration_minutes=d.estimated_duration_minutes,
            delivery_fee=d.delivery_fee,
            status=d.status,
            started_at=d.started_at,
            picked_up_at=d.picked_up_at,
            delivered_at=d.delivered_at,
            notes=d.notes,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in deliveries
    ]


@router.put("/{delivery_id}/status", response_model=DeliveryResponse)
async def update_status(
    delivery_id: int,
    data: DeliveryStatusUpdate,
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    rider = await get_rider_from_phone(phone, db)
    service = DeliveryService(db)

    result = await db.execute(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.rider_id == rider.id,
        )
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    updated = await service.update_delivery_status(delivery_id, data.status, data.notes)
    await db.commit()

    return DeliveryResponse(
        id=updated.id,
        order_id=updated.order_id,
        rider_id=updated.rider_id,
        rider_name=rider.name,
        rider_phone=rider.phone,
        address=updated.address,
        latitude=updated.latitude,
        longitude=updated.longitude,
        distance_km=updated.distance_km,
        estimated_duration_minutes=updated.estimated_duration_minutes,
        delivery_fee=updated.delivery_fee,
        status=updated.status,
        started_at=updated.started_at,
        picked_up_at=updated.picked_up_at,
        delivered_at=updated.delivered_at,
        notes=updated.notes,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post("/{delivery_id}/verify", response_model=DeliveryAgeVerificationResponse)
async def verify_delivery_age(
    delivery_id: int,
    data: DeliveryAgeVerificationRequest,
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    rider = await get_rider_from_phone(phone, db)
    service = DeliveryService(db)

    result = await db.execute(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.rider_id == rider.id,
        )
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    try:
        verification = await service.verify_delivery(
            delivery_id=delivery_id,
            order_id=delivery.order_id,
            rider_id=rider.id,
            document_type=data.document_type,
            document_number=data.document_number,
        )
        await db.commit()

        return DeliveryAgeVerificationResponse(
            id=verification.id,
            order_id=verification.order_id,
            rider_id=verification.rider_id,
            document_type=verification.document_type,
            document_number=verification.document_number,
            verification_timestamp=verification.verification_timestamp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
