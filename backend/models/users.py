from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import uuid
from sqlmodel import Column, Field, Relationship, SQLModel
import sqlalchemy.dialects.postgresql as pg
import sqlalchemy as sa

if TYPE_CHECKING:
    from backend.models.notifications import Notification


class Users(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    email: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False))
    password: str = Field(sa_column=Column(pg.VARCHAR(255), nullable=False))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            server_onupdate=sa.text("now()"),
        ),
    )
    notifications: list["Notification"] = Relationship(back_populates="user")

    def __repr__(self):
        return f"<User email: {self.email}>"
