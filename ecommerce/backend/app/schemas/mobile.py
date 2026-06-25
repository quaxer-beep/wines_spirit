from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MobileDeviceRegisterRequest(BaseModel):
    device_token: str
    platform: str = Field(..., pattern="^(ios|android)$")
    device_model: str | None = None
    os_version: str | None = None
    app_version: str | None = None


class MobileDeviceResponse(BaseModel):
    id: int
    device_token: str
    platform: str
    device_model: str | None = None
    os_version: str | None = None
    app_version: str | None = None
    is_active: bool
    last_seen_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PushNotificationRequest(BaseModel):
    title: str
    body: str
    notification_type: str
    data: dict | None = None
    customer_id: int | None = None
    rider_id: int | None = None


class PushNotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    body: str
    sent_status: str
    sent_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiderLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: float | None = None
    speed: float | None = None
    bearing: float | None = None
    battery_level: float | None = Field(None, ge=0, le=100)
    delivery_id: int | None = None


class RiderLocationResponse(BaseModel):
    id: int
    rider_id: int
    latitude: float
    longitude: float
    accuracy: float | None = None
    speed: float | None = None
    bearing: float | None = None
    battery_level: float | None = None
    is_active_delivery: bool
    delivery_id: int | None = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryIncidentCreate(BaseModel):
    delivery_id: int
    incident_type: str = Field(..., pattern="^(customer_not_available|invalid_address|underage_recipient|refused_delivery|product_damage|other)$")
    description: str | None = None
    evidence_photo_urls: list[str] | None = None


class DeliveryIncidentResponse(BaseModel):
    id: int
    delivery_id: int
    rider_id: int | None = None
    incident_type: str
    description: str | None = None
    customer_notified: bool
    branch_notified: bool
    resolution_status: str
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MobileSessionResponse(BaseModel):
    id: int
    session_token: str
    is_active: bool
    started_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)


class AppPreferenceUpdate(BaseModel):
    theme: str | None = Field(None, pattern="^(light|dark)$")
    language: str | None = None
    notifications_enabled: bool | None = None
    location_tracking_enabled: bool | None = None
    biometric_enabled: bool | None = None


class AppPreferenceResponse(BaseModel):
    id: int
    app_type: str
    theme: str
    language: str
    notifications_enabled: bool
    location_tracking_enabled: bool
    biometric_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class CustomerAppProfile(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None = None
    date_of_birth: date | None = None
    age_verified: bool
    age_verification_status: str = "unverified"
    verification_timestamp: datetime | None = None
    is_legal_age: bool = False
    loyalty_points: int = 0
    loyalty_earned: int = 0
    loyalty_redeemed: int = 0
    addresses: list = []

    model_config = ConfigDict(from_attributes=True)


class RiderAppDashboard(BaseModel):
    assigned_deliveries: int = 0
    pending_deliveries: int = 0
    completed_today: int = 0
    total_earned_today: float = 0
    current_delivery: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class ManagerDashboard(BaseModel):
    today_sales: float = 0
    today_orders: int = 0
    inventory_value: float = 0
    low_stock_count: int = 0
    pending_deliveries: int = 0
    active_riders: int = 0
    pending_approvals: int = 0

    model_config = ConfigDict(from_attributes=True)


class ExecutiveDashboard(BaseModel):
    total_revenue: float = 0
    total_orders: int = 0
    net_profit: float = 0
    total_expenses: float = 0
    inventory_value: float = 0
    customer_count: int = 0
    active_branches: int = 0
    revenue_growth_pct: float = 0
    profit_margin_pct: float = 0

    model_config = ConfigDict(from_attributes=True)


class DeliveryAgeVerificationCreate(BaseModel):
    order_id: int
    document_type: str = Field(..., pattern="^(national_id|passport|alien_card)$")
    document_number: str


class DeliveryAgeVerificationResponse(BaseModel):
    id: int
    order_id: int
    rider_id: int | None = None
    document_type: str
    document_number: str
    verification_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryPaymentRequest(BaseModel):
    order_id: int
    customer_phone: str = Field(..., min_length=10, max_length=15)
    amount: float = Field(..., gt=0)


class DeliveryPaymentResponse(BaseModel):
    id: int
    order_id: int
    rider_id: int | None = None
    customer_phone: str
    mpesa_receipt: str | None = None
    amount: float
    status: str
    payment_timestamp: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class ProductReviewResponse(BaseModel):
    id: int
    product_id: int
    customer_id: int
    customer_name: str
    rating: int
    review: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
