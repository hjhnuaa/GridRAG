"""Schemas for resident and visit APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.event import EventResponse


class ResidentBase(BaseSchema):
    """Shared resident fields."""

    name: str = Field(min_length=2, max_length=100)
    id_number: str = Field(min_length=6, max_length=32)
    phone: str = Field(min_length=6, max_length=32)
    address: str = Field(min_length=2, max_length=255)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ResidentCreate(ResidentBase):
    """Create resident payload."""


class ResidentUpdate(BaseSchema):
    """Update resident payload."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    id_number: str | None = Field(default=None, min_length=6, max_length=32)
    phone: str | None = Field(default=None, min_length=6, max_length=32)
    address: str | None = Field(default=None, min_length=2, max_length=255)
    tags: list[str] | None = None
    notes: str | None = None


class VisitCreate(BaseSchema):
    """Create visit record payload."""

    visitor_name: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=4, max_length=4000)
    summary: str | None = None


class VisitRecordResponse(BaseSchema):
    """Resident visit payload."""

    id: str
    resident_id: str
    visitor_name: str
    content: str
    summary: str | None = None
    created_at: datetime


class ResidentResponse(ResidentBase):
    """Basic resident payload."""

    id: str
    last_visit_at: datetime | None = None
    visit_count: int
    created_at: datetime
    updated_at: datetime


class ResidentDetailResponse(ResidentResponse):
    """Resident detail with visit history and related events."""

    visits: list[VisitRecordResponse]
    related_events: list[EventResponse]


class VisitSuggestResponse(BaseSchema):
    """AI-generated visit guidance."""

    resident_id: str
    suggestions: list[str]
    risk_summary: str

