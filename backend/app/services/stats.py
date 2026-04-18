"""Service functions for dashboard statistics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import DocumentChunk
from app.models.event import Event
from app.schemas.stats import DashboardStatsResponse, MonthlyDuration, PieSlice, TrendPoint


async def build_dashboard_stats(session: AsyncSession) -> DashboardStatsResponse:
    """Build dashboard data used by the frontend overview page."""

    end_day = datetime.now(UTC).date()
    start_day = end_day - timedelta(days=29)

    trend_rows = (
        await session.execute(
            select(
                func.date(Event.created_at),
                Event.category,
                func.count(Event.id),
            )
            .where(Event.created_at >= start_day)
            .group_by(func.date(Event.created_at), Event.category)
            .order_by(func.date(Event.created_at), Event.category)
        )
    ).all()

    category_rows = (
        await session.execute(
            select(Event.category, func.count(Event.id)).group_by(Event.category).order_by(Event.category)
        )
    ).all()

    status_rows = (
        await session.execute(select(Event.status, func.count(Event.id)).group_by(Event.status).order_by(Event.status))
    ).all()

    duration_rows = (
        await session.execute(
            select(
                func.date_format(Event.created_at, "%Y-%m"),
                func.avg(
                    case(
                        (
                            Event.resolved_at.is_not(None),
                            func.timestampdiff(literal_column("HOUR"), Event.created_at, Event.resolved_at),
                        ),
                        else_=0,
                    )
                ),
            )
            .group_by(func.date_format(Event.created_at, "%Y-%m"))
            .order_by(func.date_format(Event.created_at, "%Y-%m"))
        )
    ).all()

    chunk_rows = (
        await session.execute(
            select(DocumentChunk.doc_type, func.count(DocumentChunk.id))
            .group_by(DocumentChunk.doc_type)
            .order_by(DocumentChunk.doc_type)
        )
    ).all()

    return DashboardStatsResponse(
        event_trend=[
            TrendPoint(date=str(day), category=str(category), count=int(count))
            for day, category, count in trend_rows
        ],
        event_category_distribution=[
            PieSlice(name=str(name), value=int(value)) for name, value in category_rows
        ],
        event_status_distribution=[
            PieSlice(name=str(name), value=int(value)) for name, value in status_rows
        ],
        average_resolution_hours=[
            MonthlyDuration(month=str(month), hours=float(hours or 0)) for month, hours in duration_rows
        ],
        knowledge_cards=[
            {"name": str(doc_type), "value": int(count)} for doc_type, count in chunk_rows
        ],
    )
