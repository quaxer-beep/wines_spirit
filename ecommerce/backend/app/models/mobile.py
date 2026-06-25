from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MobileDevice(Base):
    __tablename__ = "mobile_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    device_token: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    device_model: Mapped[str] = mapped_column(String(255), nullable=True)
    os_version: Mapped[str] = mapped_column(String(50), nullable=True)
    app_version: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", backref="mobile_devices")

    __table_args__ = (
        Index("idx_mobile_devices_token", "device_token"),
        Index("idx_mobile_devices_platform", "platform"),
    )


class PushNotification(Base):
    __tablename__ = "push_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    device_token: Mapped[str] = mapped_column(String(500), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=True)
    sent_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_push_notifications_customer", "customer_id"),
        Index("idx_push_notifications_type", "notification_type"),
        Index("idx_push_notifications_status", "sent_status"),
    )


class RiderLocation(Base):
    __tablename__ = "rider_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, nullable=True)
    speed: Mapped[float] = mapped_column(Float, nullable=True)
    bearing: Mapped[float] = mapped_column(Float, nullable=True)
    battery_level: Mapped[float] = mapped_column(Float, nullable=True)
    is_active_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deliveries.id", ondelete="SET NULL"), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    rider = relationship("Rider")

    __table_args__ = (
        Index("idx_rider_locations_rider", "rider_id"),
        Index("idx_rider_locations_time", "recorded_at"),
        Index("idx_rider_locations_active", "is_active_delivery"),
    )


class DeliveryIncident(Base):
    __tablename__ = "delivery_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    customer_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    branch_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_photo_urls: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    resolved_by: Mapped[int] = mapped_column(Integer, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    delivery = relationship("Delivery")

    __table_args__ = (
        Index("idx_delivery_incidents_delivery", "delivery_id"),
        Index("idx_delivery_incidents_type", "incident_type"),
        Index("idx_delivery_incidents_status", "resolution_status"),
    )


class MobileSession(Base):
    __tablename__ = "mobile_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    device_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mobile_devices.id", ondelete="SET NULL"), nullable=True
    )
    session_token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    refresh_token: Mapped[str] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    device = relationship("MobileDevice")

    __table_args__ = (
        Index("idx_mobile_sessions_customer", "customer_id"),
        Index("idx_mobile_sessions_token", "session_token"),
        Index("idx_mobile_sessions_active", "is_active"),
    )


class AppPreference(Base):
    __tablename__ = "app_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    app_type: Mapped[str] = mapped_column(String(20), nullable=False)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="light")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    location_tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    biometric_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_app_prefs_customer", "customer_id"),
        Index("idx_app_prefs_rider", "rider_id"),
        Index("idx_app_prefs_app", "app_type"),
    )


class DeliveryPayment(Base):
    __tablename__ = "delivery_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    mpesa_receipt: Mapped[str] = mapped_column(String(100), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant_request_id: Mapped[str] = mapped_column(String(100), nullable=True)
    checkout_request_id: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_desc: Mapped[str] = mapped_column(Text, nullable=True)
    payment_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order")
    rider = relationship("Rider")

    __table_args__ = (
        Index("idx_delivery_payments_order", "order_id"),
        Index("idx_delivery_payments_rider", "rider_id"),
        Index("idx_delivery_payments_checkout", "checkout_request_id"),
        Index("idx_delivery_payments_status", "status"),
    )
