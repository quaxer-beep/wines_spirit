from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import TimestampMixin


class CustomerBase(BaseModel):
    full_name: str
    phone: str
    email: EmailStr | None = None


class CustomerCreate(CustomerBase):
    password: str
    date_of_birth: date | None = None
    national_id: str | None = None


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    date_of_birth: date | None = None


class CustomerResponse(CustomerBase, TimestampMixin):
    id: int
    role: str
    date_of_birth: date | None = None
    national_id: str | None = None
    age_verified: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    status: str = "active"
    registration_date: datetime | None = None
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AddressBase(BaseModel):
    label: str | None = None
    address: str
    building_name: str | None = None
    landmark: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: str | None = None
    address: str | None = None
    building_name: str | None = None
    landmark: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool | None = None


class AddressResponse(AddressBase, TimestampMixin):
    id: int
    customer_id: int

    model_config = ConfigDict(from_attributes=True)
