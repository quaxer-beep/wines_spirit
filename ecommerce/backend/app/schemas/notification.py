from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    channel: str
    title: str
    message: str
    reference_type: str | None = None
    reference_id: int | None = None
    is_read: bool = False
    sent_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationMarkRead(BaseModel):
    notification_ids: list[int]


class NotificationSendRequest(BaseModel):
    customer_id: int | None = None
    rider_id: int | None = None
    branch_id: int | None = None
    notification_type: str
    channel: str = "in_app"
    title: str
    message: str
    reference_type: str | None = None
    reference_id: int | None = None
