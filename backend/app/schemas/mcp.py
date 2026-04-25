"""Schemas for the MCP JSON-RPC gateway."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class MCPRequest(BaseSchema):
    """Single JSON-RPC request for MCP."""

    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
