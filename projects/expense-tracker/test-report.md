<!--
artifact: test-report.md
created_by: tester
created_at: 2026-10-04T21:25:00+05:30
status: draft
version: 1
related: requirements.md (FR-001..FR-017, US-001..US-007), architecture.md
-->

# Student Expense Tracker — Test Report

## 1. Summary

| Metric | Count |
|---|---|
| Total | 42 |
| Passed | 42 |
| Failed | 0 |
| Skipped | 0 |

**Final pytest summary line (verbatim):**

```
42 passed, 4 warnings in 0.73s
```

Command: `projects/expense-tracker/.venv/bin/python -m pytest -q`
(run from `projects/expense-tracker`). Interpreter: Python 3.14.6; fastapi
0.142.2, pydantic 2.13.5, httpx 0.28.1, pytest 9.1.1.

All six endpoints and every validation rule are covered with both happy-path
and failure-path cases. Tests run fully offline using
`fastapi.testclient.TestClient`. Each test is isolated via a unique temp-file
SQLite database (`DATABASE_PATH` set before the app is built); the in-memory
keep-alive is reset per app build so no state leaks across tests. A dedicated
test exercises file persistence across a simulated restart (FR-016).

## 2. Per-test results

All tests reside in `tests/test_api.py` (fixtures in `tests/conftest.py`).

| # | Test | What it checks | Expected | Result |
|---|---|---|---|---|
| 1 | `test_create_expense_with_note_returns_201` | Create with amount/category/date/note | 201 + id, fields echoed | PASS |
| 2 | `test_create_expense_without_note_returns_201_note_null` | Note optional/absent | 201, note=null | PASS |
| 3 | `test_create_expense_trims_category` | Category stored trimmed | 201, "Groceries" | PASS |
| 4 | `test_create_missing_amount_422` | Missing amount rejected | 422 | PASS |
| 5 | `test_create_zero_amount_422` | Zero amount rejected | 422 | PASS |
| 6 | `test_create_negative_amount_422` | Negative amount rejected | 422 | PASS |
| 7 | `test_create_non_numeric_amount_422` | Non-numeric amount rejected | 422 | PASS |
| 8 | `test_create_amount_more_than_two_decimals_422` | >2 decimal amount rejected | 422 | PASS |
| 9 | `test_create_empty_category_422` | Empty category rejected | 422 | PASS |
| 10 | `test_create_whitespace_category_422` | Whitespace-only category rejected | 422 | PASS |
| 11 | `test_create_missing_date_422` | Missing date rejected | 422 | PASS |
| 12 | `test_create_malformed_date_422` | Garbage date string rejected | 422 | PASS |
| 13 | `test_create_impossible_calendar_date_422` | `2026-02-30` rejected | 422 | PASS |
| 14 | `test_create_note_over_500_chars_422` | Note > 500 chars rejected | 422 | PASS |
| 15 | `test_create_note_exactly_500_chars_ok` | Note == 500 chars accepted (boundary) | 201 | PASS |
| 16 | `test_create_unknown_extra_field_422` | Unknown field rejected (`extra=forbid`) | 422 | PASS |
| 17 | `test_get_expense_found_200` | Fetch existing expense | 200 + fields | PASS |
| 18 | `test_get_expense_not_found_404` | Fetch missing id | 404 + detail | PASS |
| 19 | `test_get_expense_non_integer_id_422` | Non-integer path id | 422 | PASS |
| 20 | `test_list_all_expenses_200` | List with no filters | 200, all rows | PASS |
| 21 | `test_list_filter_by_category` | Filter by category | 200, only that category | PASS |
| 22 | `test_list_filter_date_range_inclusive` | Inclusive date range | 200, boundaries included | PASS |
| 23 | `test_list_filter_by_month` | Year+month filter | 200, only that month | PASS |
| 24 | `test_list_empty_result_returns_empty_list` | No match returns [] | 200, `[]` | PASS |
| 25 | `test_list_start_date_after_end_date_422` | start_date > end_date | 422 | PASS |
| 26 | `test_list_month_without_year_422` | month without year | 422 | PASS |
| 27 | `test_list_year_without_month_422` | year without month | 422 | PASS |
| 28 | `test_list_malformed_date_filter_422` | Malformed filter date | 422 | PASS |
| 29 | `test_list_invalid_month_value_422` | month=13 filter | 422 | PASS |
| 30 | `test_update_expense_200` | Update existing + persisted | 200, changes persist | PASS |
| 31 | `test_update_expense_not_found_404` | Update missing id | 404 | PASS |
| 32 | `test_update_invalid_amount_422` | Update negative amount | 422 | PASS |
| 33 | `test_update_invalid_date_422` | Update impossible date | 422 | PASS |
| 34 | `test_update_unknown_field_422` | Update unknown field | 422 | PASS |
| 35 | `test_delete_expense_204_then_get_404` | Delete then re-fetch | 204, then 404 | PASS |
| 36 | `test_delete_missing_expense_404` | Delete missing id | 404 | PASS |
| 37 | `test_monthly_summary_totals_by_category_200` | Category totals + grand == sum | 200, correct totals | PASS |
| 38 | `test_monthly_summary_empty_month_zero` | Empty month | 200, total 0, by_category [] | PASS |
| 39 | `test_monthly_summary_invalid_month_422` | month=13 | 422 | PASS |
| 40 | `test_monthly_summary_missing_month_422` | Missing month | 422 | PASS |
| 41 | `test_monthly_summary_missing_year_422` | Missing year | 422 | PASS |
| 42 | `test_persistence_across_fresh_client` | Fresh client on same file DB | Data survives "restart" | PASS |

