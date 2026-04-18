"""Event ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import EventCategory, EventStatus


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Grid event ticket raised by a community worker."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_status_category_created_at", "status", "category", "created_at"),
        Index("ix_events_resident_id", "resident_id"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[EventCategory] = mapped_column(String(32), nullable=False)
    status: Mapped[EventStatus] = mapped_column(String(32), nullable=False, default=EventStatus.PENDING)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    resident_id: Mapped[str | None] = mapped_column(ForeignKey("residents.id"), nullable=True)
    ai_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[list[str]] = mapped_column(nullable=False, default=list)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    resident = relationship("Resident", back_populates="events")

