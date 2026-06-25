from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.common import TimestampMixin


class LoyaltyAccountResponse(TimestampMixin):
    id: int
    customer_id: int
    points_earned: int = 0
    points_redeemed: int = 0
    points_expired: int = 0
    current_balance: int = 0

    model_config = ConfigDict(from_attributes=True)


class LoyaltyTransactionResponse(BaseModel):
    id: int
    account_id: int
    transaction_type: str
    points: int
    reference_type: str | None = None
    reference_id: int | None = None
    description: str | None = None
    expiry_date: date | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoyaltyTransactionListResponse(BaseModel):
    transactions: list[LoyaltyTransactionResponse]
    total: int


class LoyaltySettings(BaseModel):
    points_per_currency: float = 1.0
    redemption_rate: float = 0.05
    min_redemption_points: int = 100
    points_expiry_days: int = 365


class LoyaltyRedeemRequest(BaseModel):
    points: int


class LoyaltyRedeemResponse(BaseModel):
    points_redeemed: int
    amount_off: float
    remaining_balance: int
