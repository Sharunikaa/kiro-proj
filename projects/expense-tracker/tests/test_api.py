"""End-to-end API tests for the Student Expense Tracker.

Covers all six endpoints with happy-path and failure-path cases, every
validation rule, and persistence across a fresh client (FR-016). Tests run
offline via ``fastapi.testclient.TestClient`` against an isolated temp-file
SQLite database per test (see ``conftest.py``).

Traceability tags in test docstrings map each test to FR-/US- identifiers.
"""

from __future__ import annotations

from decimal import Decimal

from conftest import _build_client, make_expense


# =====================================================================
# POST /expenses — create (US-001, FR-001, FR-005)
# =====================================================================


def test_create_expense_with_note_returns_201(client):
    """FR-001/US-001: create with all fields incl. note -> 201 with id."""
    resp = client.post(
        "/expenses",
        json={
            "amount": 12.50,
            "category": "Food",
            "date": "2026-01-15",
            "note": "Lunch with friends",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert isinstance(body["id"], int) and body["id"] >= 1
    assert Decimal(str(body["amount"])) == Decimal("12.50")
    assert body["category"] == "Food"
    assert body["date"] == "2026-01-15"
    assert body["note"] == "Lunch with friends"
    assert body["created_at"]  # non-empty ISO timestamp


def test_create_expense_without_note_returns_201_note_null(client):
    """FR-005/US-001: note is optional; absence stored as null."""
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Transport", "date": "2026-01-10"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["note"] is None


def test_create_expense_trims_category(client):
    """FR-003: category stored trimmed of surrounding whitespace."""
    body = make_expense(client, category="  Groceries  ")
    assert body["category"] == "Groceries"


# =====================================================================
# POST /expenses — validation failures -> 422 (FR-002..FR-005)
# =====================================================================


def test_create_missing_amount_422(client):
    """FR-002: missing amount -> 422."""
    resp = client.post(
        "/expenses", json={"category": "Food", "date": "2026-01-15"}
    )
    assert resp.status_code == 422, resp.text


def test_create_zero_amount_422(client):
    """FR-002: zero amount -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": 0, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_negative_amount_422(client):
    """FR-002: negative amount -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": -3.50, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_non_numeric_amount_422(client):
    """FR-002: non-numeric amount -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": "abc", "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_amount_more_than_two_decimals_422(client):
    """FR-002/arch: amount with >2 decimal places -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": 12.345, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_empty_category_422(client):
    """FR-003: empty category -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_whitespace_category_422(client):
    """FR-003: whitespace-only category -> 422 after trim."""
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "   ", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_create_missing_date_422(client):
    """FR-004: missing date -> 422."""
    resp = client.post(
        "/expenses", json={"amount": 5, "category": "Food"}
    )
    assert resp.status_code == 422, resp.text


def test_create_malformed_date_422(client):
    """FR-004: malformed/garbage date -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "not-a-date"},
    )
    assert resp.status_code == 422, resp.text


def test_create_impossible_calendar_date_422(client):
    """FR-004: impossible calendar date 2026-02-30 -> 422."""
    resp = client.post(
        "/expenses",
        json={"amount": 5, "category": "Food", "date": "2026-02-30"},
    )
    assert resp.status_code == 422, resp.text


def test_create_note_over_500_chars_422(client):
    """FR-005/arch: note longer than 500 chars -> 422."""
    resp = client.post(
        "/expenses",
        json={
            "amount": 5,
            "category": "Food",
            "date": "2026-01-15",
            "note": "x" * 501,
        },
    )
    assert resp.status_code == 422, resp.text


def test_create_note_exactly_500_chars_ok(client):
    """FR-005/arch boundary: note of exactly 500 chars accepted."""
    resp = client.post(
        "/expenses",
        json={
            "amount": 5,
            "category": "Food",
            "date": "2026-01-15",
            "note": "x" * 500,
        },
    )
    assert resp.status_code == 201, resp.text


def test_create_unknown_extra_field_422(client):
    """arch (extra='forbid'): unknown field -> 422."""
    resp = client.post(
        "/expenses",
        json={
            "amount": 5,
            "category": "Food",
            "date": "2026-01-15",
            "currency": "USD",
        },
    )
    assert resp.status_code == 422, resp.text


# =====================================================================
# GET /expenses/{id} — found / not-found (FR-006, US-002)
# =====================================================================


def test_get_expense_found_200(client):
    """FR-006/US-002: fetch an existing expense -> 200 with all fields."""
    created = make_expense(client, note="Coffee")
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["category"] == created["category"]
    assert body["note"] == "Coffee"


