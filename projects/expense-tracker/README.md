<!--
artifact: README.md
created_by: documentation-agent
created_at: 2026-10-04T21:54:32+05:30
status: draft
version: 1
related: requirements.md, architecture.md, tasks.md, test-report.md, security-review.md, src/
-->

# Student Expense Tracker

A simple, reliable backend API that helps budget-conscious college students
record and understand their personal spending. A student can add an expense
(amount, category, date, and an optional note), retrieve and filter their
recorded expenses, update or delete entries, and view a monthly spending
summary broken down by category.

## Overview

The Student Expense Tracker is a single-process REST API built with Python and
FastAPI, persisting to a local SQLite database. It is a **single-user MVP** —
authentication, multi-user accounts, budgets, and reporting/export are out of
scope by design.

### Target users

- **College students** managing limited budgets who want to log day-to-day
  spending and review monthly totals.

## Features

- **Create an expense** with amount, category, date, and an optional note
  (`POST /expenses`).
- **Retrieve a single expense** by its identifier (`GET /expenses/{id}`).
- **List and filter expenses** by category, inclusive date range, and/or a
  specific year+month (`GET /expenses`).
- **Update an existing expense** with the same validation rules as create
  (`PUT /expenses/{id}`).
- **Delete an expense** by its identifier (`DELETE /expenses/{id}`).
- **Monthly summary** of spending totalled by category for a given year/month
  (`GET /summary/monthly`).
- **Input validation** with meaningful error responses (422 for invalid input,
  404 for not-found) and durable local persistence in SQLite that survives
  restarts.

## Tech stack

- **Language:** Python 3.11+ (verified against the toolchain used for testing,
  Python 3.14.6)
- **Web framework:** FastAPI
- **Validation:** Pydantic v2
- **ASGI server:** Uvicorn
- **Database:** SQLite via the standard-library `sqlite3` driver
  (parameterized queries only; no ORM)
- **Testing:** pytest with httpx (FastAPI `TestClient`)

### Pinned dependencies

Runtime (`requirements.txt`):

```
fastapi==0.142.2
uvicorn==0.54.0
pydantic==2.13.5
```

Development / testing (`requirements-dev.txt`, which also includes
`-r requirements.txt`):

```
pytest==9.1.1
httpx==0.28.1
```

## Project structure

```
projects/expense-tracker/
├── src/
│   ├── __init__.py
│   ├── config.py        # Reads DATABASE_PATH from the environment (default: expenses.db)
│   ├── db.py            # SQLite connection factory + schema bootstrap (init_db / ensure_schema)
│   ├── errors.py        # Domain errors: NotFoundError (404), DomainValidationError (422)
│   ├── schemas.py       # Pydantic v2 models: ExpenseIn, ExpenseOut, CategoryTotal, MonthlySummaryOut
│   ├── repository.py    # Parameterized SQLite CRUD + monthly aggregation (owns all SQL)
│   ├── service.py       # Business rules: cross-field validation, existence checks
│   ├── routes.py        # The six HTTP endpoints + domain-error exception handlers
│   └── main.py          # App factory create_app(); module-level app = create_app()
├── tests/
│   ├── conftest.py      # Test fixtures (isolated temp-file SQLite per test)
│   └── test_api.py      # 42 API tests (happy-path + failure-path)
├── requirements.txt     # Pinned runtime dependencies
├── requirements-dev.txt # Pinned dev/test dependencies (includes runtime)
├── requirements.md      # Requirements & user stories
├── architecture.md      # Architecture, API & data design
├── tasks.md             # Implementation task breakdown
├── test-report.md       # Test run report (42/42 passing)
└── security-review.md   # Security review (PASS WITH FINDINGS)
```

## Setup & installation

