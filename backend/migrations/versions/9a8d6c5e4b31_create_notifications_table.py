"""create notifications table

Revision ID: 9a8d6c5e4b31
Revises: 12c49d84e6f9
Create Date: 2026-07-31 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a8d6c5e4b31"
down_revision: Union[str, Sequence[str], None] = "12c49d84e6f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the table that stores notification history."""
    op.create_table(
        "notification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_user_id_created_at",
        "notification",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    """Drop notification history."""
    op.drop_index("ix_notification_user_id_created_at", table_name="notification")
    op.drop_table("notification")
