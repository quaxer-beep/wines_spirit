from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.delivery import (
    DeliveryFeeEstimateRequest,
    DeliveryFeeEstimateResponse,
    DeliveryResponse,
)
from app.services.delivery_service import DeliveryService
from app.services.order_service import OrderService

router = APIRouter()


@router.post("/estimate-fee", response_model=DeliveryFeeEstimateResponse)
async def estimate_fee(
    data: DeliveryFeeEstimateRequest,
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryService(db)
    try:
        fee_data = await service.calculate_delivery_fee()
        return DeliveryFeeEstimateResponse(
            distance_km=fee_data["distance_km"],
            estimated_duration_minutes=30,
            base_fee=fee_data["base_fee"],
            distance_fee=fee_data["distance_fee"],
            fuel_surcharge=fee_data["fuel_surcharge"],
            total_fee=fee_data["total_fee"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/track/{order_id}", response_model=DeliveryResponse)
async def track_delivery(
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, current_user.id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    delivery_service = DeliveryService(db)
    delivery = await delivery_service.get_delivery_for_order(order_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    return DeliveryResponse(
        id=delivery.id,
        order_id=delivery.order_id,
        rider_id=delivery.rider_id,
        rider_name=delivery.rider.name if delivery.rider else None,
        rider_phone=delivery.rider.phone if delivery.rider else None,
        address=delivery.address,
        latitude=delivery.latitude,
        longitude=delivery.longitude,
        distance_km=delivery.distance_km,
        estimated_duration_minutes=delivery.estimated_duration_minutes,
        delivery_fee=delivery.delivery_fee,
        status=delivery.status,
        started_at=delivery.started_at,
        picked_up_at=delivery.picked_up_at,
        delivered_at=delivery.delivered_at,
        notes=delivery.notes,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )
