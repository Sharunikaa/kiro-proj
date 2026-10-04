"""Data access layer: parameterized SQLite CRUD and aggregation.

All SQL is parameterized (never string-concatenated with user values).
Amounts are stored as canonical 2-decimal TEXT and returned as `Decimal`
to avoid binary float drift.
"""

from __future__ import annotations

import sqlite3
from datetime import date as date_type
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

TWO_PLACES = Decimal("0.01")


def _canonical_amount(amount: Decimal) -> str:
    """Serialize a Decimal to a canonical 2-decimal string for storage."""
    return str(amount.quantize(TWO_PLACES))


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Map a DB row to a dict with typed amount/date/created_at values."""
    return {
        "id": row["id"],
        "amount": Decimal(row["amount"]),
        "category": row["category"],
        "date": date_type.fromisoformat(row["date"]),
        "note": row["note"],
        "created_at": datetime.fromisoformat(row["created_at"]),
    }


def create_expense(
    conn: sqlite3.Connection,
    *,
    amount: Decimal,
    category: str,
    date: date_type,
    note: Optional[str],
) -> dict[str, Any]:
    """Insert a new expense and return the full stored record (FR-001)."""
    created_at = datetime.now(timezone.utc)
    cur = conn.execute(
        """
        INSERT INTO expenses (amount, category, date, note, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            _canonical_amount(amount),
            category,
            date.isoformat(),
            note,
            created_at.isoformat(),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    created = get_expense(conn, new_id)
    assert created is not None  # just inserted
    return created


def get_expense(conn: sqlite3.Connection, expense_id: int) -> Optional[dict[str, Any]]:
    """Return a single expense by id, or None if absent (FR-006)."""
    row = conn.execute(
        "SELECT id, amount, category, date, note, created_at "
        "FROM expenses WHERE id = ?",
        (expense_id,),
    ).fetchone()
    return _row_to_dict(row) if row is not None else None


def list_expenses(
    conn: sqlite3.Connection,
    *,
    category: Optional[str] = None,
    start_date: Optional[date_type] = None,
    end_date: Optional[date_type] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> list[dict[str, Any]]:
    """List expenses with optional AND-combined filters (FR-007..FR-010).

    Filters are applied with parameterized clauses only.
    """
    clauses: list[str] = []
    params: list[Any] = []

    if category is not None:
        clauses.append("category = ?")
        params.append(category)

    if start_date is not None:
        clauses.append("date >= ?")
        params.append(start_date.isoformat())

    if end_date is not None:
        clauses.append("date <= ?")
        params.append(end_date.isoformat())

    if year is not None and month is not None:
        # Prefix match on canonical YYYY-MM for the month filter.
        prefix = f"{year:04d}-{month:02d}"
        clauses.append("substr(date, 1, 7) = ?")
        params.append(prefix)

    sql = "SELECT id, amount, category, date, note, created_at FROM expenses"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date ASC, id ASC"

    rows = conn.execute(sql, tuple(params)).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_expense(
    conn: sqlite3.Connection,
    expense_id: int,
    *,
    amount: Decimal,
    category: str,
    date: date_type,
    note: Optional[str],
) -> Optional[dict[str, Any]]:
    """Full replacement of mutable fields; return updated record or None.

    Returns None when the id does not exist (FR-011).
    """
    cur = conn.execute(
        """
        UPDATE expenses
           SET amount = ?, category = ?, date = ?, note = ?
         WHERE id = ?
        """,
        (
            _canonical_amount(amount),
            category,
            date.isoformat(),
            note,
            expense_id,
        ),
    )
    conn.commit()
    if cur.rowcount == 0:
        return None
    return get_expense(conn, expense_id)


def delete_expense(conn: sqlite3.Connection, expense_id: int) -> bool:
    """Delete an expense; return True if a row was removed (FR-013)."""
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    return cur.rowcount > 0


def monthly_summary(
    conn: sqlite3.Connection,
    *,
    year: int,
    month: int,
) -> tuple[Decimal, list[dict[str, Any]]]:
    """Return (grand_total, per-category totals) for a month (FR-014/FR-015).

    Totals are computed in Python with `Decimal` to avoid float drift.
    """
    prefix = f"{year:04d}-{month:02d}"
    rows = conn.execute(
        """
        SELECT category, amount
          FROM expenses
         WHERE substr(date, 1, 7) = ?
        """,
        (prefix,),
    ).fetchall()

    totals: dict[str, Decimal] = {}
    grand_total = Decimal("0.00")
    for row in rows:
        amt = Decimal(row["amount"])
        grand_total += amt
        totals[row["category"]] = totals.get(row["category"], Decimal("0.00")) + amt

    by_category = [
        {"category": cat, "total": total.quantize(TWO_PLACES)}
        for cat, total in sorted(totals.items())
    ]
    return grand_total.quantize(TWO_PLACES), by_category
