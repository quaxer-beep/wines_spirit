from datetime import datetime

from sqlalchemy import (

    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# LOOKUP / REFERENCE
# ---------------------------------------------------------------------------

class Branch(TimestampMixin, Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    location = Column(String)
    phone = Column(String)
    email = Column(String)
    tax_reg_no = Column(String)
    is_active = Column(Integer, nullable=False, default=1)

    users = relationship("User", back_populates="branch")
    inventory = relationship("Inventory", back_populates="branch")
    stock_movements = relationship("StockMovement", back_populates="branch")
    sales = relationship("Sale", back_populates="branch")
    expenses = relationship("Expense", back_populates="branch")
    audit_logs = relationship("AuditLog", back_populates="branch")
    sync_queue = relationship("SyncQueue", back_populates="branch")

    __table_args__ = (
        Index("idx_branches_code", "code"),
        Index("idx_branches_is_active", "is_active"),
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource = Column(String, nullable=False)
    can_create = Column(Integer, nullable=False, default=0)
    can_read = Column(Integer, nullable=False, default=0)
    can_update = Column(Integer, nullable=False, default=0)
    can_delete = Column(Integer, nullable=False, default=0)

    role = relationship("Role", back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "resource", name="uq_permissions_role_resource"),
        Index("idx_permissions_role_id", "role_id"),
        Index("idx_permissions_resource", "resource"),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    is_active = Column(Integer, nullable=False, default=1)
    last_login = Column(DateTime)

    branch = relationship("Branch", back_populates="users")
    role = relationship("Role", back_populates="users")
    sales = relationship("Sale", back_populates="user")
    stock_movements = relationship("StockMovement", back_populates="created_by_user")
    expenses = relationship("Expense", back_populates="recorded_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        Index("idx_users_branch_id", "branch_id"),
        Index("idx_users_role_id", "role_id"),
        Index("idx_users_username", "username"),
        Index("idx_users_is_active", "is_active"),
    )


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    products = relationship("Product", back_populates="category")

    __table_args__ = (
        Index("idx_categories_name", "name"),
    )


# ---------------------------------------------------------------------------
# PRODUCT & INVENTORY
# ---------------------------------------------------------------------------

class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String, unique=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    cost_price = Column(Float, nullable=False, default=0)
    selling_price = Column(Float, nullable=False, default=0)
    unit = Column(String, nullable=False, default="pcs")
    reorder_level = Column(Float, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")

    __table_args__ = (
        Index("idx_products_barcode", "barcode"),
        Index("idx_products_category_id", "category_id"),
        Index("idx_products_name", "name"),
        Index("idx_products_is_active", "is_active"),
    )

    @validates("cost_price", "selling_price")
    def validate_non_negative(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


class Inventory(TimestampMixin, Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    quantity_on_hand = Column(Float, nullable=False, default=0)
    last_count_date = Column(DateTime)

    product = relationship("Product", back_populates="inventory")
    branch = relationship("Branch", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint("product_id", "branch_id", name="uq_inventory_product_branch"),
        Index("idx_inventory_product_id", "product_id"),
        Index("idx_inventory_branch_id", "branch_id"),
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    reference_type = Column(String)
    reference_id = Column(Integer)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    product = relationship("Product", back_populates="stock_movements")
    branch = relationship("Branch", back_populates="stock_movements")
    created_by_user = relationship("User", back_populates="stock_movements")

    __table_args__ = (
        CheckConstraint("movement_type IN ('IN', 'OUT', 'ADJUSTMENT', 'TRANSFER')", name="ck_stock_movement_type"),
        Index("idx_stock_movements_product_id", "product_id"),
        Index("idx_stock_movements_branch_id", "branch_id"),
        Index("idx_stock_movements_type", "movement_type"),
        Index("idx_stock_movements_created", "created_at"),
    )

    @validates("movement_type")
    def validate_movement_type(self, key, value):
        allowed = {"IN", "OUT", "ADJUSTMENT", "TRANSFER"}
        if value not in allowed:
            raise ValueError(f"movement_type must be one of {allowed}")
        return value

    @validates("quantity")
    def validate_quantity(self, key, value):
        if value is None:
            raise ValueError("quantity is required")
        return value


# ---------------------------------------------------------------------------
# SALES & PAYMENTS
# ---------------------------------------------------------------------------

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_number = Column(String, nullable=False, unique=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    subtotal = Column(Float, nullable=False, default=0)
    discount = Column(Float, nullable=False, default=0)
    tax = Column(Float, nullable=False, default=0)
    grand_total = Column(Float, nullable=False, default=0)
    payment_method = Column(String)
    status = Column(String, nullable=False, default="PENDING")
    voided = Column(Integer, nullable=False, default=0)
    void_reason = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    branch = relationship("Branch", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")
    etims_invoice = relationship("EtimsInvoice", back_populates="sale", uselist=False)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'COMPLETED', 'REFUNDED', 'CANCELLED')", name="ck_sale_status"),
        Index("idx_sales_receipt_number", "receipt_number"),
        Index("idx_sales_branch_id", "branch_id"),
        Index("idx_sales_user_id", "user_id"),
        Index("idx_sales_status", "status"),
        Index("idx_sales_created_at", "created_at"),
    )

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"PENDING", "COMPLETED", "REFUNDED", "CANCELLED"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return value

    @validates("subtotal", "discount", "tax", "grand_total")
    def validate_non_negative_sale(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    __table_args__ = (
        Index("idx_sale_items_sale_id", "sale_id"),
        Index("idx_sale_items_product_id", "product_id"),
    )

    @validates("quantity", "unit_price", "subtotal")
    def validate_non_negative_item(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    method = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String)
    mpesa_code = Column(String)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    sale = relationship("Sale", back_populates="payments")

    __table_args__ = (
        CheckConstraint("method IN ('CASH', 'MPESA', 'CARD', 'BANK_TRANSFER', 'CREDIT')", name="ck_payment_method"),
        CheckConstraint("status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')", name="ck_payment_status"),
        Index("idx_payments_sale_id", "sale_id"),
        Index("idx_payments_method", "method"),
        Index("idx_payments_status", "status"),
    )

    @validates("method")
    def validate_method(self, key, value):
        allowed = {"CASH", "MPESA", "CARD", "BANK_TRANSFER", "CREDIT"}
        if value not in allowed:
            raise ValueError(f"method must be one of {allowed}")
        return value

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"PENDING", "COMPLETED", "FAILED", "REFUNDED"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return value


# ---------------------------------------------------------------------------
# MPESA & EXPENSES
# ---------------------------------------------------------------------------

class MpesaTransaction(TimestampMixin, Base):
    __tablename__ = "mpesa_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checkout_request_id = Column(String)
    merchant_request_id = Column(String)
    transaction_code = Column(String, unique=True)
    amount = Column(Float, nullable=False)
    phone_number = Column(String)
    status = Column(String, nullable=False, default="PENDING")
    result_desc = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'SUCCESS', 'FAILED', 'CANCELLED')", name="ck_mpesa_status"),
        Index("idx_mpesa_checkout_request_id", "checkout_request_id"),
        Index("idx_mpesa_transaction_code", "transaction_code"),
        Index("idx_mpesa_status", "status"),
    )

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"PENDING", "SUCCESS", "FAILED", "CANCELLED"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return value


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    expense_date = Column(DateTime, nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    branch = relationship("Branch", back_populates="expenses")
    recorded_by_user = relationship("User", back_populates="expenses")

    __table_args__ = (
        Index("idx_expenses_branch_id", "branch_id"),
        Index("idx_expenses_category", "category"),
        Index("idx_expenses_date", "expense_date"),
    )

    @validates("amount")
    def validate_non_negative(self, key, value):
        if value is not None and value < 0:
            raise ValueError("amount must be non-negative")
        return value


# ---------------------------------------------------------------------------
# SYSTEM
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")
    branch = relationship("Branch", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_branch_id", "branch_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource"),
        Index("idx_audit_logs_created", "created_at"),
    )


class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=True)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    payload = Column(Text)
    status = Column(String, nullable=False, default="PENDING")
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    synced_at = Column(DateTime)

    branch = relationship("Branch", back_populates="sync_queue")

    __table_args__ = (
        CheckConstraint("action IN ('CREATE', 'UPDATE', 'DELETE')", name="ck_sync_action"),
        CheckConstraint("status IN ('PENDING', 'SYNCED', 'FAILED')", name="ck_sync_status"),
        Index("idx_sync_queue_branch_id", "branch_id"),
        Index("idx_sync_queue_status", "status"),
        Index("idx_sync_queue_table_name", "table_name"),
    )

    @validates("action")
    def validate_action(self, key, value):
        allowed = {"CREATE", "UPDATE", "DELETE"}
        if value not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return value

    @validates("status")
    def validate_status(self, key, value):
        allowed = {"PENDING", "SYNCED", "FAILED"}
        if value not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return value


class EtimsInvoice(Base):
    __tablename__ = "etims_invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, unique=True)
    invoice_number = Column(String, unique=True)
    control_number = Column(String)
    qr_code = Column(Text)
    submission_status = Column(String, nullable=False, default="PENDING")
    submission_response = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now())
    submitted_at = Column(DateTime)

    sale = relationship("Sale", back_populates="etims_invoice")

    __table_args__ = (
        CheckConstraint(
            "submission_status IN ('PENDING', 'SUBMITTED', 'FAILED', 'CANCELLED')",
            name="ck_etims_submission_status",
        ),
        Index("idx_etims_sale_id", "sale_id"),
        Index("idx_etims_invoice_number", "invoice_number"),
        Index("idx_etims_submission_status", "submission_status"),
    )

    @validates("submission_status")
    def validate_submission_status(self, key, value):
        allowed = {"PENDING", "SUBMITTED", "FAILED", "CANCELLED"}
        if value not in allowed:
            raise ValueError(f"submission_status must be one of {allowed}")
        return value


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, nullable=False, default=func.now(), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_config_key", "key"),
    )
