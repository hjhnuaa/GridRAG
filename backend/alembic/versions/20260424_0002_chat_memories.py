"""Add chat memories."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260424_0002"
down_revision = "20260418_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the chat memory table."""

    op.create_table(
        "chat_memories",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("memory_type", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_memories")),
    )
    op.create_index(
        "ix_chat_memories_session_id_updated_at",
        "chat_memories",
        ["session_id", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the chat memory table."""

    op.drop_index("ix_chat_memories_session_id_updated_at", table_name="chat_memories")
    op.drop_table("chat_memories")
