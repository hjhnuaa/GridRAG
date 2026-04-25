"""Memory management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.common import ApiResponse, success_response
from app.schemas.memory import MemoryCreateRequest, MemoryItem, MemorySearchResponse
from app.services.memory import delete_memory, list_memories, save_memory, to_memory_item

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
    )
    return success_response(to_memory_item(memory))


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


@router.delete("/{memory_id}")
async def remove_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict[str, bool]]:
    """Delete a memory item."""

    deleted = await delete_memory(session=session, memory_id=memory_id)
    return success_response({"deleted": deleted})
