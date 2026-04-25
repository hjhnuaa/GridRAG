"""MCP-compatible JSON-RPC gateway."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.core.exceptions import AppError
from app.schemas.common import ApiResponse, success_response
from app.schemas.mcp import MCPRequest
from app.services.memory import list_memories, save_memory, to_memory_item
from app.services.web_search import WebSearchService

router = APIRouter(prefix="/mcp", tags=["MCP"])

MCP_SERVER_NAME = "gridrag-mcp"


@router.get("/tools")
async def list_mcp_tools() -> ApiResponse[dict[str, Any]]:
    """Return MCP tool definitions for normal REST inspection."""

    return success_response({"tools": _tool_definitions()})


@router.post("")
async def mcp_rpc(
    payload: MCPRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Handle MCP JSON-RPC requests."""

    settings = get_settings()
    if not settings.mcp_enabled:
        return _error(payload.id, -32000, "MCP gateway is disabled")

    if payload.method == "initialize":
        return _result(
            payload.id,
            {
                "protocolVersion": settings.mcp_protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": MCP_SERVER_NAME, "version": "1.0.0"},
            },
        )
    if payload.method == "ping":
        return _result(payload.id, {})
    if payload.method == "tools/list":
        return _result(payload.id, {"tools": _tool_definitions()})
    if payload.method == "tools/call":
        return await _call_tool(payload, session)
    if payload.method == "notifications/initialized":
        return _result(payload.id, {})
    return _error(payload.id, -32601, f"Unknown MCP method: {payload.method}")


async def _call_tool(payload: MCPRequest, session: AsyncSession) -> dict[str, Any]:
    """Dispatch a tools/call request."""

    name = str(payload.params.get("name") or "")
    arguments = payload.params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _error(payload.id, -32602, "Tool arguments must be an object")

    try:
        if name == "gridrag.memory.add":
            result = await _tool_memory_add(session, arguments)
        elif name == "gridrag.memory.search":
            result = await _tool_memory_search(session, arguments)
        elif name == "gridrag.web_search":
            result = await _tool_web_search(arguments)
        else:
            return _error(payload.id, -32602, f"Unknown tool: {name}")
    except (AppError, httpx.HTTPError, ValueError) as exc:
        return _result(payload.id, _tool_error(str(exc)))

    return _result(payload.id, _tool_text(result))


async def _tool_memory_add(session: AsyncSession, arguments: dict[str, Any]) -> dict[str, Any]:
    """Add a memory through MCP."""

    session_id = _required_string(arguments, "session_id")
    content = _required_string(arguments, "content")
    memory_type = str(arguments.get("memory_type") or "mcp")
    metadata = arguments.get("metadata") if isinstance(arguments.get("metadata"), dict) else {}
    memory = await save_memory(
        session,
        session_id=session_id,
        content=content,
        memory_type=memory_type,
        metadata=metadata,
    )
    return to_memory_item(memory).model_dump()


async def _tool_memory_search(session: AsyncSession, arguments: dict[str, Any]) -> dict[str, Any]:
    """Search memories through MCP."""

    session_id = _required_string(arguments, "session_id")
    query = str(arguments.get("query") or "")
    limit = int(arguments.get("limit") or 5)
    memories = await list_memories(session, session_id=session_id, query=query, limit=max(1, min(limit, 20)))
    return {"items": [to_memory_item(item).model_dump() for item in memories]}


async def _tool_web_search(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run a web search through MCP."""

    query = _required_string(arguments, "query")
    max_results = int(arguments.get("max_results") or 5)
    items = await WebSearchService().search(query, max(1, min(max_results, 10)))
    return {"items": [item.model_dump() for item in items]}


def _tool_definitions() -> list[dict[str, Any]]:
    """Return MCP tool definitions."""

    return [
        {
            "name": "gridrag.memory.add",
            "description": "为指定会话写入一条长期记忆。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "聊天会话 ID"},
                    "content": {"type": "string", "description": "需要记住的内容"},
                    "memory_type": {"type": "string", "description": "记忆类型，可选"},
                    "metadata": {"type": "object", "description": "附加元数据，可选"},
                },
                "required": ["session_id", "content"],
            },
        },
        {
            "name": "gridrag.memory.search",
            "description": "按会话和查询词检索长期记忆。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "聊天会话 ID"},
                    "query": {"type": "string", "description": "检索词，可为空"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "required": ["session_id"],
            },
        },
        {
            "name": "gridrag.web_search",
            "description": "通过后端配置的搜索供应商执行联网搜索。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    ]


def _required_string(arguments: dict[str, Any], key: str) -> str:
    """Read a required string argument."""

    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required argument: {key}")
    return value.strip()


def _tool_text(value: dict[str, Any]) -> dict[str, Any]:
    """Format a successful MCP tool result."""

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(value, ensure_ascii=False),
            }
        ],
        "structuredContent": value,
        "isError": False,
    }


def _tool_error(message: str) -> dict[str, Any]:
    """Format a failed MCP tool result."""

    return {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    }


def _result(request_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-RPC result."""

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: str | int | None, code: int, message: str) -> dict[str, Any]:
    """Build a JSON-RPC error."""

    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
