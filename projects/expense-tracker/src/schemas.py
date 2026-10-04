"""Pydantic v2 request/response models and field-level validation rules.

Validation rules (from architecture.md section 5):
- amount: strictly > 0, at most 2 decimal places (excess precision -> 422).
- category: non-empty after trim, stored trimmed.
- date: valid ISO calendar date (datetime.date handles 2026-02-30 rejection).
- note: optional, max 500 characters.
- Unknown/extra fields rejected via `extra="forbid"`.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

NOTE_MAX_LENGTH = 500
TWO_PLACES = Decimal("0.01")


def quantize_amount(value: Decimal) -> Decimal:
    """Return a 2-decimal canonical amount, rejecting excess precision."""
    # Reject more than two decimal places rather than silently rounding.
    exponent = value.as_tuple().exponent
    # exponent is an int for finite decimals; -2 means two decimal places.
    if isinstance(exponent, int) and exponent < -2:
        raise ValueError("amount must have at most 2 decimal places")
    return value.quantize(TWO_PLACES)


class ExpenseIn(BaseModel):
    """Request body for create (POST) and full update (PUT)."""

    model_config = ConfigDict(extra="forbid")

    amount: Decimal
    category: str
    date: date_type
    note: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def _validate_amount(cls, v: Decimal) -> Decimal:
        try:
            value = Decimal(v)
        except (InvalidOperation, TypeError, ValueError) as exc:  # pragma: no cover
            raise ValueError("amount must be numeric") from exc
        if value <= 0:
            raise ValueError("amount must be greater than 0")
        return quantize_amount(value)

    @field_validator("category")
    @classmethod
    def _validate_category(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("category must not be empty")
        return trimmed

    @field_validator("note")
    @classmethod
    def _validate_note(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) > NOTE_MAX_LENGTH:
            raise ValueError(f"note must be at most {NOTE_MAX_LENGTH} characters")
        return v


class ExpenseOut(BaseModel):
    """Full expense record returned to clients."""

    model_config = ConfigDict(extra="forbid")

    id: int
    amount: Decimal
    category: str
    date: date_type
    note: Optional[str] = None
    created_at: datetime


class CategoryTotal(BaseModel):
    """A single category total line within a monthly summary."""

    model_config = ConfigDict(extra="forbid")

    category: str
    total: Decimal


class MonthlySummaryOut(BaseModel):
    """Monthly spending summary grouped by category (FR-014/FR-015)."""

    model_config = ConfigDict(extra="forbid")

    year: int
    month: int
    total: Decimal
    by_category: list[CategoryTotal]
