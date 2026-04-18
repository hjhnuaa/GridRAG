"""Domain enumerations used by ORM and Pydantic models."""

from __future__ import annotations

from enum import StrEnum


class EventCategory(StrEnum):
    """Event type enum."""

    COMPLAINT = "COMPLAINT"
    HAZARD = "HAZARD"
    DISPUTE = "DISPUTE"
    VISIT = "VISIT"
    OTHER = "OTHER"


class EventStatus(StrEnum):
    """Event status enum."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class DocType(StrEnum):
    """Knowledge document type enum."""

    POLICY = "policy"
    MANUAL = "manual"
    TICKET = "ticket"
    CASE = "case"


class IngestStatus(StrEnum):
    """Document ingest status enum."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class ResidentTag(StrEnum):
    """Resident tags used for vulnerable population categorization."""

    ELDERLY_ALONE = "ELDERLY_ALONE"
    DISABLED = "DISABLED"
    LOW_INCOME = "LOW_INCOME"
    CHRONIC_DISEASE = "CHRONIC_DISEASE"
    LEFT_BEHIND_CHILD = "LEFT_BEHIND_CHILD"
    OTHER = "OTHER"

