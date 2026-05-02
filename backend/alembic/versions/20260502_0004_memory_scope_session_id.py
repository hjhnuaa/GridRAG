"""Widen memory session ids for scoped memory layers."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260502_0004"
down_revision = "20260429_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Allow reserved scoped memory ids such as organization/global."""

    op.alter_column(
        "chat_memories",
        "session_id",
        existing_type=sa.String(length=36),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Restore the original session id length."""

    op.alter_column(
        "chat_memories",
        "session_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=36),
        existing_nullable=False,
    )
