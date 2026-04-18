"""Service functions for event management."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.enums import EventStatus
from app.models.event import Event
from app.schemas.common import PaginatedData, PaginationMeta
from app.schemas.event import EventCreate, EventResponse, EventUpdate


async def create_event(session: AsyncSession, payload: EventCreate) -> Event:
    """Create and persist a new event."""

    event = Event(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        status=EventStatus.PENDING,
        priority=payload.priority,
        address=payload.address,
        reporter_name=payload.reporter_name,
        resident_id=payload.resident_id,
        ai_suggestion=payload.ai_suggestion,
        attachments=payload.attachments,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def get_event_or_404(session: AsyncSession, event_id: str) -> Event:
    """Return an event by ID or raise 404."""

    event = await session.get(Event, event_id)
    if event is None:
        raise AppError("未找到指定工单。", code=4041, status_code=status.HTTP_404_NOT_FOUND)
    return event


async def list_events(
    session: AsyncSession,
    page: int,
    page_size: int,
    status_filter: str | None = None,
    category_filter: str | None = None,
    keyword: str | None = None,
) -> PaginatedData[EventResponse]:
    """List events with optional filters."""

    stmt: Select[tuple[Event]] = select(Event).order_by(Event.created_at.desc())
    count_stmt = select(func.count()).select_from(Event)

    if status_filter:
        stmt = stmt.where(Event.status == status_filter)
        count_stmt = count_stmt.where(Event.status == status_filter)
    if category_filter:
        stmt = stmt.where(Event.category == category_filter)
        count_stmt = count_stmt.where(Event.category == category_filter)
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(Event.title.like(pattern) | Event.description.like(pattern))
        count_stmt = count_stmt.where(Event.title.like(pattern) | Event.description.like(pattern))

    total = int((await session.execute(count_stmt)).scalar_one())
    result = await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    items = [EventResponse.model_validate(row) for row in result.scalars().all()]
    return PaginatedData(
        items=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


async def update_event(session: AsyncSession, event_id: str, payload: EventUpdate) -> Event:
    """Update an event."""

    event = await get_event_or_404(session, event_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(event, field_name, value)
    if payload.status == EventStatus.RESOLVED and event.resolved_at is None:
        event.resolved_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(event)
    return event


async def close_event(session: AsyncSession, event_id: str) -> Event:
    """Mark an event as closed."""

    event = await get_event_or_404(session, event_id)
    event.status = EventStatus.CLOSED
    event.resolved_at = event.resolved_at or datetime.now(UTC)
    await session.commit()
    await session.refresh(event)
    return event
