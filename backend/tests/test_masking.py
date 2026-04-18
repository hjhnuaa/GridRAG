"""Tests for masking utilities."""

from __future__ import annotations

from app.services.utils import mask_id_number, mask_phone


def test_mask_id_number() -> None:
    """ID numbers should only expose the last four characters."""

    assert mask_id_number("123456789012345678") == "**************5678"


def test_mask_phone() -> None:
    """Phone numbers should hide middle digits."""

    assert mask_phone("13812345678") == "138****5678"

