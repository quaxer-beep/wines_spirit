import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import Supplier, SupplierRating
from app.schemas.head_office import SupplierCreate, SupplierUpdate, SupplierRatingCreate
from app.services.head_office.supplier_service import SupplierService


class TestSupplierService:
    async def test_create(self, db_session: AsyncSession):
        service = SupplierService(db_session)
        data = SupplierCreate(
            name="New Supplier",
            contact_person="Jane Doe",
            email="jane@new.com",
            phone="0798765432",
            physical_address="456 New Rd",
            tax_info="P059876543Z",
        )
        supplier = await service.create(data)
        await db_session.commit()

        assert supplier.id is not None
        assert supplier.name == "New Supplier"
        assert supplier.is_active is True

    async def test_get(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        supplier = await service.get(sample_supplier.id)
        assert supplier is not None
        assert supplier.id == sample_supplier.id
        assert supplier.name == "Test Supplier Ltd"

    async def test_get_not_found(self, db_session: AsyncSession):
        service = SupplierService(db_session)
        assert await service.get(999) is None

    async def test_update(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        data = SupplierUpdate(name="Updated Supplier")
        updated = await service.update(sample_supplier.id, data)
        await db_session.commit()

        assert updated is not None
        assert updated.name == "Updated Supplier"

    async def test_delete(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        result = await service.delete(sample_supplier.id)
        await db_session.commit()
        assert result is True

        assert await service.get(sample_supplier.id) is None

    async def test_list(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        items, total = await service.list(page=1, page_size=20)
        assert total >= 1
        assert any(s.id == sample_supplier.id for s in items)

    async def test_add_rating(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        data = SupplierRatingCreate(
            supplier_id=sample_supplier.id,
            delivery_accuracy=4.0,
            delivery_timeliness=5.0,
            product_quality=4.5,
            order_fulfillment_rate=4.0,
            notes="Good supplier",
        )
        rating = await service.add_rating(data)
        await db_session.commit()

        assert rating.id is not None
        assert rating.overall_score is not None
        assert 4.0 <= rating.overall_score <= 5.0

    async def test_get_performance(self, db_session: AsyncSession, sample_supplier: Supplier):
        service = SupplierService(db_session)
        perf = await service.get_performance(sample_supplier.id)
        assert perf is not None
        assert perf.supplier_id == sample_supplier.id
        assert perf.supplier_name == "Test Supplier Ltd"
