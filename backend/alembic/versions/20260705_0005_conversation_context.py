"""Add conversation context metadata."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260705_0005"
down_revision = "20260502_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Store conversation summaries and message status."""

    op.add_column("chat_sessions", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column(
        "chat_sessions",
        sa.Column("summary_message_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("chat_sessions", sa.Column("summary_updated_at", sa.DateTime(), nullable=True))
    op.add_column(
        "chat_histories",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="complete"),
    )
    op.alter_column("chat_sessions", "summary_message_count", server_default=None)
    op.alter_column("chat_histories", "status", server_default=None)


def downgrade() -> None:
    """Remove conversation summaries and message status."""

    op.drop_column("chat_histories", "status")
    op.drop_column("chat_sessions", "summary_updated_at")
    op.drop_column("chat_sessions", "summary_message_count")
    op.drop_column("chat_sessions", "summary")
