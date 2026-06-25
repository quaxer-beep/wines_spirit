from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.customer import (
    Customer,
    CustomerVerification,
    VerificationDocument,
)


class VerificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_verification(
        self,
        customer_id: int,
        date_of_birth: date,
        national_id: str,
    ) -> CustomerVerification:
        existing = await self.db.execute(
            select(CustomerVerification).where(
                CustomerVerification.customer_id == customer_id
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Verification already submitted")

        age = self._calculate_age(date_of_birth)
        if age < settings.LEGAL_DRINKING_AGE:
            raise ValueError(
                f"You must be at least {settings.LEGAL_DRINKING_AGE} years old"
            )

        verification = CustomerVerification(
            customer_id=customer_id,
            date_of_birth=date_of_birth,
            national_id=national_id,
            verification_status="pending",
        )
        self.db.add(verification)
        await self.db.flush()
        return verification

    async def add_document(
        self,
        verification_id: int,
        document_type: str,
        document_number: str,
        front_image_url: str | None = None,
        back_image_url: str | None = None,
        selfie_url: str | None = None,
    ) -> VerificationDocument:
        doc = VerificationDocument(
            verification_id=verification_id,
            document_type=document_type,
            document_number=document_number,
            front_image_url=front_image_url,
            back_image_url=back_image_url,
            selfie_url=selfie_url,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def approve_verification(
        self, customer_id: int, admin_id: int
    ) -> CustomerVerification:
        result = await self.db.execute(
            select(CustomerVerification).where(
                CustomerVerification.customer_id == customer_id
            )
        )
        verification = result.scalar_one_or_none()
        if not verification:
            raise ValueError("Verification not found")
        if verification.verification_status != "pending":
            raise ValueError(f"Verification already {verification.verification_status}")

        verification.verification_status = "approved"
        verification.verification_date = datetime.now(timezone.utc)
        verification.verified_by = admin_id

        customer_result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer:
            customer.age_verified = True
            customer.verification_date = datetime.now(timezone.utc)
            customer.date_of_birth = verification.date_of_birth
            customer.national_id = verification.national_id

        await self.db.flush()
        return verification

    async def reject_verification(
        self, customer_id: int, admin_id: int, reason: str
    ) -> CustomerVerification:
        result = await self.db.execute(
            select(CustomerVerification).where(
                CustomerVerification.customer_id == customer_id
            )
        )
        verification = result.scalar_one_or_none()
        if not verification:
            raise ValueError("Verification not found")

        verification.verification_status = "rejected"
        verification.rejection_reason = reason
        verification.verified_by = admin_id
        await self.db.flush()
        return verification

    async def get_verification(
        self, customer_id: int
    ) -> CustomerVerification | None:
        result = await self.db.execute(
            select(CustomerVerification)
            .where(CustomerVerification.customer_id == customer_id)
            .options(selectinload(CustomerVerification.documents))
        )
        return result.scalar_one_or_none()

    async def get_pending_verifications(
        self, page: int = 1, page_size: int = 20
    ) -> tuple[list[CustomerVerification], int]:
        from sqlalchemy import func

        query = (
            select(CustomerVerification)
            .where(CustomerVerification.verification_status == "pending")
            .order_by(CustomerVerification.created_at.asc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = (
            query.offset(offset)
            .limit(page_size)
            .options(selectinload(CustomerVerification.documents))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    def _calculate_age(self, birth_date: date) -> int:
        today = date.today()
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
