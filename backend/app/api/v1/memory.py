"""Memory management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import AppError
from app.schemas.common import ApiResponse, success_response
from app.schemas.memory import (
    MemoryContextResponse,
    MemoryCreateRequest,
    MemoryDeleteResponse,
    MemoryItem,
    MemorySearchResponse,
    ScopedMemoryCreateRequest,
)
from app.services.memory import (
    HUMAN_RULE_SCOPES,
    MemoryScope,
    delete_memory,
    delete_session_memories,
    find_relevant_memories,
    list_memories,
    list_scoped_memories,
    normalize_memory_scope,
    render_memory_context,
    save_memory,
    scoped_session_id,
    to_memory_item,
)

router = APIRouter(prefix="/memory", tags=["长期记忆"])


@router.post("")
async def create_memory(
    payload: MemoryCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemoryItem]:
    """Create a memory item for a chat session."""

    memory = await save_memory(
        session=session,
        session_id=payload.session_id,
        content=payload.content,
        memory_type=payload.memory_type,
        metadata=payload.metadata,
        scope=payload.scope,
        key=payload.key,
    )
    return success_response(to_memory_item(memory))


@router.post("/scopes/{scope}")
async def create_scoped_memory(
    scope: str,
    payload: ScopedMemoryCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemoryItem]:
    """Create a rule memory in a reserved layered scope."""

    normalized_scope = _require_scoped_memory_scope(scope)
    memory = await save_memory(
        session=session,
        session_id="",
        content=payload.content,
        memory_type=payload.memory_type,
        metadata=payload.metadata,
        scope=normalized_scope,
        key=payload.key,
    )
    return success_response(to_memory_item(memory))


@router.get("/scopes/{scope}")
async def get_scoped_memories(
    scope: str,
    query: str = "",
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemorySearchResponse]:
    """List or search memories stored in one layered scope."""

    normalized_scope = _require_scoped_memory_scope(scope)
    memories = await list_scoped_memories(session=session, scope=normalized_scope, query=query, limit=limit)
    return success_response(MemorySearchResponse(items=[to_memory_item(item) for item in memories]))


@router.get("/{session_id}/context")
async def get_memory_context(
    session_id: str,
    query: str = "",
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemoryContextResponse]:
    """Preview the final memory snippets that would be injected into a prompt."""

    memories = await find_relevant_memories(session=session, session_id=session_id, query=query, mark_used=False)
    return success_response(MemoryContextResponse(snippets=render_memory_context(memories)))


@router.get("/{session_id}")
async def get_memories(
    session_id: str,
    query: str = "",
    limit: int = 20,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemorySearchResponse]:
    """List or search memories for a chat session."""

    memories = await list_memories(session=session, session_id=session_id, query=query, limit=limit)
    return success_response(MemorySearchResponse(items=[to_memory_item(item) for item in memories]))


@router.delete("/sessions/{session_id}")
async def clear_session_memories(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemoryDeleteResponse]:
    """Delete all memory items for a chat session."""

    data = await delete_session_memories(session=session, session_id=session_id)
    return success_response(data)


@router.delete("/scopes/{scope}")
async def clear_scoped_memories(
    scope: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[MemoryDeleteResponse]:
    """Delete all memory items stored in one layered scope."""

    normalized_scope = _require_scoped_memory_scope(scope)
    data = await delete_session_memories(session=session, session_id=scoped_session_id(normalized_scope))
    return success_response(data)


@router.delete("/{memory_id}")
async def remove_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict[str, bool]]:
    """Delete a memory item."""

    deleted = await delete_memory(session=session, memory_id=memory_id)
    return success_response({"deleted": deleted})


def _require_scoped_memory_scope(scope: str) -> MemoryScope:
    """Validate route scope values for scoped memory APIs."""

    normalized = normalize_memory_scope(scope)
    if normalized is MemoryScope.SESSION:
        raise AppError("不支持的记忆层级。可选：organization、project、personal、local、global、auto。", code=4001)
    if normalized not in (*HUMAN_RULE_SCOPES, MemoryScope.AUTO):
        raise AppError("不支持的记忆层级。", code=4001)
    return normalized
