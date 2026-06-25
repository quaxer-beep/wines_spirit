from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampMixin


class DeliveryFeeResponse(BaseModel):
    id: int
    base_fee: float
    per_km_rate: float
    fuel_adjustment_pct: float
    min_distance_km: float = 0
    max_distance_km: float | None = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class DeliveryFeeUpdate(BaseModel):
    base_fee: float | None = None
    per_km_rate: float | None = None
    fuel_adjustment_pct: float | None = None
    min_distance_km: float | None = None
    max_distance_km: float | None = None
    is_active: bool | None = None


class DeliveryFeeEstimateRequest(BaseModel):
    address_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    destination: str | None = None


class DeliveryFeeEstimateResponse(BaseModel):
    distance_km: float
    estimated_duration_minutes: int
    base_fee: float
    distance_fee: float
    fuel_surcharge: float
    total_fee: float
    currency: str = "KES"


class RiderBase(BaseModel):
    name: str
    phone: str
    email: str | None = None
    vehicle_type: str
    plate_number: str
    branch_id: int | None = None


class RiderCreate(RiderBase):
    pass


class RiderUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    vehicle_type: str | None = None
    plate_number: str | None = None
    status: str | None = None
    branch_id: int | None = None
    is_active: bool | None = None


class RiderResponse(RiderBase, TimestampMixin):
    id: int
    status: str = "available"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class DeliveryResponse(TimestampMixin):
    id: int
    order_id: int
    rider_id: int | None = None
    rider_name: str | None = None
    rider_phone: str | None = None
    address: str
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float | None = None
    estimated_duration_minutes: int | None = None
    delivery_fee: float
    status: str
    started_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryAssignRequest(BaseModel):
    rider_id: int


class DeliveryStatusUpdate(BaseModel):
    status: str
    notes: str | None = None


class DeliveryAgeVerificationRequest(BaseModel):
    delivery_id: int
    document_type: str
    document_number: str


class DeliveryAgeVerificationResponse(BaseModel):
    id: int
    order_id: int
    rider_id: int | None = None
    document_type: str
    document_number: str
    verification_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
