"""Schemas for long-term chat memory."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class MemoryCreateRequest(BaseSchema):
    """Request payload for creating a memory."""

    session_id: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=2000)
    memory_type: str = Field(default="note", max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryItem(BaseSchema):
    """A persisted memory item."""

    id: str
    session_id: str
    content: str
    memory_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    usage_count: int
    last_used_at: str | None = None
    created_at: str
    updated_at: str


class MemorySearchResponse(BaseSchema):
    """Search response for session memories."""

    items: list[MemoryItem]