All commands below are run from the `projects/expense-tracker` directory.

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   # .venv\Scripts\activate         # Windows (PowerShell: .venv\Scripts\Activate.ps1)
   ```

2. Install dependencies:

   ```bash
   # Runtime only (to run the app):
   pip install -r requirements.txt

   # Runtime + test tools (to run the test suite):
   pip install -r requirements-dev.txt
   ```

### Configuration

The database location is controlled by the `DATABASE_PATH` environment
variable, read in `src/config.py`:

- **Default:** `expenses.db` (a file created in the current working directory).
- **Ephemeral / testing:** set a temporary file path, or `:memory:` for an
  in-memory database (the app routes `:memory:` through a shared-cache in-memory
  database so data is consistent across requests for the process lifetime).

```bash
export DATABASE_PATH=expenses.db     # default
# export DATABASE_PATH=:memory:      # ephemeral, non-persistent
```

## Running the application

The FastAPI app is created by the factory `create_app()` in `src/main.py`,
which also exposes a module-level `app = create_app()`. Run it with Uvicorn
from the `projects/expense-tracker` directory:

```bash
uvicorn src.main:app --reload
```

- Interactive API docs (Swagger UI): http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

> **Localhost-only assumption.** This is a single-user MVP intended to run on
> the loopback interface. Per the security review (SEC-02/SEC-03), bind Uvicorn
> to `127.0.0.1` and do not expose the service or its SQLite database to a
> network. If the API is ever exposed beyond localhost, disable the interactive
> docs (`docs_url=None, redoc_url=None`) or place them behind authentication
> first.

## Running tests

Install the dev dependencies, then from the `projects/expense-tracker`
directory run:

```bash
python -m pytest -q
```

The suite contains **42 tests** and the latest run reported **42 passed, 0
failed, 0 skipped** (`42 passed, 4 warnings in 0.73s`; see `test-report.md`).
Tests run fully offline using FastAPI's `TestClient`, with each test isolated
via its own temp-file SQLite database. The 4 warnings are library-version
deprecation notices (Starlette/httpx) and do not affect correctness.

## API reference

Base path: none (routes are mounted at the root). All request/response bodies
are JSON. `{id}` is an integer path parameter. Non-2xx responses use a
consistent body: `{"detail": "<message>"}` (Pydantic validation 422s keep
FastAPI's structured body).

| Method | Path | Request | Success | Error cases |
|---|---|---|---|---|
| POST | `/expenses` | Body: `ExpenseIn` `{amount, category, date, note?}` | `201` → `ExpenseOut` | `422` amount ≤ 0 / non-numeric / > 2 decimals; empty/whitespace category; missing/invalid/impossible date; note > 500 chars; unknown field |
| GET | `/expenses/{id}` | Path: `id` | `200` → `ExpenseOut` | `404` not found; `422` non-integer id |
| GET | `/expenses` | Query (all optional): `category`, `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `year` (int), `month` (int 1–12) | `200` → `[ExpenseOut]` (empty list if no match) | `422` malformed date; `start_date > end_date`; `year`/`month` not supplied together; `month` out of 1–12 |
| PUT | `/expenses/{id}` | Path: `id`; Body: `ExpenseIn` (same rules as create) | `200` → updated `ExpenseOut` | `404` not found; `422` same validation as create |
| DELETE | `/expenses/{id}` | Path: `id` | `204` No Content | `404` not found; `422` non-integer id |
| GET | `/summary/monthly` | Query (required): `year` (int), `month` (int 1–12) | `200` → `MonthlySummaryOut` | `422` missing/invalid `year` or `month`; a valid but empty month returns a zeroed summary (not an error) |

### Request / response schemas

`ExpenseIn` (request body for create and update):

```json
{
  "amount": 12.50,
  "category": "Groceries",
  "date": "2026-10-04",
  "note": "weekly shop"
}
```

- `amount` — number, strictly `> 0`, at most 2 decimal places (excess
  precision → 422).
- `category` — non-empty string (trimmed; stored trimmed).
- `date` — valid ISO calendar date `YYYY-MM-DD` (e.g. `2026-02-30` is rejected).
- `note` — optional string, max 500 characters.
- Unknown/extra fields are rejected (`extra="forbid"`).

`ExpenseOut` (full record returned to clients):

```json
{
  "id": 1,
  "amount": 12.50,
  "category": "Groceries",
  "date": "2026-10-04",
  "note": "weekly shop",
  "created_at": "2026-10-04T16:30:00+00:00"
}
```

`MonthlySummaryOut`:

```json
{
  "year": 2026,
  "month": 10,
  "total": 42.50,
  "by_category": [
    { "category": "Groceries", "total": 30.00 },
    { "category": "Transport", "total": 12.50 }
  ]
}
```

For a valid month with no expenses: `total` is `0.00` and `by_category` is `[]`.

### Example requests

Create an expense:

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.50, "category": "Groceries", "date": "2026-10-04", "note": "weekly shop"}'
```

Create an expense without a note:

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 3.75, "category": "Coffee", "date": "2026-10-05"}'
```

List expenses filtered by category and date range:

```bash
curl "http://127.0.0.1:8000/expenses?category=Groceries&start_date=2026-10-01&end_date=2026-10-31"
```

Get the monthly summary:

```bash
curl "http://127.0.0.1:8000/summary/monthly?year=2026&month=10"
```

## Security considerations

The security review (`security-review.md`) status is **PASS WITH FINDINGS**.
The implementation uses parameterized SQL throughout, validates all input via
Pydantic with `extra="forbid"`, stores amounts as `Decimal` (no float drift),
reads configuration from the environment with no hardcoded secrets, and returns
safe, generic error messages.

- **SEC-01 (Medium) — FIXED.** Dependencies are now pinned
  (`fastapi==0.142.2`, `uvicorn==0.54.0`, `pydantic==2.13.5`;
  dev: `pytest==9.1.1`, `httpx==0.28.1`). A clean install from the pinned
  manifest was verified and the full suite passed 42/42.
- **SEC-02 / SEC-03 (Low) — localhost-only.** FastAPI's interactive docs
  (`/docs`, `/redoc`) are enabled by default, and nothing in the code enforces
  the network binding. For this MVP, bind Uvicorn to `127.0.0.1` and keep the
  SQLite database local. If exposing beyond loopback, disable the docs or gate
  them behind authentication.
- **SEC-04 (Info) — no authentication by design.** The MVP is single-user; no
  authn/authz is present. If multi-user support is ever added, introduce
  authentication and per-user data isolation before exposing the API.

See `security-review.md` for the full findings table and checklist.
