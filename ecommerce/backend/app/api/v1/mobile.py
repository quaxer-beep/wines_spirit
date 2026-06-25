from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_authenticated_customer, get_db, get_rider_user
from app.models.customer import Customer, Delivery, Notification, Order, Product, Rider
from app.models.mobile import (
    AppPreference,
    DeliveryIncident,
    MobileDevice,
    MobileSession,
    PushNotification,
    RiderLocation,
)
from app.schemas.mobile import (
    AppPreferenceResponse,
    AppPreferenceUpdate,
    CustomerAppProfile,
    DeliveryAgeVerificationCreate,
    DeliveryAgeVerificationResponse,
    DeliveryIncidentCreate,
    DeliveryIncidentResponse,
    DeliveryPaymentRequest,
    DeliveryPaymentResponse,
    ExecutiveDashboard,
    ManagerDashboard,
    MobileDeviceRegisterRequest,
    MobileDeviceResponse,
    MobileSessionResponse,
    PushNotificationResponse,
    RiderAppDashboard,
    RiderLocationResponse,
    RiderLocationUpdate,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.loyalty_service import LoyaltyService
from app.services.mobile_service import (
    DeliveryAgeVerificationService,
    DeliveryIncidentService,
    DeliveryPaymentService,
    MobileAuthService,
    MobileDashboardService,
    PushNotificationService,
    RiderTrackingService,
)
from app.services.notification_service import NotificationService as InAppNotificationService

router = APIRouter(prefix="/mobile", tags=["Mobile"])


@router.post("/devices/register", response_model=MobileDeviceResponse)
async def register_device(
    data: MobileDeviceRegisterRequest,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    role = current_user.role
    rider_id = current_user.id if role == "rider" else None
    customer_id = current_user.id if role == "customer" else None
    device = await service.register_device(
        customer_id=customer_id,
        rider_id=rider_id,
        device_token=data.device_token,
        platform=data.platform,
        device_model=data.device_model,
        os_version=data.os_version,
        app_version=data.app_version,
    )
    await db.commit()
    return device


@router.post("/devices/unregister", response_model=MessageResponse)
async def unregister_device(
    device_token: str,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    await service.unregister_device(device_token)
    await db.commit()
    return MessageResponse(message="Device unregistered", status_code=200)


@router.get("/devices", response_model=list[MobileDeviceResponse])
async def list_devices(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    return await service.get_devices(current_user.id)


@router.get("/preferences", response_model=AppPreferenceResponse)
async def get_preferences(
    app_type: str = Query(..., pattern="^(customer|rider|manager|executive)$"),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    role = current_user.role
    rider_id = current_user.id if role == "rider" else None
    customer_id = current_user.id if role in ("customer", "admin") else None
    prefs = await service.get_or_create_preferences(customer_id, rider_id, app_type)
    return prefs


@router.put("/preferences", response_model=AppPreferenceResponse)
async def update_preferences(
    data: AppPreferenceUpdate,
    app_type: str = Query(..., pattern="^(customer|rider|manager|executive)$"),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    role = current_user.role
    rider_id = current_user.id if role == "rider" else None
    customer_id = current_user.id if role in ("customer", "admin") else None
    prefs = await service.get_or_create_preferences(customer_id, rider_id, app_type)
    updated = await service.update_preferences(
        prefs.id, data.model_dump(exclude_none=True)
    )
    await db.commit()
    if not updated:
        raise HTTPException(404, "Preferences not found")
    return updated


@router.get("/sessions", response_model=list[MobileSessionResponse])
async def list_sessions(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    return await service.get_active_sessions(current_user.id)


@router.post("/sessions/{session_token}/end", response_model=MessageResponse)
async def end_session(
    session_token: str,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileAuthService(db)
    await service.end_session(session_token)
    await db.commit()
    return MessageResponse(message="Session ended", status_code=200)


@router.get("/dashboard/customer", response_model=CustomerAppProfile)
async def customer_dashboard(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = MobileDashboardService(db)
    return await service.get_customer_profile(current_user.id)


@router.get("/dashboard/rider", response_model=RiderAppDashboard)
async def rider_dashboard(
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = MobileDashboardService(db)
    return await service.get_rider_dashboard(current_user.id)


@router.get("/dashboard/manager", response_model=ManagerDashboard)
async def manager_dashboard(
    branch_id: int = Query(..., ge=1),
    current_user: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = MobileDashboardService(db)
    return await service.get_manager_dashboard(branch_id)


@router.get("/dashboard/executive", response_model=ExecutiveDashboard)
async def executive_dashboard(
    current_user: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = MobileDashboardService(db)
    return await service.get_executive_dashboard()


@router.post("/location/update", response_model=RiderLocationResponse)
async def update_location(
    data: RiderLocationUpdate,
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = RiderTrackingService(db)
    location = await service.update_location(
        rider_id=current_user.id,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
        speed=data.speed,
        bearing=data.bearing,
        battery_level=data.battery_level,
        delivery_id=data.delivery_id,
    )
    await db.commit()
    return location


@router.get("/location/riders", response_model=list[dict])
async def get_active_riders(
    branch_id: int | None = Query(None),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = RiderTrackingService(db)
    return await service.get_active_rider_locations(branch_id)


@router.get("/location/nearby", response_model=list[dict])
async def get_nearby_riders(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    branch_id: int | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = RiderTrackingService(db)
    return await service.get_nearest_riders(latitude, longitude, branch_id, limit)


@router.get("/location/history", response_model=list[RiderLocationResponse])
async def get_location_history(
    rider_id: int = Query(...),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = RiderTrackingService(db)
    return await service.get_rider_location_history(rider_id, limit)


@router.post("/incidents", response_model=DeliveryIncidentResponse, status_code=201)
async def report_incident(
    data: DeliveryIncidentCreate,
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryIncidentService(db)
    incident = await service.create_incident(
        delivery_id=data.delivery_id,
        rider_id=current_user.id,
        incident_type=data.incident_type,
        description=data.description,
        evidence_photo_urls=data.evidence_photo_urls,
    )
    await db.commit()
    return incident


@router.get("/incidents", response_model=PaginatedResponse)
async def list_incidents(
    delivery_id: int | None = Query(None),
    status: str | None = Query(None, pattern="^(open|resolved|dismissed)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryIncidentService(db)
    rider_id = current_user.id if current_user.role == "rider" else None
    incidents, total = await service.get_incidents(
        delivery_id=delivery_id,
        rider_id=rider_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [DeliveryIncidentResponse.model_validate(i).model_dump() for i in incidents],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.post("/incidents/{incident_id}/resolve", response_model=DeliveryIncidentResponse)
async def resolve_incident(
    incident_id: int,
    resolution_status: str = Query(..., pattern="^(resolved|dismissed)$"),
    resolution_notes: str | None = Query(None),
    current_user: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryIncidentService(db)
    incident = await service.resolve_incident(
        incident_id=incident_id,
        resolved_by=current_user.id,
        resolution_status=resolution_status,
        resolution_notes=resolution_notes,
    )
    await db.commit()
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


@router.post("/delivery/verify-age", response_model=DeliveryAgeVerificationResponse, status_code=201)
async def verify_age_delivery(
    data: DeliveryAgeVerificationCreate,
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryAgeVerificationService(db)
    verification = await service.verify_age(
        order_id=data.order_id,
        rider_id=current_user.id,
        document_type=data.document_type,
        document_number=data.document_number,
    )
    await db.commit()
    return verification


@router.get("/delivery/verification/{order_id}", response_model=DeliveryAgeVerificationResponse | None)
async def get_delivery_verification(
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryAgeVerificationService(db)
    return await service.get_verification(order_id)


@router.post("/delivery/payment", response_model=DeliveryPaymentResponse, status_code=201)
async def initiate_delivery_payment(
    data: DeliveryPaymentRequest,
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryPaymentService(db)
    try:
        payment = await service.initiate_payment(
            order_id=data.order_id,
            rider_id=current_user.id,
            customer_phone=data.customer_phone,
            amount=data.amount,
        )
        await db.commit()
        return payment
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, f"Payment initiation failed: {e}")


@router.post("/delivery/payment/{payment_id}/retry", response_model=DeliveryPaymentResponse)
async def retry_delivery_payment(
    payment_id: int,
    current_user: Customer = Depends(get_rider_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryPaymentService(db)
    try:
        payment = await service.retry_payment(payment_id)
        await db.commit()
        if not payment:
            raise HTTPException(404, "Payment not found or already completed")
        return payment
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, f"Payment retry failed: {e}")


@router.get("/delivery/payment/{order_id}", response_model=DeliveryPaymentResponse | None)
async def get_delivery_payment(
    order_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = DeliveryPaymentService(db)
    return await service.get_payment(order_id)


@router.post("/notifications/send", response_model=list[PushNotificationResponse])
async def send_notification(
    title: str = Query(...),
    body: str = Query(...),
    notification_type: str = Query("general"),
    customer_id: int | None = Query(None),
    rider_id: int | None = Query(None),
    current_user: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = PushNotificationService(db)
    if customer_id:
        notifications = await service.send_to_customer(
            customer_id, title, body, notification_type=notification_type
        )
    elif rider_id:
        notifications = await service.send_to_rider(
            rider_id, title, body, notification_type=notification_type
        )
    else:
        raise HTTPException(400, "Specify customer_id or rider_id")
    await db.commit()
    return notifications


@router.get("/notifications", response_model=list[PushNotificationResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = PushNotificationService(db)
    rider_id = current_user.id if current_user.role == "rider" else None
    customer_id = current_user.id if current_user.role == "customer" else None
    notifications, _ = await service.get_notifications(
        customer_id=customer_id, rider_id=rider_id,
        page=page, page_size=page_size,
    )
    return [PushNotificationResponse.model_validate(n).model_dump() for n in notifications]


@router.post("/notifications/{notification_id}/read", response_model=PushNotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = PushNotificationService(db)
    n = await service.mark_read(notification_id)
    if not n:
        raise HTTPException(404, "Notification not found")
    return n
