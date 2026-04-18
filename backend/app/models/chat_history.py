"""Chat history and retrieval log ORM models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


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
