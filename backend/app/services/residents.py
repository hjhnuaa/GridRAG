"""Service functions for resident management."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.core.security import mask_id_number, mask_phone
from app.models.event import Event
from app.models.resident import Resident, VisitRecord
from app.schemas.common import PaginatedData, PaginationMeta
from app.schemas.event import EventResponse
from app.schemas.resident import (
    ResidentCreate,
    ResidentDetailResponse,
    ResidentResponse,
    ResidentUpdate,
    VisitCreate,
    VisitRecordResponse,
)


async def create_resident(session: AsyncSession, payload: ResidentCreate) -> Resident:
    """Create and persist a resident profile."""

    resident = Resident(
        name=payload.name,
        id_number=mask_id_number(payload.id_number),
        phone=mask_phone(payload.phone),
        address=payload.address,
        tags=payload.tags,
        notes=payload.notes,
    )
    session.add(resident)
    await session.commit()
    await session.refresh(resident)
    return resident


async def get_resident_or_404(session: AsyncSession, resident_id: str) -> Resident:
    """Return a resident with relations or raise 404."""

    stmt = (
        select(Resident)
        .where(Resident.id == resident_id)
        .options(selectinload(Resident.visits), selectinload(Resident.events))
    )
    resident = (await session.execute(stmt)).scalar_one_or_none()
    if resident is None:
        raise AppError("未找到指定居民档案。", code=4042, status_code=status.HTTP_404_NOT_FOUND)
    return resident


async def list_residents(
    session: AsyncSession,
    page: int,
    page_size: int,
    tags: list[str] | None = None,
) -> PaginatedData[ResidentResponse]:
    """List residents with optional tag filters."""

    stmt = select(Resident).order_by(Resident.created_at.desc())
    count_stmt = select(func.count()).select_from(Resident)
    if tags:
        for tag in tags:
            stmt = stmt.where(Resident.tags.contains([tag]))
            count_stmt = count_stmt.where(Resident.tags.contains([tag]))

    total = int((await session.execute(count_stmt)).scalar_one())
    residents = (
        await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()
    return PaginatedData(
        items=[ResidentResponse.model_validate(item) for item in residents],
        meta=PaginationMeta(page=page, page_size=page_size, total=total),
    )


async def update_resident(session: AsyncSession, resident_id: str, payload: ResidentUpdate) -> Resident:
    """Update a resident profile."""

    resident = await get_resident_or_404(session, resident_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "id_number" in update_data and update_data["id_number"] is not None:
        update_data["id_number"] = mask_id_number(update_data["id_number"])
    if "phone" in update_data and update_data["phone"] is not None:
        update_data["phone"] = mask_phone(update_data["phone"])
    for field_name, value in update_data.items():
        setattr(resident, field_name, value)
    await session.commit()
    await session.refresh(resident)
    return resident


async def add_visit_record(session: AsyncSession, resident_id: str, payload: VisitCreate) -> VisitRecord:
    """Create a new visit record for a resident."""

    resident = await get_resident_or_404(session, resident_id)
    visit = VisitRecord(
        resident_id=resident_id,
        visitor_name=payload.visitor_name,
        content=payload.content,
        summary=payload.summary,
        created_at=datetime.now(UTC),
    )
    resident.last_visit_at = visit.created_at
    resident.visit_count += 1
    session.add(visit)
    await session.commit()
    await session.refresh(visit)
    return visit


async def build_resident_detail(session: AsyncSession, resident_id: str) -> ResidentDetailResponse:
    """Build a resident detail view model."""

    resident = await get_resident_or_404(session, resident_id)
    related_events_stmt = select(Event).where(Event.resident_id == resident_id).order_by(Event.created_at.desc())
    related_events = (await session.execute(related_events_stmt)).scalars().all()
    return ResidentDetailResponse(
        **ResidentResponse.model_validate(resident).model_dump(),
        visits=[
            VisitRecordResponse.model_validate(item)
            for item in sorted(resident.visits, key=lambda item: item.created_at, reverse=True)
        ],
        related_events=[EventResponse.model_validate(item) for item in related_events],
    )
