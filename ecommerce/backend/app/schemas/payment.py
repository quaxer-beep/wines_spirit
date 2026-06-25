from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MpesaSTKPushRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?254\d{9}$")
    amount: float = Field(..., gt=0)


class MpesaCallbackRequest(BaseModel):
    Body: dict


class MpesaCallbackResponse(BaseModel):
    ResultCode: int = 0
    ResultDesc: str = "Success"


class PaymentInitiateResponse(BaseModel):
    checkout_request_id: str
    merchant_request_id: str
    amount: float
    phone: str
    status: str = "pending"


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    method: str
    amount: float
    merchant_request_id: str | None = None
    checkout_request_id: str | None = None
    receipt_number: str | None = None
    phone_number: str | None = None
    status: str
    result_desc: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
