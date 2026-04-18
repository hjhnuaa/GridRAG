"""Event management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.common import ApiResponse, success_response
from app.schemas.event import EventAIAssistRequest, EventCreate, EventResponse, EventUpdate
from app.services.assistants import generate_event_assist
from app.services.events import close_event, create_event, get_event_or_404, list_events, update_event

router = APIRouter(prefix="/events", tags=["事件管理"])


@router.get("")
async def get_events(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """List events."""

    data = await list_events(
        session=session,
        page=page,
        page_size=page_size,
        status_filter=status,
        category_filter=category,
        keyword=keyword,
    )
    return success_response(data)


@router.post("")
async def post_event(
    payload: EventCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EventResponse]:
    """Create an event ticket."""

    event = await create_event(session, payload)
    return success_response(EventResponse.model_validate(event))


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EventResponse]:
    """Get event details."""

    event = await get_event_or_404(session, event_id)
    return success_response(EventResponse.model_validate(event))


@router.patch("/{event_id}")
async def patch_event(
    event_id: str,
    payload: EventUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EventResponse]:
    """Update an event."""

    event = await update_event(session, event_id, payload)
    return success_response(EventResponse.model_validate(event))


@router.post("/{event_id}/close")
async def post_close_event(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EventResponse]:
    """Close an event."""

    event = await close_event(session, event_id)
    return success_response(EventResponse.model_validate(event))


@router.post("/ai-assist")
async def ai_assist(
    payload: EventAIAssistRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Generate AI-assisted event suggestions."""

    data = await generate_event_assist(session=session, description=payload.description)
    return success_response(data)
