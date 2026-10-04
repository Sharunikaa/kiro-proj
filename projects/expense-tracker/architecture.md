<!--
artifact: architecture.md
created_by: software-architect
created_at: 2026-10-04T20:45:40+05:30
status: draft
version: 1
related: requirements.md (FR-001..FR-017, US-001..US-007)
-->

# Student Expense Tracker — Architecture

## 1. Overview

A single-process **layered monolith** exposing a RESTful JSON API built with
**FastAPI** (Python 3.11+), persisting to a local **SQLite** database via the
standard-library `sqlite3` driver using **parameterized queries only**. The
design follows a strict three-layer separation — **Routes/API → Service →
Data** — so business rules are testable independently of HTTP and storage.
Request/response validation is handled by **Pydantic v2** models. No ORM is
required for an MVP of this size; the data layer is a thin, typed repository
over `sqlite3`.

## 2. Components and responsibilities

| Component | Module (suggested) | Responsibility |
|---|---|---|
| App factory | `src/main.py` | Create the FastAPI app, wire routers, initialize the DB on startup (`init_db`). |
| Config | `src/config.py` | Read `DATABASE_PATH` (and similar) from environment variables; provide defaults. No hardcoded secrets. |
| API schemas | `src/schemas.py` | Pydantic models for request bodies, query params, and responses; enforce field-level validation rules. |
| Routes/API | `src/routes.py` | Define HTTP endpoints, bind path/query/body to schemas, translate service results and domain errors into HTTP responses. |
| Service | `src/service.py` | Business logic: cross-field validation (date-range ordering, month validity), orchestrate persistence, raise domain errors (`NotFoundError`, `ValidationError`). |
| Data/Repository | `src/repository.py` | CRUD + aggregation over SQLite using parameterized SQL; row↔dict mapping. Owns all SQL. |
| DB bootstrap | `src/db.py` | Connection factory and schema creation (`init_db`), enforce `PRAGMA foreign_keys`/row factory. |
| Domain errors | `src/errors.py` | `NotFoundError`, `DomainValidationError` used by the service and mapped by routes. |

## 3. Layering and request flow

```
HTTP client
   │  JSON request
   ▼
Routes/API (FastAPI)      ── Pydantic validates shape & field rules (422 on failure)
   │  typed DTOs
   ▼
Service                   ── business rules: amount>0, trimmed category, date-range order,
   │  validated domain       month range; raises NotFoundError / DomainValidationError
   ▼
Data/Repository (sqlite3) ── parameterized SQL, returns rows/dicts
   │
   ▼
SQLite file (DATABASE_PATH)
```

Flow details:
1. **Routes** parse and validate the request via Pydantic. Pure shape/field
   errors return **422** automatically.
2. Routes call a **Service** function with validated values.
3. **Service** performs cross-field and existence checks. Missing entities
   raise `NotFoundError`; semantic violations raise `DomainValidationError`.
4. Service calls the **Repository**, which executes parameterized SQL and
   returns plain dict rows.
5. Routes serialize the result via a response schema. An exception handler maps
   `NotFoundError → 404` and `DomainValidationError → 422` with a consistent
   error body.

**Error body shape** (all non-2xx): `{"detail": "<human-readable message>"}`
(FastAPI's default `detail` convention; validation errors keep FastAPI's
structured 422 body).

## 4. API design

Base path: none (routes mounted at root). All request/response bodies are JSON.
`<id>` is an integer path parameter.

| # | Method | Path | Request (body / params) | Success response | Error cases |
|---|---|---|---|---|---|
| 1 | POST | `/expenses` | Body: `{amount: number, category: string, date: "YYYY-MM-DD", note?: string}` | `201` → `ExpenseOut` (full record incl. `id`, `created_at`) | `422` amount ≤ 0 / non-numeric / >2 decimals; empty category; invalid date; note > 500 chars (FR-002..FR-005) |
| 2 | GET | `/expenses/{id}` | Path: `id` | `200` → `ExpenseOut` | `404` not found (FR-006); `422` non-integer id |
| 3 | GET | `/expenses` | Query (all optional): `category: string`, `start_date: YYYY-MM-DD`, `end_date: YYYY-MM-DD`, `year: int`, `month: int(1-12)` | `200` → `[ExpenseOut]` (empty list if no match) | `422` malformed date; `start_date > end_date`; invalid month/year; mixing `month` with explicit range when conflicting (FR-007..FR-010) |
| 4 | PUT | `/expenses/{id}` | Path: `id`; Body: same schema and rules as create (full replacement of mutable fields) | `200` → updated `ExpenseOut` | `404` not found (FR-011); `422` same validation as create (FR-012) |
| 5 | DELETE | `/expenses/{id}` | Path: `id` | `204` No Content | `404` not found (FR-013); `422` non-integer id |
| 6 | GET | `/summary/monthly` | Query (required): `year: int`, `month: int(1-12)` | `200` → `MonthlySummaryOut` | `422` missing/invalid year or month (FR-014); empty-but-valid month returns zeroed summary, not an error (FR-015) |

