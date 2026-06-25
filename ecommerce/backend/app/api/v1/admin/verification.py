from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_db
from app.models.customer import Customer
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.verification_service import VerificationService

router = APIRouter()


@router.get("/pending")
async def get_pending_verifications(
    page: int = 1,
    page_size: int = 20,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    verifications, total = await service.get_pending_verifications(page, page_size)
    return {
        "items": verifications,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post("/{customer_id}/approve", response_model=MessageResponse)
async def approve_verification(
    customer_id: int,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    try:
        await service.approve_verification(customer_id, admin.id)
        await db.commit()
        return MessageResponse(message="Verification approved")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{customer_id}/reject", response_model=MessageResponse)
async def reject_verification(
    customer_id: int,
    reason: str,
    admin: Customer = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    try:
        await service.reject_verification(customer_id, admin.id, reason)
        await db.commit()
        return MessageResponse(message="Verification rejected")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
