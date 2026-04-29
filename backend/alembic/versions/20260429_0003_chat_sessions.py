"""Add chat session metadata."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260429_0003"
down_revision = "20260424_0002"
branch_labels = None
depends_on = None

DEFAULT_SESSION_TITLE = "新会话"


def _build_title(content: str) -> str:
    title = " ".join((content or "").split()).strip()
    return title[:24] or DEFAULT_SESSION_TITLE


def upgrade() -> None:
    """Create the chat session metadata table and backfill existing histories."""

    op.create_table(
        "chat_sessions",
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
    )
    op.create_index("ix_chat_sessions_updated_at", "chat_sessions", ["updated_at"], unique=False)

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT session_id, role, content, created_at
            FROM chat_histories
            ORDER BY session_id, created_at
            """
        )
    ).mappings()

    sessions: dict[str, dict[str, object]] = {}
    for row in rows:
        session_id = str(row["session_id"])
        created_at = row["created_at"]
        item = sessions.setdefault(
            session_id,
            {
                "id": session_id,
                "title": DEFAULT_SESSION_TITLE,
                "message_count": 0,
                "created_at": created_at,
                "updated_at": created_at,
            },
        )
        item["message_count"] = int(item["message_count"]) + 1
        item["updated_at"] = created_at
        if row["role"] == "user" and item["title"] == DEFAULT_SESSION_TITLE:
            item["title"] = _build_title(str(row["content"]))

    if sessions:
        chat_sessions = sa.table(
            "chat_sessions",
            sa.column("id", sa.String(length=36)),
            sa.column("title", sa.String(length=120)),
            sa.column("message_count", sa.Integer()),
            sa.column("created_at", sa.DateTime()),
            sa.column("updated_at", sa.DateTime()),
        )
        op.bulk_insert(chat_sessions, list(sessions.values()))


def downgrade() -> None:
    """Drop the chat session metadata table."""

    op.drop_index("ix_chat_sessions_updated_at", table_name="chat_sessions")
    op.drop_table("chat_sessions")
