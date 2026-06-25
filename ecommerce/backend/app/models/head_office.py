from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    physical_address: Mapped[str] = mapped_column(Text, nullable=True)
    tax_info: Mapped[str] = mapped_column(String(255), nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    goods_received = relationship("GoodsReceivedNote", back_populates="supplier")
    ratings = relationship("SupplierRating", back_populates="supplier", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_suppliers_name", "name"),
        Index("idx_suppliers_phone", "phone"),
        Index("idx_suppliers_active", "is_active"),
    )


class SupplierRating(Base):
    __tablename__ = "supplier_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False
    )
    delivery_accuracy: Mapped[float] = mapped_column(Float, nullable=True)
    delivery_timeliness: Mapped[float] = mapped_column(Float, nullable=True)
    product_quality: Mapped[float] = mapped_column(Float, nullable=True)
    order_fulfillment_rate: Mapped[float] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    rated_by: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    supplier = relationship("Supplier", back_populates="ratings")

    __table_args__ = (
        Index("idx_supplier_ratings_supplier", "supplier_id"),
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    ordered_by: Mapped[int] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft"
    )
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grand_total: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    expected_delivery_date: Mapped[date] = mapped_column(nullable=True)
    actual_delivery_date: Mapped[date] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_received = relationship("GoodsReceivedNote", back_populates="purchase_order")

    __table_args__ = (
        Index("idx_po_number", "po_number"),
        Index("idx_po_supplier", "supplier_id"),
        Index("idx_po_status", "status"),
        Index("idx_po_branch", "branch_id"),
        Index("idx_po_created", "created_at"),
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_received: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    purchase_order = relationship("PurchaseOrder", back_populates="items")

    __table_args__ = (
        Index("idx_poi_order", "purchase_order_id"),
        Index("idx_poi_product", "product_id"),
    )


class GoodsReceivedNote(Base):
    __tablename__ = "goods_received_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grn_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    received_by: Mapped[int] = mapped_column(Integer, nullable=True)
    delivery_note_number: Mapped[str] = mapped_column(String(100), nullable=True)
    invoice_reference: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    purchase_order = relationship("PurchaseOrder", back_populates="goods_received")
    supplier = relationship("Supplier", back_populates="goods_received")
    items = relationship("GoodsReceivedItem", back_populates="grn", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_grn_number", "grn_number"),
        Index("idx_grn_po", "purchase_order_id"),
        Index("idx_grn_supplier", "supplier_id"),
        Index("idx_grn_branch", "branch_id"),
    )


class GoodsReceivedItem(Base):
    __tablename__ = "goods_received_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grn_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("goods_received_notes.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    grn = relationship("GoodsReceivedNote", back_populates="items")


class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    from_branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    to_branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by: Mapped[int] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[int] = mapped_column(Integer, nullable=True)
    dispatched_by: Mapped[int] = mapped_column(Integer, nullable=True)
    received_by: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="requested"
    )
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    items = relationship("StockTransferItem", back_populates="transfer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_st_transfer_number", "transfer_number"),
        Index("idx_st_from_branch", "from_branch_id"),
        Index("idx_st_to_branch", "to_branch_id"),
        Index("idx_st_status", "status"),
        Index("idx_st_requested", "requested_at"),
    )


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_transfer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    transfer = relationship("StockTransfer", back_populates="items")

    __table_args__ = (
        Index("idx_sti_transfer", "stock_transfer_id"),
        Index("idx_sti_product", "product_id"),
    )


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[date] = mapped_column(nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    total_sales: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_expenses: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    net_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    inventory_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    customer_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("snapshot_date", "branch_id", name="uq_snapshot_date_branch"),
        Index("idx_snapshots_date", "snapshot_date"),
        Index("idx_snapshots_branch", "branch_id"),
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_date: Mapped[date] = mapped_column(nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=True)
    forecast_type: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_lower: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float] = mapped_column(Float, nullable=True)
    actual_value: Mapped[float] = mapped_column(Float, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_forecasts_date", "forecast_date"),
        Index("idx_forecasts_branch", "branch_id"),
        Index("idx_forecasts_product", "product_id"),
        Index("idx_forecasts_type", "forecast_type"),
    )


class ExecutiveReport(Base):
    __tablename__ = "executive_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[date] = mapped_column(nullable=False)
    period_end: Mapped[date] = mapped_column(nullable=False)
    total_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    net_profit: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    operating_expenses: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    inventory_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    customer_growth: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    online_sales_growth: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    report_data: Mapped[str] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_exec_reports_type", "report_type"),
        Index("idx_exec_reports_period", "period_start", "period_end"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    changes: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_audit_events_type", "event_type"),
        Index("idx_audit_events_resource", "resource_type", "resource_id"),
        Index("idx_audit_events_user", "user_id"),
        Index("idx_audit_events_branch", "branch_id"),
        Index("idx_audit_events_created", "created_at"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_alerts_type", "alert_type"),
        Index("idx_alerts_branch", "branch_id"),
        Index("idx_alerts_severity", "severity"),
        Index("idx_alerts_created", "created_at"),
        Index("idx_alerts_read", "is_read"),
    )
