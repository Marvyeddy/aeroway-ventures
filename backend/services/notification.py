from typing import Optional

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.models.notifications import Notification
from backend.schemas.notifications import NotificationCreate
import uuid


async def create_notification(
    session: AsyncSession, notification: NotificationCreate
) -> Notification:
    # Step 1 of the notification flow: save it permanently.
    # Redis is only for "right now"; the database is the history/inbox.
    db_notification = Notification(**notification.model_dump())
    session.add(db_notification)
    await session.commit()
    await session.refresh(db_notification)
    return db_notification


async def get_notifications_by_user(
    session: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 10
) -> list[Notification]:
    statement = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    return list(result.all())


async def get_unread_notifications_count(
    session: AsyncSession, user_id: uuid.UUID
) -> int:
    statement = (
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .where(Notification.is_read.is_(False))
    )
    result = await session.exec(statement)
    return result.one()


async def mark_notification_as_read(
    session: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[Notification]:
    statement = (
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user_id)
    )
    result = await session.exec(statement)
    notification = result.first()
    if notification:
        notification.is_read = True
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
    return notification


async def mark_all_notifications_as_read(
    session: AsyncSession, user_id: uuid.UUID
) -> int:
    statement = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read.is_(False))
    )
    result = await session.exec(statement)
    notifications = result.all()
    for notification in notifications:
        notification.is_read = True
        session.add(notification)
    await session.commit()
    return len(notifications)


async def delete_notification(
    session: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    statement = (
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user_id)
    )
    result = await session.exec(statement)
    notification = result.first()
    if notification:
        await session.delete(notification)
        await session.commit()
        return True
    return False
