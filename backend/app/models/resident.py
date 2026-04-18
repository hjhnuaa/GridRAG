"""Resident and visit ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Resident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Resident profile for community governance work."""

    __tablename__ = "residents"
    __table_args__ = (Index("ix_residents_name_address", "name", "address"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    id_number: Mapped[str] = mapped_column(String(32), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    tags: Mapped[list[str]] = mapped_column(nullable=False, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_visit_at: Mapped[datetime | None] = mapped_column(nullable=True)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    visits = relationship("VisitRecord", back_populates="resident", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="resident")


class VisitRecord(UUIDPrimaryKeyMixin, Base):
    """Visit history for a resident."""

    __tablename__ = "visit_records"
    __table_args__ = (Index("ix_visit_records_resident_id_created_at", "resident_id", "created_at"),)

    resident_id: Mapped[str] = mapped_column(ForeignKey("residents.id"), nullable=False)
    visitor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    resident = relationship("Resident", back_populates="visits")

