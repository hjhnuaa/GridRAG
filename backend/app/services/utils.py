"""Shared service utilities."""

from __future__ import annotations


def mask_id_number(value: str) -> str:
    """Mask an ID number, keeping only the last four characters visible."""

    cleaned = value.strip()
    if len(cleaned) <= 4:
        return cleaned
    return "*" * (len(cleaned) - 4) + cleaned[-4:]


def mask_phone(value: str) -> str:
    """Mask a phone number while preserving the last four digits."""

    cleaned = value.strip()
    if len(cleaned) <= 4:
        return cleaned
    return f"{cleaned[:3]}****{cleaned[-4:]}"

