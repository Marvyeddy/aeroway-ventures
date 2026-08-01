from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime
from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone

if TYPE_CHECKING:
    from backend.models.users import Users


class NotificationType:
    TICKET_UPLOADED = "ticket_uploaded"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    BOOKING_CONFIRMED = "booking_confirmed"
    GENERAL = "general"


class Notification(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    type: str = Field(default=NotificationType.GENERAL, nullable=False)
    message: str = Field(nullable=False)
    is_read: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )
    )
    user: "Users" = Relationship(back_populates="notifications")
