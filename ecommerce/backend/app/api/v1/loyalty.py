from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.loyalty import (
    LoyaltyAccountResponse,
    LoyaltyRedeemRequest,
    LoyaltyRedeemResponse,
    LoyaltyTransactionListResponse,
    LoyaltyTransactionResponse,
)
from app.services.loyalty_service import LoyaltyService

router = APIRouter()


@router.get("/account", response_model=LoyaltyAccountResponse)
async def get_loyalty_account(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = LoyaltyService(db)
    account = await service.get_account(current_user.id)
    if not account:
        account = await service.get_or_create_account(current_user.id)
        await db.commit()
    return account


@router.get("/transactions", response_model=LoyaltyTransactionListResponse)
async def get_loyalty_transactions(
    page: int = 1,
    page_size: int = 20,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = LoyaltyService(db)
    transactions, total = await service.get_transactions(
        current_user.id, page, page_size
    )
    return LoyaltyTransactionListResponse(
        transactions=[
            LoyaltyTransactionResponse(
                id=t.id,
                account_id=t.account_id,
                transaction_type=t.transaction_type,
                points=t.points,
                reference_type=t.reference_type,
                reference_id=t.reference_id,
                description=t.description,
                expiry_date=t.expiry_date,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=total,
    )


@router.post("/redeem", response_model=LoyaltyRedeemResponse)
async def redeem_points(
    data: LoyaltyRedeemRequest,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = LoyaltyService(db)
    try:
        result = await service.redeem_points(current_user.id, data.points)
        await db.commit()
        return LoyaltyRedeemResponse(
            points_redeemed=result["points_redeemed"],
            amount_off=result["amount_off"],
            remaining_balance=result["remaining_balance"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
