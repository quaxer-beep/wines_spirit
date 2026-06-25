from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.customer import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    CustomerResponse,
    CustomerUpdate,
)
from app.schemas.common import MessageResponse
from app.services.customer_service import CustomerService

router = APIRouter()


@router.get("/me", response_model=CustomerResponse)
async def get_profile(current_user: Customer = Depends(get_authenticated_customer)):
    return current_user


@router.put("/me", response_model=CustomerResponse)
async def update_profile(
    data: CustomerUpdate,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    customer = await service.update_profile(current_user.id, data)
    await db.commit()
    return customer


@router.get("/addresses", response_model=list[AddressResponse])
async def list_addresses(
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    return await service.get_addresses(current_user.id)


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    data: AddressCreate,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    address = await service.create_address(current_user.id, data)
    await db.commit()
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: int,
    data: AddressUpdate,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    try:
        address = await service.update_address(current_user.id, address_id, data)
        await db.commit()
        return address
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_address(
    address_id: int,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = CustomerService(db)
    try:
        await service.delete_address(current_user.id, address_id)
        await db.commit()
        return MessageResponse(message="Address deleted")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
