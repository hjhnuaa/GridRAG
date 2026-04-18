"""Schemas for event management APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.models.enums import EventCategory, EventStatus
from app.schemas.common import BaseSchema


class EventBase(BaseSchema):
    """Shared event fields."""

    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=4)
    category: EventCategory
    priority: int = Field(ge=1, le=5)
    address: str = Field(min_length=2, max_length=255)
    reporter_name: str = Field(min_length=2, max_length=100)
    resident_id: str | None = None
    ai_suggestion: str | None = None
    attachments: list[str] = Field(default_factory=list)


class EventCreate(EventBase):
    """Create event payload."""


class EventUpdate(BaseSchema):
    """Update event payload."""

    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, min_length=4)
    category: EventCategory | None = None
    status: EventStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    address: str | None = Field(default=None, min_length=2, max_length=255)
    reporter_name: str | None = Field(default=None, min_length=2, max_length=100)
    resident_id: str | None = None
    ai_suggestion: str | None = None
    attachments: list[str] | None = None


class EventResponse(EventBase):
    """Response payload for an event."""

    id: str
    status: EventStatus
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class EventAIAssistRequest(BaseSchema):
    """Natural language description used to request AI suggestions."""

    description: str = Field(min_length=4, max_length=2000)


class EventAIAssistResponse(BaseSchema):
    """AI-assisted event draft fields."""

    suggested_category: EventCategory
    suggested_priority: int = Field(ge=1, le=5)
    suggested_title: str
    suggested_action: str
    relevant_policy: str

    @field_validator("suggested_title", "suggested_action", "relevant_policy")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Reject blank AI suggestions."""

        stripped = value.strip()
        if not stripped:
            raise ValueError("字段不能为空。")
        return stripped

