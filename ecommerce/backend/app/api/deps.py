from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.customer import Customer

security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_authenticated_customer(
    token: str = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    customer = await get_current_user(token, db)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return customer


async def get_admin_user(
    current_user: Customer = Depends(get_authenticated_customer),
) -> Customer:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_rider_user(
    current_user: Customer = Depends(get_authenticated_customer),
) -> Customer:
    if current_user.role != "rider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rider privileges required",
        )
    return current_user
