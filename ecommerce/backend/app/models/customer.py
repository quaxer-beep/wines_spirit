from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")
    date_of_birth: Mapped[date] = mapped_column(nullable=True)
    national_id: Mapped[str] = mapped_column(String(50), nullable=True)
    age_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    age_verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    verification_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    verification_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    registration_date: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    addresses = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    loyalty_account = relationship("LoyaltyAccount", back_populates="customer", uselist=False)
    verification = relationship("CustomerVerification", back_populates="customer", uselist=False)
    notifications = relationship("Notification", back_populates="customer")
    cart_items = relationship("CartItem", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_email", "email"),
        Index("idx_customers_status", "status"),
    )


class CustomerAddress(Base):
    __tablename__ = "customer_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    building_name: Mapped[str] = mapped_column(String(255), nullable=True)
    landmark: Mapped[str] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="addresses")

    __table_args__ = (
        Index("idx_addresses_customer", "customer_id"),
    )


class CustomerVerification(Base):
    __tablename__ = "customer_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    date_of_birth: Mapped[date] = mapped_column(nullable=False)
    national_id: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    verification_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    verified_by: Mapped[int] = mapped_column(Integer, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="verification")
    documents = relationship("VerificationDocument", back_populates="verification", cascade="all, delete-orphan")


class VerificationDocument(Base):
    __tablename__ = "verification_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer_verifications.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[str] = mapped_column(String(100), nullable=False)
    front_image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    back_image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    selfie_url: Mapped[str] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    verification = relationship("CustomerVerification", back_populates="documents")

    __table_args__ = (
        Index("idx_verification_docs_verification", "verification_id"),
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pos_product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    selling_price: Mapped[float] = mapped_column(Float, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit: Mapped[str] = mapped_column(String(50), default="pcs")
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_alcoholic: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_age_verification: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        Index("idx_products_name", "name"),
        Index("idx_products_category", "category"),
        Index("idx_products_brand", "brand"),
        Index("idx_products_pos_id", "pos_product_id"),
    )


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    product = relationship("Product", back_populates="images")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

    __table_args__ = (
        Index("idx_cart_customer", "customer_id"),
        Index("idx_cart_product", "product_id"),
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    address_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer_addresses.id", ondelete="RESTRICT"), nullable=True
    )
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    delivery_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    loyalty_used: Mapped[int] = mapped_column(Integer, nullable=True)
    tax: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grand_total: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    delivery_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    age_verified_at_checkout: Mapped[bool] = mapped_column(Boolean, default=False)
    age_consent_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    age_consent_ip: Mapped[str] = mapped_column(String(50), nullable=True)
    age_consent_device: Mapped[str] = mapped_column(String(500), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    pos_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="orders")
    address = relationship("CustomerAddress")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="order", uselist=False)

    __table_args__ = (
        Index("idx_orders_customer", "customer_id"),
        Index("idx_orders_branch", "branch_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_number", "order_number"),
        Index("idx_orders_created", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="MPESA")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant_request_id: Mapped[str] = mapped_column(String(100), nullable=True)
    checkout_request_id: Mapped[str] = mapped_column(String(100), nullable=True)
    receipt_number: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_desc: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order", back_populates="payments")

    __table_args__ = (
        Index("idx_payments_order", "order_id"),
        Index("idx_payments_checkout", "checkout_request_id"),
    )


class DeliveryFee(Base):
    __tablename__ = "delivery_fees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    base_fee: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    per_km_rate: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    fuel_adjustment_pct: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    min_distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_distance_km: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    plate_number: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    last_latitude: Mapped[float] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    deliveries = relationship("Delivery", back_populates="rider")

    __table_args__ = (
        Index("idx_riders_phone", "phone"),
        Index("idx_riders_status", "status"),
        Index("idx_riders_branch", "branch_id"),
    )


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    rider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    delivery_fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    picked_up_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order", back_populates="delivery")
    rider = relationship("Rider", back_populates="deliveries")

    __table_args__ = (
        Index("idx_deliveries_order", "order_id"),
        Index("idx_deliveries_rider", "rider_id"),
        Index("idx_deliveries_status", "status"),
    )


class DeliveryAgeVerification(Base):
    __tablename__ = "delivery_age_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    rider_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[str] = mapped_column(String(100), nullable=False)
    verification_timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    order = relationship("Order", backref="delivery_age_verification", uselist=False)
    rider = relationship("Rider")

    __table_args__ = (
        Index("idx_delivery_age_ver_order", "order_id"),
        Index("idx_delivery_age_ver_rider", "rider_id"),
    )


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_redeemed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_expired: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    customer = relationship("Customer", back_populates="loyalty_account")
    transactions = relationship("LoyaltyTransaction", back_populates="account", cascade="all, delete-orphan")


class LoyaltyTransaction(Base):
    __tablename__ = "loyalty_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    expiry_date: Mapped[date] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    account = relationship("LoyaltyAccount", back_populates="transactions")

    __table_args__ = (
        Index("idx_loyalty_tx_account", "account_id"),
        Index("idx_loyalty_tx_type", "transaction_type"),
    )


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    promotion_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    discount_type: Mapped[str] = mapped_column(String(20), nullable=True)
    discount_value: Mapped[float] = mapped_column(Float, nullable=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=True)
    free_product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    min_order_amount: Mapped[float] = mapped_column(Float, nullable=True)
    max_discount: Mapped[float] = mapped_column(Float, nullable=True)
    loyalty_multiplier: Mapped[float] = mapped_column(Float, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_promotions_type", "promotion_type"),
        Index("idx_promotions_active", "is_active"),
        Index("idx_promotions_dates", "start_date", "end_date"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="in_app")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_customer", "customer_id"),
        Index("idx_notifications_type", "notification_type"),
        Index("idx_notifications_read", "is_read"),
    )


class ProductSyncLog(Base):
    __tablename__ = "product_sync_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    products_synced: Mapped[int] = mapped_column(Integer, default=0)
    products_added: Mapped[int] = mapped_column(Integer, default=0)
    products_updated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class ComplianceIncident(Base):
    __tablename__ = "compliance_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    rider_id: Mapped[int] = mapped_column(Integer, nullable=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rider_notes: Mapped[str] = mapped_column(Text, nullable=True)
    resolution_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )
    resolved_by: Mapped[int] = mapped_column(Integer, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_incidents_type", "incident_type"),
        Index("idx_incidents_status", "resolution_status"),
    )


class ComplianceAuditLog(Base):
    __tablename__ = "compliance_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )

    __table_args__ = (
        Index("idx_audit_customer", "customer_id"),
        Index("idx_audit_event", "event_type"),
    )


class WebsiteSession(Base):
    __tablename__ = "website_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=True)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_sessions_session", "session_id"),
        Index("idx_sessions_customer", "customer_id"),
    )
