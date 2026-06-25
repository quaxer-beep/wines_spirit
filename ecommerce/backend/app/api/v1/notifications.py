from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_authenticated_customer, get_db
from app.models.customer import Customer
from app.schemas.common import MessageResponse
from app.schemas.notification import (
    NotificationListResponse,
    NotificationMarkRead,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = 1,
    page_size: int = 20,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    notifications, total, unread_count = await service.get_customer_notifications(
        current_user.id, page, page_size
    )

    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                notification_type=n.notification_type,
                channel=n.channel,
                title=n.title,
                message=n.message,
                reference_type=n.reference_type,
                reference_id=n.reference_id,
                is_read=n.is_read,
                sent_at=n.sent_at,
                read_at=n.read_at,
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count,
    )


@router.put("/read", response_model=MessageResponse)
async def mark_notifications_read(
    data: NotificationMarkRead,
    current_user: Customer = Depends(get_authenticated_customer),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.mark_as_read(current_user.id, data.notification_ids)
    await db.commit()
    return MessageResponse(message=f"{count} notifications marked as read")
