import asyncio
from datetime import date, datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio

from app.core.database import Base
from app.models.customer import Customer, Order, OrderItem, Product
from app.models.head_office import Alert, PurchaseOrder, PurchaseOrderItem, StockTransfer, StockTransferItem, Supplier, SupplierRating


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_branch() -> int:
    return 1


@pytest_asyncio.fixture
async def sample_supplier(db_session: AsyncSession) -> Supplier:
    supplier = Supplier(
        name="Test Supplier Ltd",
        contact_person="John Doe",
        email="john@testsupplier.com",
        phone="0712345678",
        physical_address="123 Test St, Nairobi",
        tax_info="P051234567Z",
    )
    db_session.add(supplier)
    await db_session.flush()
    return supplier


@pytest_asyncio.fixture
async def sample_products(db_session: AsyncSession, sample_branch: int) -> list[Product]:
    products = [
        Product(
            name="Test Wine",
            brand="TestBrand",
            category="Wines",
            selling_price=1000.0,
            cost_price=600.0,
            unit="btl",
            reorder_level=10,
            is_active=True,
            is_alcoholic=True,
            requires_age_verification=True,
            stock_quantity=100,
            branch_id=sample_branch,
        ),
        Product(
            name="Test Whisky",
            brand="TestBrand",
            category="Spirits",
            selling_price=2500.0,
            cost_price=1500.0,
            unit="btl",
            reorder_level=5,
            is_active=True,
            is_alcoholic=True,
            requires_age_verification=True,
            stock_quantity=50,
            branch_id=sample_branch,
        ),
    ]
    db_session.add_all(products)
    await db_session.flush()
    return products


@pytest_asyncio.fixture
async def sample_customer(db_session: AsyncSession) -> Customer:
    customer = Customer(
        full_name="Test Customer",
        phone="0711111111",
        email="customer@test.com",
        password_hash="hashed",
        role="customer",
        date_of_birth=date(1990, 1, 1),
        national_id="12345678",
        age_verified=True,
        status="active",
    )
    db_session.add(customer)
    await db_session.flush()
    return customer


@pytest_asyncio.fixture
async def sample_order(db_session: AsyncSession, sample_customer: Customer, sample_products: list[Product], sample_branch: int) -> Order:
    order = Order(
        order_number="ORD-TEST-001",
        customer_id=sample_customer.id,
        branch_id=sample_branch,
        subtotal=3500.0,
        delivery_fee=200.0,
        grand_total=3700.0,
        status="delivered",
        payment_status="paid",
        delivery_status="delivered",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(order)
    await db_session.flush()

    items = [
        OrderItem(
            order_id=order.id,
            product_id=sample_products[0].id,
            product_name=sample_products[0].name,
            quantity=2,
            unit_price=sample_products[0].selling_price,
            subtotal=2000.0,
        ),
        OrderItem(
            order_id=order.id,
            product_id=sample_products[1].id,
            product_name=sample_products[1].name,
            quantity=1,
            unit_price=sample_products[1].selling_price,
            subtotal=2500.0,
        ),
    ]
    db_session.add_all(items)
    await db_session.flush()
    return order


_counter = 0


@pytest_asyncio.fixture
async def sample_purchase_order(db_session: AsyncSession, sample_supplier: Supplier, sample_branch: int, sample_products: list[Product]) -> PurchaseOrder:
    global _counter
    _counter += 1
    po = PurchaseOrder(
        po_number=f"PO-TEST-{_counter:04d}",
        supplier_id=sample_supplier.id,
        branch_id=sample_branch,
        ordered_by=1,
        status="draft",
        subtotal=13500.0,
        grand_total=13500.0,
        notes="Test PO",
    )
    db_session.add(po)
    await db_session.flush()

    items = [
        PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=sample_products[0].id,
            product_name=sample_products[0].name,
            quantity_ordered=10,
            unit_price=600.0,
            subtotal=6000.0,
        ),
        PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=sample_products[1].id,
            product_name=sample_products[1].name,
            quantity_ordered=5,
            unit_price=1500.0,
            subtotal=7500.0,
        ),
    ]
    db_session.add_all(items)
    await db_session.flush()
    return po


@pytest_asyncio.fixture
async def sample_transfer(db_session: AsyncSession, sample_branch: int, sample_products: list[Product]) -> StockTransfer:
    import time
    transfer = StockTransfer(
        transfer_number=f"TRF-TEST-{time.time_ns()}",
        from_branch_id=sample_branch,
        to_branch_id=2,
        requested_by=1,
        status="requested",
        notes="Test transfer",
    )
    db_session.add(transfer)
    await db_session.flush()

    items = [
        StockTransferItem(
            stock_transfer_id=transfer.id,
            product_id=sample_products[0].id,
            product_name=sample_products[0].name,
            quantity=10,
            unit_cost=sample_products[0].cost_price,
        ),
        StockTransferItem(
            stock_transfer_id=transfer.id,
            product_id=sample_products[1].id,
            product_name=sample_products[1].name,
            quantity=5,
            unit_cost=sample_products[1].cost_price,
        ),
    ]
    db_session.add_all(items)
    await db_session.flush()
    return transfer
