from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.customer import (
    Customer,
    LoyaltyAccount,
    LoyaltyTransaction,
    Order,
)


class LoyaltyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_account(
        self, customer_id: int
    ) -> LoyaltyAccount:
        result = await self.db.execute(
            select(LoyaltyAccount).where(
                LoyaltyAccount.customer_id == customer_id
            )
        )
        account = result.scalar_one_or_none()
        if not account:
            account = LoyaltyAccount(
                customer_id=customer_id,
                points_earned=0,
                points_redeemed=0,
                points_expired=0,
                current_balance=0,
            )
            self.db.add(account)
            await self.db.flush()
        return account

    async def earn_points(
        self, customer_id: int, order_id: int, order_amount: float, multiplier: float = 1.0
    ) -> LoyaltyTransaction:
        account = await self.get_or_create_account(customer_id)

        points = int(order_amount * settings.LOYALTY_POINTS_PER_KES * multiplier)
        if points <= 0:
            raise ValueError("Order amount too low to earn points")

        expiry_date = date.today() + timedelta(days=settings.LOYALTY_POINTS_EXPIRY_DAYS)

        account.points_earned += points
        account.current_balance += points

        transaction = LoyaltyTransaction(
            account_id=account.id,
            transaction_type="earn",
            points=points,
            reference_type="order",
            reference_id=order_id,
            description=f"Points earned from order #{order_id}",
            expiry_date=expiry_date,
        )
        self.db.add(transaction)
        await self.db.flush()
        return transaction

    async def redeem_points(
        self, customer_id: int, points: int, reference_type: str | None = None,
        reference_id: int | None = None
    ) -> dict:
        account = await self.get_or_create_account(customer_id)

        if points <= 0:
            raise ValueError("Points must be positive")
        if points < settings.LOYALTY_MIN_REDEMPTION:
            raise ValueError(
                f"Minimum redemption is {settings.LOYALTY_MIN_REDEMPTION} points"
            )
        if points > account.current_balance:
            raise ValueError(
                f"Insufficient points. Available: {account.current_balance}, requested: {points}"
            )

        amount_off = points * settings.LOYALTY_REDEMPTION_RATE

        account.points_redeemed += points
        account.current_balance -= points

        transaction = LoyaltyTransaction(
            account_id=account.id,
            transaction_type="redeem",
            points=points,
            reference_type=reference_type,
            reference_id=reference_id,
            description=f"Points redeemed for KES {amount_off:.2f} off",
        )
        self.db.add(transaction)
        await self.db.flush()

        return {
            "points_redeemed": points,
            "amount_off": round(amount_off, 2),
            "remaining_balance": account.current_balance,
        }

    async def expire_points(self) -> int:
        expired_result = await self.db.execute(
            select(LoyaltyAccount)
        )
        total_expired = 0
        for account in expired_result.scalars().all():
            result = await self.db.execute(
                select(func.coalesce(func.sum(LoyaltyTransaction.points), 0))
                .where(
                    LoyaltyTransaction.account_id == account.id,
                    LoyaltyTransaction.expiry_date <= date.today(),
                    LoyaltyTransaction.expiry_date.isnot(None),
                    LoyaltyTransaction.transaction_type == "earn",
                )
            )
            expiring_points = result.scalar() or 0
            if expiring_points > 0:
                expire_amount = min(expiring_points, account.current_balance)
                if expire_amount > 0:
                    account.points_expired += expire_amount
                    account.current_balance -= expire_amount
                    tx = LoyaltyTransaction(
                        account_id=account.id,
                        transaction_type="expire",
                        points=expire_amount,
                        description=f"Points expired on {date.today().isoformat()}",
                    )
                    self.db.add(tx)
                    total_expired += expire_amount

        await self.db.flush()
        return total_expired

    async def get_account(self, customer_id: int) -> LoyaltyAccount | None:
        result = await self.db.execute(
            select(LoyaltyAccount).where(
                LoyaltyAccount.customer_id == customer_id
            )
        )
        return result.scalar_one_or_none()

    async def get_transactions(
        self, customer_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[LoyaltyTransaction], int]:
        account = await self.get_or_create_account(customer_id)

        query = (
            select(LoyaltyTransaction)
            .where(LoyaltyTransaction.account_id == account.id)
            .order_by(LoyaltyTransaction.created_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