## 3. Failures

None. No test defects and no source defects were found; the suite is fully
green. `src/` was not modified (tester scope: `tests/` and `test-report.md`
only).

### Non-blocking warnings (informational, not failures)

The run emits 4 deprecation warnings from the installed library versions, none
of which affect correctness or test outcomes:

- `StarletteDeprecationWarning: Using 'httpx' with 'starlette.testclient' is
  deprecated; install 'httpx2' instead.` — from the test client import.
- `StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated.
  Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.` — triggered when the domain
  `DomainValidationError` handler returns 422 (`src/routes.py`).

These originate from Starlette's newer status-constant naming and the httpx
test transport. They are environment/library-version notices, not product
defects. Suggested (optional) follow-up for the developer, if desired: migrate
`status.HTTP_422_UNPROCESSABLE_ENTITY` references to the newer constant once the
pinned Starlette version standardizes it. No action required for the current
contract.

## 4. Coverage notes (FR / US mapping)

| Requirement | Covered by test(s) |
|---|---|
| FR-001 create + unique id | 1, 2, 3 |
| FR-002 reject bad amount (missing/zero/neg/non-numeric/>2dp) | 4, 5, 6, 7, 8 |
| FR-003 reject empty/whitespace category | 9, 10 (and 3 for trim) |
| FR-004 reject missing/invalid/impossible date | 11, 12, 13 |
| FR-005 optional note (+ max 500) | 2, 14, 15 |
| FR-006 get by id / not-found | 17, 18 (19 non-int id) |
| FR-007 list all | 20, 24 (empty) |
| FR-008 filter by category | 21 |
| FR-009 filter by date range (inclusive) + order check | 22, 25 |
| FR-010 filter by month (both required) + invalid month | 23, 26, 27, 29 |
| FR-011 update + not-found | 30, 31 |
| FR-012 same validation on update | 32, 33, 34 |
| FR-013 delete + not-found | 35, 36 |
| FR-014 monthly summary by category (total == sum) | 37, 40, 41 |
| FR-015 empty summary for empty month | 38 |
| FR-016 persistence across restarts | 42 |
| FR-017 meaningful errors + status codes | 18, 31, 36 (404 w/ detail); all 422 cases |
| US-001 add expense | 1, 2, 4–16 |
| US-002 view single | 17, 18 |
| US-003 list & filter | 20–29 |
| US-004 update | 30–34 |
| US-005 delete | 35, 36 |
| US-006 monthly summary | 37–41 |
| US-007 persistence | 42 |

Additional edge/boundary coverage beyond the minimum: 422 for malformed date
*filter* value (28), 422 for unknown extra field on both create (16) and update
(34), note length boundary at exactly 500 (15), and verification that the
monthly grand total equals the sum of per-category totals (37).

All functional requirements FR-001..FR-017 and user stories US-001..US-007 have
at least one happy-path and one failure-path (where applicable) test. No
requirement is left uncovered.
