import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.head_office.analytics_engine import AnalyticsEngine


class TestAnalyticsEngine:
    async def test_get_revenue_trends(self, db_session: AsyncSession, sample_order):
        engine = AnalyticsEngine(db_session)
        trends = await engine.get_revenue_trends(days=90)

        assert isinstance(trends, list)
        for t in trends:
            assert t.date is not None
            assert t.revenue >= 0


