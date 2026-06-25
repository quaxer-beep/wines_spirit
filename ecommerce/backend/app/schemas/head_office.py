from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    physical_address: Optional[str] = None
    tax_info: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    physical_address: Optional[str] = None
    tax_info: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: int
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    physical_address: Optional[str] = None
    tax_info: Optional[str] = None
    rating: float = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupplierRatingCreate(BaseModel):
    supplier_id: int
    delivery_accuracy: Optional[float] = None
    delivery_timeliness: Optional[float] = None
    product_quality: Optional[float] = None
    order_fulfillment_rate: Optional[float] = None
    notes: Optional[str] = None


class SupplierRatingResponse(BaseModel):
    id: int
    supplier_id: int
    delivery_accuracy: Optional[float] = None
    delivery_timeliness: Optional[float] = None
    product_quality: Optional[float] = None
    order_fulfillment_rate: Optional[float] = None
    overall_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderItemCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity_ordered: float
    unit_price: float


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    branch_id: Optional[int] = None
    notes: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    items: list[PurchaseOrderItemCreate]


class PurchaseOrderItemResponse(BaseModel):
    id: int
    purchase_order_id: int
    product_id: Optional[int] = None
    product_name: str
    quantity_ordered: float
    quantity_received: float = 0
    unit_price: float
    subtotal: float

    model_config = {"from_attributes": True}


class PurchaseOrderResponse(BaseModel):
    id: int
    po_number: str
    supplier_id: int
    branch_id: Optional[int] = None
    ordered_by: Optional[int] = None
    approved_by: Optional[int] = None
    status: str = "draft"
    subtotal: float = 0
    tax: float = 0
    grand_total: float = 0
    notes: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    items: list[PurchaseOrderItemResponse] = []
    supplier_name: Optional[str] = None

    model_config = {"from_attributes": True}


class GoodsReceivedItemCreate(BaseModel):
    product_id: Optional[int] = None
    product_name: str
    quantity_received: float
    unit_cost: float


class GoodsReceivedNoteCreate(BaseModel):
    purchase_order_id: int
    supplier_id: int
    branch_id: Optional[int] = None
    delivery_note_number: Optional[str] = None
    invoice_reference: Optional[str] = None
    notes: Optional[str] = None
    items: list[GoodsReceivedItemCreate]


class GoodsReceivedItemResponse(BaseModel):
    id: int
    grn_id: int
    product_id: Optional[int] = None
    product_name: str
    quantity_received: float
    unit_cost: float
    total_cost: float

    model_config = {"from_attributes": True}


class GoodsReceivedNoteResponse(BaseModel):
    id: int
    grn_number: str
    purchase_order_id: int
    supplier_id: int
    branch_id: Optional[int] = None
    received_by: Optional[int] = None
    delivery_note_number: Optional[str] = None
    invoice_reference: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None
    received_at: datetime
    created_at: datetime
    items: list[GoodsReceivedItemResponse] = []
    supplier_name: Optional[str] = None
    po_number: Optional[str] = None

    model_config = {"from_attributes": True}


class StockTransferItemCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_cost: Optional[float] = None


class StockTransferCreate(BaseModel):
    from_branch_id: int
    to_branch_id: int
    notes: Optional[str] = None
    items: list[StockTransferItemCreate]


class StockTransferItemResponse(BaseModel):
    id: int
    stock_transfer_id: int
    product_id: int
    product_name: str
    quantity: float
    unit_cost: Optional[float] = None

    model_config = {"from_attributes": True}


class StockTransferResponse(BaseModel):
    id: int
    transfer_number: str
    from_branch_id: int
    to_branch_id: int
    requested_by: Optional[int] = None
    approved_by: Optional[int] = None
    dispatched_by: Optional[int] = None
    received_by: Optional[int] = None
    status: str = "requested"
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    dispatched_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    items: list[StockTransferItemResponse] = []

    model_config = {"from_attributes": True}


class BranchSummary(BaseModel):
    branch_id: int
    branch_name: str
    branch_code: str
    total_sales: float = 0
    total_orders: int = 0
    inventory_value: float = 0
    gross_profit: float = 0
    total_expenses: float = 0
    net_profit: float = 0
    profit_margin_pct: float = 0


class HeadOfficeDashboard(BaseModel):
    total_sales_today: float = 0
    total_sales_week: float = 0
    total_sales_month: float = 0
    total_sales_year: float = 0
    total_orders_today: int = 0
    total_orders_week: int = 0
    revenue_by_branch: list[dict] = []
    revenue_by_category: list[dict] = []
    revenue_by_brand: list[dict] = []
    revenue_by_payment_method: list[dict] = []
    branch_count: int = 0
    active_alerts: int = 0


class RevenueTrend(BaseModel):
    date: str
    revenue: float = 0
    orders: int = 0
    profit: float = 0


class ProductPerformance(BaseModel):
    product_id: int
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    times_sold: int = 0
    total_quantity: float = 0
    total_revenue: float = 0
    gross_profit: float = 0
    profit_margin_pct: float = 0


class BrandPerformance(BaseModel):
    brand: str
    total_revenue: float = 0
    total_cost: float = 0
    gross_profit: float = 0
    profit_margin_pct: float = 0
    units_sold: float = 0


class SupplierPerformance(BaseModel):
    supplier_id: int
    supplier_name: str
    total_orders: int = 0
    total_value: float = 0
    avg_delivery_delay_days: float = 0
    order_fulfillment_rate: float = 0
    overall_rating: float = 0


class ExecutiveKPI(BaseModel):
    total_revenue: float = 0
    gross_profit: float = 0
    net_profit: float = 0
    operating_expenses: float = 0
    inventory_value: float = 0
    customer_count: int = 0
    customer_growth_pct: float = 0
    online_sales: float = 0
    online_sales_growth_pct: float = 0
    average_order_value: float = 0
    profit_margin_pct: float = 0


class AlertResponse(BaseModel):
    id: int
    branch_id: Optional[int] = None
    alert_type: str
    severity: str = "info"
    title: str
    message: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    is_read: bool = False
    is_resolved: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    branch_id: Optional[int] = None
    event_type: str
    resource_type: str
    resource_id: Optional[int] = None
    description: str
    changes: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
