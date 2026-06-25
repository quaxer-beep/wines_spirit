import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.head_office import Alert
from app.services.head_office.alert_service import AlertService


class TestAlertService:
    async def test_create_alert(self, db_session: AsyncSession):
        service = AlertService(db_session)
        alert = await service.create_alert(
            alert_type="low_stock",
            severity="warning",
            title="Low Stock Alert",
            message="Product Test Wine is below reorder level",
            branch_id=1,
            resource_type="product",
            resource_id=1,
        )
        await db_session.commit()

        assert alert.id is not None
        assert alert.alert_type == "low_stock"
        assert alert.severity == "warning"
        assert not alert.is_read

    async def test_list_alerts(self, db_session: AsyncSession):
        service = AlertService(db_session)
        await service.create_alert("low_stock", "warning", "Test Alert", "Test message", branch_id=1)
        await db_session.flush()

        items, total = await service.list_alerts(page=1, page_size=20)
        assert total >= 1

    async def test_mark_read(self, db_session: AsyncSession):
        service = AlertService(db_session)
        alert = await service.create_alert("low_stock", "warning", "Test Alert", "Test", branch_id=1)
        await db_session.flush()

        updated = await service.mark_read(alert.id)
        await db_session.commit()
        assert updated is not None
        assert updated.is_read

    async def test_mark_resolved(self, db_session: AsyncSession):
        service = AlertService(db_session)
        alert = await service.create_alert("low_stock", "warning", "Test Alert", "Test", branch_id=1)
        await db_session.flush()

        updated = await service.mark_resolved(alert.id)
        await db_session.commit()
        assert updated is not None
        assert updated.is_resolved
        assert updated.resolved_at is not None
