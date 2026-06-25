from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import Customer, Delivery, DeliveryAgeVerification, Order, Rider
from app.models.mobile import (
    AppPreference,
    DeliveryIncident,
    DeliveryPayment,
    MobileDevice,
    MobileSession,
    PushNotification as PushNotificationModel,
    RiderLocation,
)

logger = logging.getLogger(__name__)


class MobileAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_device(
        self, customer_id: int | None, rider_id: int | None, device_token: str,
        platform: str, device_model: str | None = None,
        os_version: str | None = None, app_version: str | None = None,
    ) -> MobileDevice:
        result = await self.db.execute(
            select(MobileDevice).where(MobileDevice.device_token == device_token)
        )
        device = result.scalar_one_or_none()
        if device:
            device.customer_id = customer_id
            device.rider_id = rider_id
            device.platform = platform
            device.device_model = device_model
            device.os_version = os_version
            device.app_version = app_version
            device.is_active = True
            device.last_seen_at = datetime.now(timezone.utc)
        else:
            device = MobileDevice(
                customer_id=customer_id,
                rider_id=rider_id,
                device_token=device_token,
                platform=platform,
                device_model=device_model,
                os_version=os_version,
                app_version=app_version,
                is_active=True,
                last_seen_at=datetime.now(timezone.utc),
            )
            self.db.add(device)
        await self.db.flush()
        return device

    async def unregister_device(self, device_token: str) -> None:
        await self.db.execute(
            update(MobileDevice)
            .where(MobileDevice.device_token == device_token)
            .values(is_active=False)
        )
        await self.db.flush()

    async def get_or_create_preferences(
        self, customer_id: int | None, rider_id: int | None, app_type: str
    ) -> AppPreference:
        if customer_id:
            result = await self.db.execute(
                select(AppPreference).where(
                    AppPreference.customer_id == customer_id,
                    AppPreference.app_type == app_type,
                )
            )
        else:
            result = await self.db.execute(
                select(AppPreference).where(
                    AppPreference.rider_id == rider_id,
                    AppPreference.app_type == app_type,
                )
            )
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = AppPreference(
                customer_id=customer_id,
                rider_id=rider_id,
                app_type=app_type,
            )
            self.db.add(prefs)
            await self.db.flush()
        return prefs

    async def update_preferences(
        self, prefs_id: int, updates: dict
    ) -> AppPreference | None:
        result = await self.db.execute(
            select(AppPreference).where(AppPreference.id == prefs_id)
        )
        prefs = result.scalar_one_or_none()
        if not prefs:
            return None
        for key, value in updates.items():
            if hasattr(prefs, key) and value is not None:
                setattr(prefs, key, value)
        await self.db.flush()
        return prefs

    async def create_session(
        self, customer_id: int | None, rider_id: int | None,
        device_id: int | None, session_token: str,
        refresh_token: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MobileSession:
        session = MobileSession(
            customer_id=customer_id,
            rider_id=rider_id,
            device_id=device_id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def end_session(self, session_token: str) -> None:
        await self.db.execute(
            update(MobileSession)
            .where(MobileSession.session_token == session_token)
            .values(is_active=False, ended_at=datetime.now(timezone.utc))
        )
        await self.db.flush()

    async def get_active_sessions(self, customer_id: int) -> list[MobileSession]:
        result = await self.db.execute(
            select(MobileSession).where(
                MobileSession.customer_id == customer_id,
                MobileSession.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_devices(self, customer_id: int) -> list[MobileDevice]:
        result = await self.db.execute(
            select(MobileDevice).where(
                MobileDevice.customer_id == customer_id,
                MobileDevice.is_active == True,
            )
        )
        return list(result.scalars().all())


class PushNotificationService:
    FCM_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_push(
        self, device_token: str, title: str, body: str,
        data: dict | None = None,
        notification_type: str = "general",
        customer_id: int | None = None,
        rider_id: int | None = None,
    ) -> PushNotificationModel:
        notification = PushNotificationModel(
            customer_id=customer_id,
            rider_id=rider_id,
            device_token=device_token,
            notification_type=notification_type,
            title=title,
            body=body,
            data=json.dumps(data) if data else None,
            sent_status="pending",
        )
        self.db.add(notification)
        await self.db.flush()

        try:
            success = await self._send_fcm(device_token, title, body, data)
            notification.sent_status = "sent" if success else "failed"
            notification.sent_at = datetime.now(timezone.utc)
            if not success:
                notification.error_message = "FCM delivery failed"
        except Exception as e:
            notification.sent_status = "failed"
            notification.error_message = str(e)
            logger.error(f"FCM send error: {e}")

        await self.db.flush()
        return notification

    async def _send_fcm(
        self, device_token: str, title: str, body: str, data: dict | None = None
    ) -> bool:
        if not settings.FCM_SERVER_KEY:
            logger.warning("FCM_SERVER_KEY not configured, skipping push")
            return False

        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
                "badge": "1",
            },
            "data": data or {},
            "priority": "high",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.FCM_URL,
                json=payload,
                headers={
                    "Authorization": f"key={settings.FCM_SERVER_KEY}",
                    "Content-Type": "application/json",
                },
            )
            result = response.json()
            return result.get("success", 0) == 1

    async def send_to_customer(
        self, customer_id: int, title: str, body: str,
        data: dict | None = None, notification_type: str = "general",
    ) -> list[PushNotificationModel]:
        result = await self.db.execute(
            select(MobileDevice).where(
                MobileDevice.customer_id == customer_id,
                MobileDevice.is_active == True,
            )
        )
        devices = result.scalars().all()
        notifications = []
        for device in devices:
            n = await self.send_push(
                device_token=device.device_token,
                title=title, body=body, data=data,
                notification_type=notification_type,
                customer_id=customer_id,
            )
            notifications.append(n)
        return notifications

    async def send_to_rider(
        self, rider_id: int, title: str, body: str,
        data: dict | None = None, notification_type: str = "rider",
    ) -> list[PushNotificationModel]:
        result = await self.db.execute(
            select(MobileDevice).where(
                MobileDevice.rider_id == rider_id,
                MobileDevice.is_active == True,
            )
        )
        devices = result.scalars().all()
        notifications = []
        for device in devices:
            n = await self.send_push(
                device_token=device.device_token,
                title=title, body=body, data=data,
                notification_type=notification_type,
                rider_id=rider_id,
            )
            notifications.append(n)
        return notifications

    async def send_to_branch_managers(
        self, branch_id: int, title: str, body: str,
        data: dict | None = None, notification_type: str = "manager",
    ) -> list[PushNotificationModel]:
        result = await self.db.execute(
            select(MobileDevice).where(
                MobileDevice.customer_id.isnot(None),
                MobileDevice.is_active == True,
            )
        )
        devices = result.scalars().all()
        manager_devices = []
        for device in devices:
            if device.customer_id:
                customer_result = await self.db.execute(
                    select(Customer).where(
                        Customer.id == device.customer_id,
                        Customer.role == "admin",
                    )
                )
                if customer_result.scalar_one_or_none():
                    manager_devices.append(device)

        notifications = []
        for device in manager_devices:
            n = await self.send_push(
                device_token=device.device_token,
                title=title, body=body, data=data,
                notification_type=notification_type,
            )
            notifications.append(n)
        return notifications

    async def get_notifications(
        self, customer_id: int | None = None, rider_id: int | None = None,
        page: int = 1, page_size: int = 20,
    ) -> tuple[list[PushNotificationModel], int]:
        query = select(PushNotificationModel)
        if customer_id:
            query = query.where(PushNotificationModel.customer_id == customer_id)
        if rider_id:
            query = query.where(PushNotificationModel.rider_id == rider_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(PushNotificationModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def mark_read(self, notification_id: int) -> PushNotificationModel | None:
        result = await self.db.execute(
            select(PushNotificationModel).where(PushNotificationModel.id == notification_id)
        )
        n = result.scalar_one_or_none()
        if n:
            n.read_at = datetime.now(timezone.utc)
            await self.db.flush()
        return n


class RiderTrackingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_location(
        self, rider_id: int, latitude: float, longitude: float,
        accuracy: float | None = None, speed: float | None = None,
        bearing: float | None = None, battery_level: float | None = None,
        delivery_id: int | None = None,
    ) -> RiderLocation:
        location = RiderLocation(
            rider_id=rider_id,
            latitude=latitude,
            longitude=longitude,
            accuracy=accuracy,
            speed=speed,
            bearing=bearing,
            battery_level=battery_level,
            is_active_delivery=delivery_id is not None,
            delivery_id=delivery_id,
        )
        self.db.add(location)
        await self.db.flush()

        await self.db.execute(
            update(Rider)
            .where(Rider.id == rider_id)
            .values(last_latitude=latitude, last_longitude=longitude)
        )
        await self.db.flush()
        return location

    async def get_latest_location(self, rider_id: int) -> RiderLocation | None:
        result = await self.db.execute(
            select(RiderLocation)
            .where(RiderLocation.rider_id == rider_id)
            .order_by(RiderLocation.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_active_rider_locations(self, branch_id: int | None = None) -> list[dict[str, Any]]:
        query = (
            select(
                RiderLocation.rider_id,
                RiderLocation.latitude,
                RiderLocation.longitude,
                RiderLocation.speed,
                RiderLocation.bearing,
                RiderLocation.battery_level,
                RiderLocation.recorded_at,
                RiderLocation.delivery_id,
                Rider.name,
                Rider.phone,
                Rider.vehicle_type,
            )
            .join(Rider, RiderLocation.rider_id == Rider.id)
            .where(
                RiderLocation.is_active_delivery == True,
                Rider.is_active == True,
            )
        )
        if branch_id:
            query = query.where(Rider.branch_id == branch_id)

        subquery = (
            select(
                RiderLocation.rider_id,
                func.max(RiderLocation.recorded_at).label("max_time"),
            )
            .group_by(RiderLocation.rider_id)
        ).subquery()

        query = query.join(
            subquery,
            (RiderLocation.rider_id == subquery.c.rider_id) &
            (RiderLocation.recorded_at == subquery.c.max_time),
        )

        result = await self.db.execute(query)
        return [
            {
                "rider_id": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "speed": row[3],
                "bearing": row[4],
                "battery_level": row[5],
                "last_updated": row[6].isoformat() if row[6] else None,
                "delivery_id": row[7],
                "rider_name": row[8],
                "rider_phone": row[9],
                "vehicle_type": row[10],
            }
            for row in result.all()
        ]

    async def get_rider_location_history(
        self, rider_id: int, limit: int = 100
    ) -> list[RiderLocation]:
        result = await self.db.execute(
            select(RiderLocation)
            .where(RiderLocation.rider_id == rider_id)
            .order_by(RiderLocation.recorded_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_nearest_riders(
        self, latitude: float, longitude: float,
        branch_id: int | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        locations = await self.get_active_rider_locations(branch_id)
        for loc in locations:
            loc["distance_km"] = self._haversine(
                latitude, longitude, loc["latitude"], loc["longitude"]
            )
        locations.sort(key=lambda x: x["distance_km"])
        return locations[:limit]

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        from math import asin, cos, radians, sin, sqrt
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return round(R * c, 2)


class DeliveryIncidentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_incident(
        self, delivery_id: int, rider_id: int, incident_type: str,
        description: str | None = None,
        evidence_photo_urls: list[str] | None = None,
    ) -> DeliveryIncident:
        incident = DeliveryIncident(
            delivery_id=delivery_id,
            rider_id=rider_id,
            incident_type=incident_type,
            description=description,
            evidence_photo_urls=json.dumps(evidence_photo_urls) if evidence_photo_urls else None,
            resolution_status="open",
        )
        self.db.add(incident)

        delivery_result = await self.db.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        delivery = delivery_result.scalar_one_or_none()
        if delivery:
            delivery.status = "failed"
            delivery.notes = f"Incident: {incident_type}. {description or ''}"

        await self.db.flush()
        return incident

    async def resolve_incident(
        self, incident_id: int, resolved_by: int,
        resolution_status: str, resolution_notes: str | None = None,
    ) -> DeliveryIncident | None:
        result = await self.db.execute(
            select(DeliveryIncident).where(DeliveryIncident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            return None
        incident.resolution_status = resolution_status
        incident.resolved_by = resolved_by
        incident.resolved_at = datetime.now(timezone.utc)
        incident.resolution_notes = resolution_notes
        await self.db.flush()
        return incident

    async def get_incidents(
        self, delivery_id: int | None = None, rider_id: int | None = None,
        status: str | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[list[DeliveryIncident], int]:
        query = select(DeliveryIncident)
        if delivery_id:
            query = query.where(DeliveryIncident.delivery_id == delivery_id)
        if rider_id:
            query = query.where(DeliveryIncident.rider_id == rider_id)
        if status:
            query = query.where(DeliveryIncident.resolution_status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(DeliveryIncident.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total


class DeliveryAgeVerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_age(
        self, order_id: int, rider_id: int, document_type: str, document_number: str,
    ) -> DeliveryAgeVerification:
        verification = DeliveryAgeVerification(
            order_id=order_id,
            rider_id=rider_id,
            document_type=document_type,
            document_number=document_number,
        )
        self.db.add(verification)

        order_result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if order:
            order.status = "age_verified"
            order.delivery_status = "age_verified"

        delivery_result = await self.db.execute(
            select(Delivery).where(Delivery.order_id == order_id)
        )
        delivery = delivery_result.scalar_one_or_none()
        if delivery:
            delivery.status = "age_verified"

        await self.db.flush()
        return verification

    async def get_verification(self, order_id: int) -> DeliveryAgeVerification | None:
        result = await self.db.execute(
            select(DeliveryAgeVerification).where(DeliveryAgeVerification.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_verifications(
        self, rider_id: int | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[list[DeliveryAgeVerification], int]:
        query = select(DeliveryAgeVerification)
        if rider_id:
            query = query.where(DeliveryAgeVerification.rider_id == rider_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(DeliveryAgeVerification.verification_timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total


class DeliveryPaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initiate_payment(
        self, order_id: int, rider_id: int, customer_phone: str, amount: float,
    ) -> DeliveryPayment:
        from app.services.payment_service import MpesaService

        payment = DeliveryPayment(
            order_id=order_id,
            rider_id=rider_id,
            customer_phone=customer_phone,
            amount=amount,
            status="pending",
        )
        self.db.add(payment)
        await self.db.flush()

        mpesa = MpesaService(self.db)
        try:
            result = await mpesa.stk_push(customer_phone, amount, order_id)
            payment.merchant_request_id = result.get("MerchantRequestID")
            payment.checkout_request_id = result.get("CheckoutRequestID")
            await self.db.flush()
        except Exception as e:
            payment.status = "failed"
            payment.result_desc = str(e)
            await self.db.flush()
            raise

        return payment

    async def handle_callback(self, callback_data: dict) -> None:
        from app.services.payment_service import MpesaService
        mpesa = MpesaService(self.db)
        await mpesa.handle_callback(callback_data)

        try:
            body = callback_data.get("Body", {})
            stk_callback = body.get("stkCallback", {})
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            result_code = stk_callback.get("ResultCode")

            if not checkout_request_id:
                return

            result = await self.db.execute(
                select(DeliveryPayment).where(
                    DeliveryPayment.checkout_request_id == checkout_request_id
                )
            )
            payment = result.scalar_one_or_none()
            if not payment:
                return

            if result_code == 0:
                callback_metadata = stk_callback.get("CallbackMetadata", {})
                items = callback_metadata.get("Item", [])
                for item in items:
                    if item.get("Name") == "MpesaReceiptNumber":
                        payment.mpesa_receipt = item.get("Value")

                payment.status = "completed"
                payment.payment_timestamp = datetime.now(timezone.utc)

                order_result = await self.db.execute(
                    select(Order).where(Order.id == payment.order_id)
                )
                order = order_result.scalar_one_or_none()
                if order:
                    order.payment_status = "paid"
                    order.status = "payment_successful"

                delivery_result = await self.db.execute(
                    select(Delivery).where(Delivery.order_id == payment.order_id)
                )
                delivery = delivery_result.scalar_one_or_none()
                if delivery:
                    delivery.status = "payment_successful"
            else:
                payment.status = "failed"
                payment.result_desc = stk_callback.get("ResultDesc")

            await self.db.flush()

        except Exception as e:
            logger.error(f"Error processing delivery payment callback: {e}")

    async def get_payment(self, order_id: int) -> DeliveryPayment | None:
        result = await self.db.execute(
            select(DeliveryPayment).where(DeliveryPayment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def retry_payment(self, payment_id: int) -> DeliveryPayment | None:
        result = await self.db.execute(
            select(DeliveryPayment).where(DeliveryPayment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment or payment.status == "completed":
            return None

        from app.services.payment_service import MpesaService
        mpesa = MpesaService(self.db)
        try:
            mpesa_result = await mpesa.stk_push(payment.customer_phone, payment.amount, payment.order_id)
            payment.merchant_request_id = mpesa_result.get("MerchantRequestID")
            payment.checkout_request_id = mpesa_result.get("CheckoutRequestID")
            payment.status = "pending"
            payment.result_desc = None
            await self.db.flush()
        except Exception as e:
            payment.status = "failed"
            payment.result_desc = str(e)
            await self.db.flush()
            raise

        return payment


class MobileDashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customer_profile(self, customer_id: int) -> dict:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return {}

        from app.services.loyalty_service import LoyaltyService
        loyalty = LoyaltyService(self.db)
        account = await loyalty.get_account(customer_id)

        legal_age = 18
        is_legal = False
        if customer.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - customer.date_of_birth.year - (
                (today.month, today.day) < (customer.date_of_birth.month, customer.date_of_birth.day)
            )
            is_legal = age >= legal_age

        return {
            "id": customer.id,
            "full_name": customer.full_name,
            "phone": customer.phone,
            "email": customer.email,
            "date_of_birth": customer.date_of_birth.isoformat() if customer.date_of_birth else None,
            "age_verified": customer.age_verified,
            "age_verification_status": customer.age_verification_status or "unverified",
            "verification_timestamp": customer.verification_timestamp.isoformat() if customer.verification_timestamp else None,
            "is_legal_age": is_legal,
            "loyalty_points": account.current_balance if account else 0,
            "loyalty_earned": account.points_earned if account else 0,
            "loyalty_redeemed": account.points_redeemed if account else 0,
        }

    async def get_rider_dashboard(self, rider_id: int) -> dict:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        assigned = await self.db.execute(
            select(func.count()).where(
                Delivery.rider_id == rider_id,
                Delivery.status.in_(["assigned", "accepted"]),
            )
        )

        pending = await self.db.execute(
            select(func.count()).where(
                Delivery.rider_id == rider_id,
                Delivery.status == "pending",
            )
        )

        completed_today = await self.db.execute(
            select(func.count()).where(
                Delivery.rider_id == rider_id,
                Delivery.status == "delivered",
                Delivery.delivered_at >= today_start,
            )
        )

        earned_today = await self.db.execute(
            select(func.coalesce(func.sum(Delivery.delivery_fee), 0)).where(
                Delivery.rider_id == rider_id,
                Delivery.status == "delivered",
                Delivery.delivered_at >= today_start,
            )
        )

        current = await self.db.execute(
            select(Delivery).where(
                Delivery.rider_id == rider_id,
                Delivery.status.in_(["assigned", "accepted", "picked_up", "en_route"]),
            ).order_by(Delivery.created_at.desc()).limit(1)
        )
        current_delivery = current.scalar_one_or_none()

        return {
            "assigned_deliveries": assigned.scalar() or 0,
            "pending_deliveries": pending.scalar() or 0,
            "completed_today": completed_today.scalar() or 0,
            "total_earned_today": float(earned_today.scalar() or 0),
            "current_delivery": {
                "id": current_delivery.id,
                "order_id": current_delivery.order_id,
                "address": current_delivery.address,
                "status": current_delivery.status,
                "delivery_fee": current_delivery.delivery_fee,
            } if current_delivery else None,
        }

    async def get_manager_dashboard(self, branch_id: int) -> dict:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        sales_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.branch_id == branch_id,
                Order.payment_status == "paid",
                Order.created_at >= today_start,
            )
        )

        orders_result = await self.db.execute(
            select(func.count()).where(
                Order.branch_id == branch_id,
                Order.created_at >= today_start,
            )
        )

        from app.models.customer import Product
        low_stock = await self.db.execute(
            select(func.count()).where(
                Product.stock_quantity <= Product.reorder_level,
                Product.branch_id == branch_id,
                Product.is_active == True,
            )
        )

        pending_deliveries = await self.db.execute(
            select(func.count()).where(
                Delivery.branch_id == branch_id,
                Delivery.status == "pending",
            )
        )

        active_riders = await self.db.execute(
            select(func.count()).where(
                Rider.branch_id == branch_id,
                Rider.is_active == True,
                Rider.status == "available",
            )
        )

        return {
            "today_sales": float(sales_result.scalar() or 0),
            "today_orders": int(orders_result.scalar() or 0),
            "low_stock_count": int(low_stock.scalar() or 0),
            "pending_deliveries": int(pending_deliveries.scalar() or 0),
            "active_riders": int(active_riders.scalar() or 0),
        }

    async def get_executive_dashboard(self) -> dict:
        from app.services.head_office.analytics_engine import AnalyticsEngine
        engine = AnalyticsEngine(self.db)

        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.grand_total), 0)).where(
                Order.payment_status == "paid"
            )
        )
        total_revenue = float(revenue_result.scalar() or 0)

        orders_result = await self.db.execute(select(func.count()).select_from(Order))
        total_orders = int(orders_result.scalar() or 0)

        customers_result = await self.db.execute(select(func.count()).select_from(Customer))
        customer_count = int(customers_result.scalar() or 0)

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "customer_count": customer_count,
        }