### Response schemas

`ExpenseOut`:
```
{ "id": int, "amount": number, "category": string, "date": "YYYY-MM-DD",
  "note": string | null, "created_at": "ISO-8601 datetime" }
```

`MonthlySummaryOut`:
```
{ "year": int, "month": int,
  "total": number,
  "by_category": [ { "category": string, "total": number } ] }
```
For a month with no expenses: `total = 0`, `by_category = []` (FR-015).

### Filter semantics (resolved decisions)

- **Date range is inclusive** of both `start_date` and `end_date`
  (SQL `date BETWEEN :start AND :end`), matching US-003 "inclusive of
  boundaries".
- If both `start_date` and `end_date` are present and `start_date > end_date`,
  return **422** (service-level check).
- `year`+`month` filter selects all expenses whose `date` falls in that month
  (string prefix `YYYY-MM` compare on the stored ISO date). If `month` is given
  without `year` (or vice versa), return **422** (both required together for the
  month filter).
- Filters combine with logical **AND** when multiple are supplied.

## 5. Data model

### Entity: `Expense`

| Field | Type (Python / API) | SQLite type | Constraints |
|---|---|---|---|
| `id` | `int` | `INTEGER` | PRIMARY KEY AUTOINCREMENT |
| `amount` | `Decimal`→serialized as JSON number | `TEXT` (store canonical `"0.00"` string) | NOT NULL; `> 0`; exactly 2-decimal precision |
| `category` | `str` | `TEXT` | NOT NULL; non-empty after trim; stored trimmed |
| `date` | `datetime.date` (`YYYY-MM-DD`) | `TEXT` | NOT NULL; valid ISO calendar date |
| `note` | `str \| None` | `TEXT` | NULLable; max length 500 chars |
| `created_at` | `datetime` (UTC) | `TEXT` | NOT NULL; set on insert (ISO-8601) |

**Amount precision (resolved):** amount must be a positive currency value with
**at most two decimal places and value strictly greater than 0**. Validation
quantizes to two decimals using `Decimal`; values with more than two decimal
places are rejected with **422**. Store as a canonical 2-decimal string in
`TEXT` to avoid binary float drift; parse back to `Decimal` and serialize as a
JSON number in responses. Aggregation sums use `Decimal`/`SUM(CAST(amount AS
REAL))` with rounding to 2 decimals on output.

**Note length (resolved):** maximum **500 characters**; empty/absent note is
stored as `NULL` (FR-005).

**Unknown-field handling (resolved):** request bodies use Pydantic models
configured with `extra="forbid"`, so unknown/extra fields are **rejected with
422**. This gives students clear feedback on typos rather than silently
dropping data.

### SQLite table definition

```sql
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amount     TEXT    NOT NULL,                 -- canonical "0.00" string, > 0
    category   TEXT    NOT NULL,                 -- trimmed, non-empty
    date       TEXT    NOT NULL,                 -- ISO 'YYYY-MM-DD'
    note       TEXT,                             -- nullable, <= 500 chars
    created_at TEXT    NOT NULL                  -- ISO-8601 timestamp
);

CREATE INDEX IF NOT EXISTS idx_expenses_date     ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
```

The index on `date` supports range and month filters; the index on `category`
supports category filtering and summary grouping (FR-008, FR-009, FR-010,
FR-014).

## 6. Dependencies (minimal)

Runtime (`requirements.txt`):
- `fastapi` — web framework and request validation integration.
- `uvicorn` — ASGI server to run the app.
- `pydantic` — v2, bundled with FastAPI; request/response models.