def test_get_expense_not_found_404(client):
    """FR-006/US-002: fetch a non-existent id -> 404 with detail."""
    resp = client.get("/expenses/999999")
    assert resp.status_code == 404, resp.text
    assert "detail" in resp.json()


def test_get_expense_non_integer_id_422(client):
    """arch: non-integer id path param -> 422."""
    resp = client.get("/expenses/abc")
    assert resp.status_code == 422, resp.text


# =====================================================================
# GET /expenses — list & filter (FR-007..FR-010, US-003)
# =====================================================================


def test_list_all_expenses_200(client):
    """FR-007/US-003: list with no filters returns all expenses."""
    make_expense(client, category="Food", date="2026-01-01")
    make_expense(client, category="Books", date="2026-01-02")
    resp = client.get("/expenses")
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2


def test_list_filter_by_category(client):
    """FR-008/US-003: filter by category returns only that category."""
    make_expense(client, category="Food", date="2026-01-01")
    make_expense(client, category="Books", date="2026-01-02")
    make_expense(client, category="Food", date="2026-01-03")
    resp = client.get("/expenses", params={"category": "Food"})
    assert resp.status_code == 200, resp.text
    cats = {e["category"] for e in resp.json()}
    assert cats == {"Food"}
    assert len(resp.json()) == 2


def test_list_filter_date_range_inclusive(client):
    """FR-009/US-003: date range filter is inclusive of both boundaries."""
    make_expense(client, date="2026-01-01")
    make_expense(client, date="2026-01-15")
    make_expense(client, date="2026-01-31")
    make_expense(client, date="2026-02-01")
    resp = client.get(
        "/expenses",
        params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
    )
    assert resp.status_code == 200, resp.text
    dates = sorted(e["date"] for e in resp.json())
    assert dates == ["2026-01-01", "2026-01-15", "2026-01-31"]


def test_list_filter_by_month(client):
    """FR-010/US-003: month filter returns only that month's expenses."""
    make_expense(client, date="2026-01-10")
    make_expense(client, date="2026-01-20")
    make_expense(client, date="2026-02-05")
    resp = client.get("/expenses", params={"year": 2026, "month": 1})
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 2
    assert all(e["date"].startswith("2026-01") for e in resp.json())


