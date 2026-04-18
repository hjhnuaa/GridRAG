"""Resident archive endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.common import ApiResponse, success_response
from app.schemas.resident import ResidentCreate, ResidentResponse, ResidentUpdate, VisitCreate, VisitRecordResponse
from app.services.assistants import generate_visit_suggest
from app.services.residents import (
    add_visit_record,
    build_resident_detail,
    create_resident,
    list_residents,
    update_resident,
)

router = APIRouter(prefix="/residents", tags=["居民档案"])


@router.get("")
async def get_residents(
    page: int = 1,
    page_size: int = 20,
    tags: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """List resident profiles."""

    tag_list = [item.strip() for item in tags.split(",")] if tags else None
    data = await list_residents(session=session, page=page, page_size=page_size, tags=tag_list)
    return success_response(data)


@router.post("")
async def post_resident(
    payload: ResidentCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ResidentResponse]:
    """Create a resident profile."""

    resident = await create_resident(session, payload)
    return success_response(ResidentResponse.model_validate(resident))


@router.get("/{resident_id}")
async def get_resident(
    resident_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Get resident details."""

    data = await build_resident_detail(session, resident_id)
    return success_response(data)


@router.patch("/{resident_id}")
async def patch_resident(
    resident_id: str,
    payload: ResidentUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ResidentResponse]:
    """Update resident details."""

    resident = await update_resident(session, resident_id, payload)
    return success_response(ResidentResponse.model_validate(resident))


@router.post("/{resident_id}/visit")
async def post_visit(
    resident_id: str,
    payload: VisitCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[VisitRecordResponse]:
    """Create a resident visit record."""

    visit = await add_visit_record(session, resident_id, payload)
    return success_response(VisitRecordResponse.model_validate(visit))


@router.get("/{resident_id}/visit-suggest")
async def visit_suggest(
    resident_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[object]:
    """Generate AI visit guidance."""

    detail = await build_resident_detail(session, resident_id)
    data = await generate_visit_suggest(
        resident=detail.model_dump(exclude={"visits", "related_events"}, mode="json"),
        visits=[item.model_dump(mode="json") for item in detail.visits],
        related_events=[item.model_dump(mode="json") for item in detail.related_events],
    )
    return success_response(data)