Standard library (no dependency): `sqlite3`, `decimal`, `datetime`.

Test / dev:
- `pytest` — test runner.
- `httpx` — drives FastAPI via `TestClient`/`ASGITransport` for API tests
  without network access.

No ORM, no migration tool, no external DB server (keeps the Tester's toolchain
single and offline, per technology steering).

## 7. Technical risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Floating-point drift on currency sums | Incorrect totals/summaries | Store amount as 2-decimal `TEXT`; compute with `Decimal`; round output to 2 places. |
| SQL injection via filter/query values | Security | Parameterized SQL only; never string-concatenate (coding standard). |
| Invalid-but-shaped dates (e.g., `2026-02-30`) | Bad data persisted | Parse with `datetime.date.fromisoformat`; reject invalid calendar dates at the schema layer (422) (FR-004). |
| Date stored as string → range correctness | Wrong filter results | Enforce canonical zero-padded `YYYY-MM-DD`; lexical compare equals chronological compare for this format; index on `date`. |
| Concurrent writes / locking | Rare for single-user MVP | SQLite default locking is sufficient; use short-lived connections per request; `check_same_thread=False` with per-request connection. |
| DB file path misconfiguration | App fails to start / writes to wrong place | `DATABASE_PATH` from env with sane default; `init_db` on startup (FR-016). |
| Silent data loss from client typos | Student confusion | `extra="forbid"` rejects unknown fields with a clear 422. |

## 8. Traceability

| Requirement | Covered by |
|---|---|
| FR-001 create expense + unique id | Endpoint 1 (POST `/expenses`); `service.create_expense`; `id` PK |
| FR-002 reject bad amount | `schemas.ExpenseIn.amount` validator (>0, ≤2 decimals) → 422 |
| FR-003 reject empty category | `schemas.ExpenseIn.category` validator (trim, non-empty) → 422 |
| FR-004 reject invalid date | `schemas.ExpenseIn.date` (`date` type / `fromisoformat`) → 422 |
| FR-005 optional note | `schemas.ExpenseIn.note` Optional, nullable column |
| FR-006 get by id / not-found | Endpoint 2 (GET `/expenses/{id}`); `NotFoundError`→404 |
| FR-007 list all | Endpoint 3 (GET `/expenses`, no filters) |
| FR-008 filter by category | Endpoint 3 `category` param; `repository.list_expenses` WHERE category |
| FR-009 filter by date range (inclusive) | Endpoint 3 `start_date`/`end_date`; `BETWEEN`; order check in service |
| FR-010 filter by month | Endpoint 3 `year`+`month`; prefix match on `date` |
| FR-011 update + not-found | Endpoint 4 (PUT `/expenses/{id}`); `NotFoundError`→404 |
| FR-012 same validation on update | Endpoint 4 reuses `ExpenseIn` schema + service checks |
| FR-013 delete + not-found | Endpoint 5 (DELETE `/expenses/{id}`); 204 / 404 |
| FR-014 monthly summary by category | Endpoint 6 (GET `/summary/monthly`); `repository.monthly_summary` GROUP BY category |
| FR-015 empty summary for empty month | Endpoint 6 returns `total=0`, `by_category=[]` |
| FR-016 persistence across restarts | SQLite file at `DATABASE_PATH`; `db.init_db`; `repository` persists |
| FR-017 meaningful errors + status codes | `errors.py` + exception handlers (404/422), consistent `{"detail"}` body |
| US-001 add expense | Endpoint 1 + schema validators |
| US-002 view single | Endpoint 2 |
| US-003 list & filter | Endpoint 3 (category / inclusive range / month; empty list on no match) |
| US-004 update | Endpoint 4 |
| US-005 delete | Endpoint 5 |
| US-006 monthly summary | Endpoint 6 |
| US-007 persistence | SQLite data layer (`db.py`, `repository.py`) |

### Resolved open decisions (from requirements "to be set during design")
- **Amount precision:** positive, strictly `> 0`, at most **2 decimal places**;
  stored as canonical 2-decimal string; excess precision → 422.
- **Note max length:** **500 characters**.
- **Date-range inclusivity:** **inclusive** of both boundaries (`BETWEEN`).
- **Unknown/extra fields:** **rejected** (Pydantic `extra="forbid"`, 422).