def test_list_empty_result_returns_empty_list(client):
    """FR-007/US-003: a filter matching nothing returns [] not an error."""
    make_expense(client, category="Food")
    resp = client.get("/expenses", params={"category": "Nonexistent"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_list_start_date_after_end_date_422(client):
    """FR-009/US-003: start_date > end_date -> 422."""
    resp = client.get(
        "/expenses",
        params={"start_date": "2026-03-01", "end_date": "2026-01-01"},
    )
    assert resp.status_code == 422, resp.text


def test_list_month_without_year_422(client):
    """FR-010/US-003: month supplied without year -> 422."""
    resp = client.get("/expenses", params={"month": 1})
    assert resp.status_code == 422, resp.text


def test_list_year_without_month_422(client):
    """FR-010/US-003: year supplied without month -> 422."""
    resp = client.get("/expenses", params={"year": 2026})
    assert resp.status_code == 422, resp.text


def test_list_malformed_date_filter_422(client):
    """US-003: malformed date filter value -> 422."""
    resp = client.get("/expenses", params={"start_date": "13/01/2026"})
    assert resp.status_code == 422, resp.text


def test_list_invalid_month_value_422(client):
    """FR-010: out-of-range month value (13) -> 422."""
    resp = client.get("/expenses", params={"year": 2026, "month": 13})
    assert resp.status_code == 422, resp.text


# =====================================================================
# PUT /expenses/{id} — update (FR-011, FR-012, US-004)
# =====================================================================


def test_update_expense_200(client):
    """FR-011/US-004: update an existing expense persists changes."""
    created = make_expense(client, category="Food", note="old")
    resp = client.put(
        f"/expenses/{created['id']}",
        json={
            "amount": 99.99,
            "category": "Dining",
            "date": "2026-03-03",
            "note": "new",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(str(body["amount"])) == Decimal("99.99")
    assert body["category"] == "Dining"
    assert body["date"] == "2026-03-03"
    assert body["note"] == "new"
    # Confirm persisted
    again = client.get(f"/expenses/{created['id']}").json()
    assert again["category"] == "Dining"


def test_update_expense_not_found_404(client):
    """FR-011/US-004: updating a non-existent expense -> 404."""
    resp = client.put(
        "/expenses/999999",
        json={"amount": 5, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 404, resp.text


def test_update_invalid_amount_422(client):
    """FR-012/US-004: update with invalid amount -> 422 (same rules)."""
    created = make_expense(client)
    resp = client.put(
        f"/expenses/{created['id']}",
        json={"amount": -1, "category": "Food", "date": "2026-01-15"},
    )
    assert resp.status_code == 422, resp.text


def test_update_invalid_date_422(client):
    """FR-012/US-004: update with impossible date -> 422."""
    created = make_expense(client)
    resp = client.put(
        f"/expenses/{created['id']}",
        json={"amount": 5, "category": "Food", "date": "2026-02-30"},
    )
    assert resp.status_code == 422, resp.text


def test_update_unknown_field_422(client):
    """FR-012/arch: update with unknown extra field -> 422."""
    created = make_expense(client)
    resp = client.put(
        f"/expenses/{created['id']}",
        json={
            "amount": 5,
            "category": "Food",
            "date": "2026-01-15",
            "bogus": True,
        },
    )
    assert resp.status_code == 422, resp.text


# =====================================================================
# DELETE /expenses/{id} (FR-013, US-005)
# =====================================================================


def test_delete_expense_204_then_get_404(client):
    """FR-013/US-005: delete existing -> 204; subsequent get -> 404."""
    created = make_expense(client)
    resp = client.delete(f"/expenses/{created['id']}")
    assert resp.status_code == 204, resp.text
    assert resp.content == b""
    follow = client.get(f"/expenses/{created['id']}")
    assert follow.status_code == 404, follow.text


def test_delete_missing_expense_404(client):
    """FR-013/US-005: deleting a non-existent expense -> 404."""
    resp = client.delete("/expenses/999999")
    assert resp.status_code == 404, resp.text


# =====================================================================
# GET /summary/monthly (FR-014, FR-015, US-006)
# =====================================================================


def test_monthly_summary_totals_by_category_200(client):
    """FR-014/US-006: per-category totals correct and grand total == sum."""
    make_expense(client, amount=10.00, category="Food", date="2026-01-05")
    make_expense(client, amount=5.50, category="Food", date="2026-01-06")
    make_expense(client, amount=20.00, category="Books", date="2026-01-07")
    # Different month, must be excluded.
    make_expense(client, amount=100.00, category="Food", date="2026-02-01")

    resp = client.get("/summary/monthly", params={"year": 2026, "month": 1})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["year"] == 2026 and body["month"] == 1

    by_cat = {c["category"]: Decimal(str(c["total"])) for c in body["by_category"]}
    assert by_cat["Food"] == Decimal("15.50")
    assert by_cat["Books"] == Decimal("20.00")

    grand = Decimal(str(body["total"]))
    assert grand == Decimal("35.50")
    # Grand total equals the sum of category totals (FR-014).
    assert grand == sum(by_cat.values())


def test_monthly_summary_empty_month_zero(client):
    """FR-015/US-006: month with no expenses -> total 0, by_category []."""
    resp = client.get("/summary/monthly", params={"year": 2030, "month": 6})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(str(body["total"])) == Decimal("0")
    assert body["by_category"] == []


def test_monthly_summary_invalid_month_422(client):
    """US-006: invalid month value (13) -> 422."""
    resp = client.get("/summary/monthly", params={"year": 2026, "month": 13})
    assert resp.status_code == 422, resp.text


def test_monthly_summary_missing_month_422(client):
    """FR-014/US-006: missing required month -> 422."""
    resp = client.get("/summary/monthly", params={"year": 2026})
    assert resp.status_code == 422, resp.text


def test_monthly_summary_missing_year_422(client):
    """FR-014/US-006: missing required year -> 422."""
    resp = client.get("/summary/monthly", params={"month": 1})
    assert resp.status_code == 422, resp.text


# =====================================================================
# Persistence across a fresh client on the same file DB (FR-016, US-007)
# =====================================================================


def test_persistence_across_fresh_client(db_file):
    """FR-016/US-007: data created in one client survives a new client.

    Uses the same temp *file* DB with two independently constructed apps,
    simulating an application restart.
    """
    with _build_client(db_file) as c1:
        created = c1.post(
            "/expenses",
            json={"amount": 42.00, "category": "Rent", "date": "2026-01-01"},
        )
        assert created.status_code == 201, created.text
        expense_id = created.json()["id"]

    # Fresh app/client on the same DB file == restart.
    with _build_client(db_file) as c2:
        resp = c2.get(f"/expenses/{expense_id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["category"] == "Rent"
        assert Decimal(str(body["amount"])) == Decimal("42.00")
