"""Service layer: business rules and orchestration.

Performs cross-field validation (date-range ordering, month validity) and
existence checks, raising domain errors (`NotFoundError`,
`DomainValidationError`). It is independent of HTTP and owns no SQL.
"""

from __future__ import annotations

import sqlite3
from datetime import date as date_type
from decimal import Decimal
from typing import Any, Optional

from . import repository
from .errors import DomainValidationError, NotFoundError


def _validate_month(year: int, month: int) -> None:
    if month < 1 or month > 12:
        raise DomainValidationError("month must be between 1 and 12")
    if year < 1:
        raise DomainValidationError("year must be a positive integer")


def create_expense(
    conn: sqlite3.Connection,
    *,
    amount: Decimal,
    category: str,
    date: date_type,
    note: Optional[str],
) -> dict[str, Any]:
    """Create an expense (FR-001)."""
    return repository.create_expense(
        conn, amount=amount, category=category, date=date, note=note
    )


def get_expense(conn: sqlite3.Connection, expense_id: int) -> dict[str, Any]:
    """Fetch one expense or raise NotFoundError (FR-006)."""
    expense = repository.get_expense(conn, expense_id)
    if expense is None:
        raise NotFoundError(f"Expense {expense_id} not found")
    return expense


def list_expenses(
    conn: sqlite3.Connection,
    *,
    category: Optional[str] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[dict[str, Any]]:
    """List expenses with validated filters (FR-007..FR-010)."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise DomainValidationError("start_date must not be after end_date")

    # Month filter requires both year and month together.
    if (year is None) != (month is None):
        raise DomainValidationError(
            "year and month must be provided together for the month filter"
        )
    if year is not None and month is not None:
        _validate_month(year, month)

    return repository.list_expenses(
        conn,
        category=category,
        start_date=start_date,
        end_date=end_date,
        year=year,
        month=month,
    )


def update_expense(
    conn: sqlite3.Connection,
    expense_id: int,
    *,
    amount: Decimal,
    category: str,
    date: date_type,
    note: Optional[str],
) -> dict[str, Any]:
    """Update an expense or raise NotFoundError (FR-011/FR-012)."""
    updated = repository.update_expense(
        conn,
        expense_id,
        amount=amount,
        category=category,
        date=date,
        note=note,
    )
    if updated is None:
        raise NotFoundError(f"Expense {expense_id} not found")
    return updated


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> None:
    """Delete an expense or raise NotFoundError (FR-013)."""
    if not repository.delete_expense(conn, expense_id):
        raise NotFoundError(f"Expense {expense_id} not found")


def monthly_summary(
    conn: sqlite3.Connection,
    *,
    year: int,
    month: int,
) -> dict[str, Any]:
    """Produce a monthly summary grouped by category (FR-014/FR-015)."""
    _validate_month(year, month)
    total, by_category = repository.monthly_summary(conn, year=year, month=month)
    return {
        "year": year,
        "month": month,
        "total": total,
        "by_category": by_category,
    }
