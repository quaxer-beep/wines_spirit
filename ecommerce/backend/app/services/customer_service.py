from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer, CustomerAddress
from app.schemas.customer import CustomerUpdate, AddressCreate, AddressUpdate


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, customer_id: int) -> Customer | None:
        result = await self.db.execute(
            select(Customer)
            .where(Customer.id == customer_id)
            .options(selectinload(Customer.addresses))
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(Customer.phone == phone)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self, customer_id: int, data: CustomerUpdate
    ) -> Customer:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            raise ValueError("Customer not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        await self.db.flush()
        return customer

    async def create_address(
        self, customer_id: int, data: AddressCreate
    ) -> CustomerAddress:
        if data.is_default:
            await self._clear_default_address(customer_id)

        address = CustomerAddress(customer_id=customer_id, **data.model_dump())
        self.db.add(address)
        await self.db.flush()
        return address

    async def update_address(
        self, customer_id: int, address_id: int, data: AddressUpdate
    ) -> CustomerAddress:
        result = await self.db.execute(
            select(CustomerAddress).where(
                CustomerAddress.id == address_id,
                CustomerAddress.customer_id == customer_id,
            )
        )
        address = result.scalar_one_or_none()
        if not address:
            raise ValueError("Address not found")

        update_data = data.model_dump(exclude_unset=True)
        if "is_default" in update_data and update_data["is_default"]:
            await self._clear_default_address(customer_id)

        for field, value in update_data.items():
            setattr(address, field, value)

        await self.db.flush()
        return address

    async def delete_address(self, customer_id: int, address_id: int) -> None:
        result = await self.db.execute(
            select(CustomerAddress).where(
                CustomerAddress.id == address_id,
                CustomerAddress.customer_id == customer_id,
            )
        )
        address = result.scalar_one_or_none()
        if not address:
            raise ValueError("Address not found")

        await self.db.delete(address)
        await self.db.flush()

    async def get_addresses(self, customer_id: int) -> list[CustomerAddress]:
        result = await self.db.execute(
            select(CustomerAddress)
            .where(CustomerAddress.customer_id == customer_id)
            .order_by(CustomerAddress.is_default.desc(), CustomerAddress.id)
        )
        return list(result.scalars().all())

    async def _clear_default_address(self, customer_id: int) -> None:
        result = await self.db.execute(
            select(CustomerAddress).where(
                CustomerAddress.customer_id == customer_id,
                CustomerAddress.is_default == True,
            )
        )
        for addr in result.scalars().all():
            addr.is_default = False
