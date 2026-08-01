import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.database import get_session
from backend.dependencies import get_current_user
from backend.models.users import Users
from backend.schemas.notifications import (
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    UnreadCountResponse,
)
from backend.services.notification import (
    create_notification,
    delete_notification,
    get_notifications_by_user,
    get_unread_notifications_count,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from backend.utils.constants import KafkaEvents, KafkaTopics
from backend.utils.kafka import KafkaProducer
from backend.utils.notification_client import notification_stream

notification_router = APIRouter()
kafka_producer = KafkaProducer()


@notification_router.get("/", response_model=list[NotificationResponse])
async def get_my_notifications(
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    # This reads the saved inbox from the database. Use it when a page loads,
    # because live Redis events only cover messages sent while the page is open.
    return await get_notifications_by_user(session, current_user.id, skip, limit)


@notification_router.get("/unread-count", response_model=UnreadCountResponse)
async def get_my_unread_count(
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    unread_count = await get_unread_notifications_count(session, current_user.id)
    return {"unread_count": unread_count}


@notification_router.get("/stream")
async def stream_my_notifications(current_user: Users = Depends(get_current_user)):
    # This opens the live lane. Frontend code usually consumes it with:
    # new EventSource("/api/v1/notifications/stream")
    return StreamingResponse(
        notification_stream(str(current_user.id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@notification_router.post("/", response_model=NotificationResponse)
async def create_my_notification(
    notification: NotificationBase,
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # The request body does not include user_id on purpose. The backend gets
    # the user from the session token so clients cannot forge another user's ID.
    saved_notification = await create_notification(
        session,
        NotificationCreate(user_id=current_user.id, **notification.model_dump()),
    )
    kafka_producer.start()
    kafka_producer.send(
        KafkaTopics.NOTIFICATION_EVENTS,
        {
            "event_type": KafkaEvents.NOTIFICATION_CREATED,
            "user_id": str(current_user.id),
            "data": jsonable_encoder(saved_notification),
        },
    )
    return saved_notification


@notification_router.patch(
    "/{notification_id}/read", response_model=NotificationResponse
)
async def read_my_notification(
    notification_id: uuid.UUID,
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    notification = await mark_notification_as_read(
        session, notification_id, current_user.id
    )
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notification


@notification_router.patch("/read-all")
async def read_all_my_notifications(
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    updated_count = await mark_all_notifications_as_read(session, current_user.id)
    unread_count = await get_unread_notifications_count(session, current_user.id)
    kafka_producer.start()
    kafka_producer.send(
        KafkaTopics.NOTIFICATION_EVENTS,
        {
            "event_type": KafkaEvents.NOTIFICATION_UNREAD_COUNT,
            "user_id": str(current_user.id),
            "data": {"unread_count": unread_count},
        },
    )
    return {"updated_count": updated_count}


@notification_router.delete(
    "/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_my_notification(
    notification_id: uuid.UUID,
    current_user: Users = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    deleted = await delete_notification(session, notification_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
