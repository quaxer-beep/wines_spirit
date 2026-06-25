from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import TimestampMixin


class VerificationSubmit(BaseModel):
    date_of_birth: date
    national_id: str = Field(..., min_length=1, max_length=50)


class VerificationDocumentResponse(BaseModel):
    id: int
    document_type: str
    document_number: str
    front_image_url: str | None = None
    back_image_url: str | None = None
    selfie_url: str | None = None
    verification_status: str
    uploaded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class VerificationStatusResponse(TimestampMixin):
    id: int
    customer_id: int
    date_of_birth: date
    national_id: str
    verification_status: str
    verification_date: datetime | None = None
    rejection_reason: str | None = None
    documents: list[VerificationDocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)
