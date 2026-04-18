"""Common response and pagination schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with ORM support."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginationMeta(BaseSchema):
    """Pagination metadata."""

    page: int
    page_size: int
    total: int


class PageParams(BaseSchema):
    """Common page parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedData(BaseSchema, Generic[T]):
    """Paginated data payload."""

    items: list[T]
    meta: PaginationMeta


class ApiResponse(BaseSchema, Generic[T]):
    """Unified API response envelope."""

    code: int = 0
    message: str = "success"
    data: T | None = None


def success_response(data: T) -> ApiResponse[T]:
    """Create a successful API response payload."""

    return ApiResponse[T](data=data)

