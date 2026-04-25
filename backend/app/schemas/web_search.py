"""Schemas for web search."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema


class WebSearchRequest(BaseSchema):
    """Web search request payload."""

    query: str = Field(min_length=1, max_length=500)
    max_results: int | None = Field(default=None, ge=1, le=10)


class WebSearchResult(BaseSchema):
    """Normalized web search result."""

    title: str
    url: str
    snippet: str
    provider: str
    score: float | None = None


class WebSearchResponse(BaseSchema):
    """Web search response payload."""

    items: list[WebSearchResult]


class WebSearchStatusResponse(BaseSchema):
    """Safe diagnostics for the configured web search provider."""

    enabled: bool
    provider: str
    endpoint: str
    api_key_configured: bool
    ok: bool
    message: str
    provider_status_code: int | None = None
    response_preview: str = ""
    sample_count: int = 0
