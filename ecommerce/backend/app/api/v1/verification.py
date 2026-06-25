from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.common import MessageResponse
from app.schemas.verification import VerificationStatusResponse, VerificationSubmit
from app.services.verification_service import VerificationService

router = APIRouter()


@router.post("/verification", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def submit_verification(
    data: VerificationSubmit,
    request: Request,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    try:
        verification = await service.submit_verification(
            customer_id=current_user.id,
            date_of_birth=data.date_of_birth,
            national_id=data.national_id,
        )
        await db.commit()
        return MessageResponse(
            message="Verification submitted successfully. Pending admin review.",
            status_code=201,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/verification/status", response_model=VerificationStatusResponse | None)
async def get_verification_status(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = VerificationService(db)
    verification = await service.get_verification(current_user.id)
    return verification
