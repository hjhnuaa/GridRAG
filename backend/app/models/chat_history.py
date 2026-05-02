"""Chat history and retrieval log ORM models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ChatSession(UUIDPrimaryKeyMixin, Base):
    """Persisted chat session metadata."""

    __tablename__ = "chat_sessions"
    __table_args__ = (Index("ix_chat_sessions_updated_at", "updated_at"),)

    title: Mapped[str] = mapped_column(String(120), nullable=False, default="新会话")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class ChatHistory(UUIDPrimaryKeyMixin, Base):
    """Persisted chat message history."""

    __tablename__ = "chat_histories"
    __table_args__ = (Index("ix_chat_histories_session_id_created_at", "session_id", "created_at"),)

    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)


class RetrievalLog(UUIDPrimaryKeyMixin, Base):
    """Stores retrieval debug data for later quality analysis."""

    __tablename__ = "retrieval_logs"
    __table_args__ = (Index("ix_retrieval_logs_session_id_created_at", "session_id", "created_at"),)

    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters: Mapped[dict[str, Any]] = mapped_column(nullable=False, default=dict)
    retrieval_ms: Mapped[int] = mapped_column(nullable=False, default=0)
    rerank_scores: Mapped[list[dict[str, Any]]] = mapped_column(nullable=False, default=list)
    top_chunks: Mapped[list[dict[str, Any]]] = mapped_column(nullable=False, default=list)
    is_grounded: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)


class ChatMemory(UUIDPrimaryKeyMixin, Base):
    """Long-term memory attached to a chat session."""

    __tablename__ = "chat_memories"
    __table_args__ = (Index("ix_chat_memories_session_id_updated_at", "session_id", "updated_at"),)

    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False, default="note")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(nullable=False, default=dict)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
