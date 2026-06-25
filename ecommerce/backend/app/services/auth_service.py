from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.customer import Customer
from app.schemas.auth import RegisterRequest, LoginRequest


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> Customer:
        existing = await self.db.execute(
            select(Customer).where(Customer.phone == data.phone)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Phone number already registered")

        if data.email:
            existing_email = await self.db.execute(
                select(Customer).where(Customer.email == data.email)
            )
            if existing_email.scalar_one_or_none():
                raise ValueError("Email already registered")

        customer = Customer(
            full_name=data.full_name,
            phone=data.phone,
            email=data.email,
            password_hash=hash_password(data.password),
            date_of_birth=data.date_of_birth,
            national_id=data.national_id,
            registration_date=datetime.now(timezone.utc),
        )
        self.db.add(customer)
        await self.db.flush()
        return customer

    async def authenticate(self, data: LoginRequest) -> Customer:
        result = await self.db.execute(
            select(Customer).where(Customer.phone == data.phone)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError("Invalid phone or password")
        if customer.status != "active":
            raise ValueError("Account is inactive or suspended")
        if not verify_password(data.password, customer.password_hash):
            raise ValueError("Invalid phone or password")

        customer.last_login = datetime.now(timezone.utc)
        await self.db.flush()
        return customer

    def generate_tokens(self, customer: Customer) -> dict:
        access_token = create_access_token(
            subject=str(customer.id),
            extra_claims={
                "role": customer.role,
                "phone": customer.phone,
            },
        )
        refresh_token = create_refresh_token(subject=str(customer.id))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid or expired refresh token")

        customer_id = int(payload["sub"])
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer or customer.status != "active":
            raise ValueError("Customer not found or inactive")

        return self.generate_tokens(customer)

    async def change_password(
        self, customer_id: int, current_password: str, new_password: str
    ) -> None:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError("Customer not found")
        if not verify_password(current_password, customer.password_hash):
            raise ValueError("Current password is incorrect")

        customer.password_hash = hash_password(new_password)
        await self.db.flush()
