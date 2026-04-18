"""Schemas for dashboard statistics."""

from __future__ import annotations

from app.schemas.common import BaseSchema


class TrendPoint(BaseSchema):
    """Time-series point."""

    date: str
    category: str
    count: int


class PieSlice(BaseSchema):
    """Pie chart slice."""

    name: str
    value: int


class MonthlyDuration(BaseSchema):
    """Average event duration by month."""

    month: str
    hours: float


class DashboardStatsResponse(BaseSchema):
    """Dashboard statistics payload."""

    event_trend: list[TrendPoint]
    event_category_distribution: list[PieSlice]
    event_status_distribution: list[PieSlice]
    average_resolution_hours: list[MonthlyDuration]
    knowledge_cards: list[dict[str, int | str]]

