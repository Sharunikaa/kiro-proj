<!--
artifact: tasks.md
created_by: developer
created_at: 2026-10-04T20:50:34+05:30
status: draft
version: 2
related: requirements.md (FR-001..FR-017, US-001..US-007), architecture.md
-->

# Student Expense Tracker — Implementation Tasks

Numbered implementation tasks for Phase 3 (Developer), mapped to functional
requirements (FR) and user stories (US). Implements the layered FastAPI +
`sqlite3` + Pydantic v2 design from `architecture.md`.

## 1. Project scaffolding & configuration

1. **Create package layout** under `src/` with `__init__.py` so the app imports
   cleanly. — Maps: architecture §2.
2. **Config module** (`src/config.py`): read `DATABASE_PATH` from the
   environment with a local-file default; no hardcoded secrets. — FR-016.
3. **Runtime dependencies** (`requirements.txt`): `fastapi`, `uvicorn`,
   `pydantic`. — architecture §6.

## 2. Persistence layer

4. **Connection factory** (`src/db.py`): `get_connection` with
   `sqlite3.Row` factory and `check_same_thread=False`. — architecture §7.
5. **Schema bootstrap** (`src/db.py` `init_db`): create `expenses` table and
   `idx_expenses_date` / `idx_expenses_category` indexes. — FR-016, FR-008/009/010/014.

## 3. Domain errors

6. **Error types** (`src/errors.py`): `NotFoundError` (→404),
   `DomainValidationError` (→422). — FR-017.

## 4. Validation schemas (Pydantic v2)

7. **`ExpenseIn`** (`src/schemas.py`): `amount` > 0 and ≤ 2 decimals via
   `Decimal`; `category` trimmed non-empty; `date` valid ISO calendar date;
   `note` optional ≤ 500 chars; `extra="forbid"`. — FR-002, FR-003, FR-004,
   FR-005; US-001.
8. **`ExpenseOut`** full record incl. `id`, `created_at`. — FR-001, US-002.
9. **`MonthlySummaryOut`** + `CategoryTotal`: `year`, `month`, `total`,
   `by_category`. — FR-014, FR-015, US-006.

## 5. Repository (parameterized SQL)

10. **`create_expense`**: insert; store `amount` as canonical 2-decimal TEXT;
    set `created_at`; return full record. — FR-001.
11. **`get_expense`**: fetch by id or `None`. — FR-006.
12. **`list_expenses`**: optional AND-combined filters — `category`,
    inclusive `start_date`/`end_date`, `year`+`month` prefix match; all
    parameterized. — FR-007, FR-008, FR-009, FR-010; US-003.
13. **`update_expense`**: full field replacement; `None` when id absent. — FR-011, FR-012.
14. **`delete_expense`**: delete by id; boolean removed flag. — FR-013.
15. **`monthly_summary`**: group totals by category using `Decimal`; grand
    total; empty month → zeroed. — FR-014, FR-015.

## 6. Service (business rules)

16. **`create_expense` / `get_expense` / `update_expense` / `delete_expense`**:
    orchestrate repository; raise `NotFoundError` on missing id. — FR-006,
    FR-011, FR-013; US-002, US-004, US-005.
17. **`list_expenses` rules**: reject `start_date > end_date`; require `year`
    and `month` together; validate month range. — FR-009, FR-010; US-003.
18. **`monthly_summary` rules**: validate `year`/`month`. — FR-014; US-006.

## 7. Routes (six endpoints) + error mapping

19. **POST `/expenses`** → 201 `ExpenseOut`. — FR-001; US-001.
20. **GET `/expenses/{id}`** → 200 / 404. — FR-006; US-002.
21. **GET `/expenses`** (filters) → 200 list (empty on no match). — FR-007..FR-010; US-003.
22. **PUT `/expenses/{id}`** → 200 / 404; same validation as create. — FR-011, FR-012; US-004.
23. **DELETE `/expenses/{id}`** → 204 / 404. — FR-013; US-005.
24. **GET `/summary/monthly`** (year, month required) → 200. — FR-014, FR-015; US-006.
25. **Exception handlers**: `NotFoundError`→404, `DomainValidationError`→422,
    consistent `{"detail": ...}` body. — FR-017.

## 8. Application factory

26. **`create_app`** (`src/main.py`): build FastAPI app, include router,
    register handlers, call `init_db` on startup. — FR-016; US-007.

## 9. Verification (developer gate)

27. **Syntax/import gate**: `python -m py_compile src/*.py` and an import check
    of `src.main`. Tests are authored by the Tester stage, not here.

## Traceability summary

| Requirement | Task(s) |
|---|---|
| FR-001 | 7, 8, 10, 19 |
| FR-002 | 7 |
| FR-003 | 7 |
| FR-004 | 7 |
| FR-005 | 7 |
| FR-006 | 11, 16, 20 |
| FR-007 | 12, 21 |
| FR-008 | 5, 12, 21 |
| FR-009 | 12, 17, 21 |
| FR-010 | 12, 17, 21 |
| FR-011 | 13, 16, 22 |
| FR-012 | 7, 22 |
| FR-013 | 14, 16, 23 |
| FR-014 | 9, 15, 18, 24 |
| FR-015 | 9, 15, 24 |
| FR-016 | 2, 5, 26 |
| FR-017 | 6, 25 |
| US-001..US-007 | 7–26 (see per-task mapping above) |

## Fixes

- **Schema-bootstrap defect (schema not created under TestClient / in-memory
  SQLite).** The app previously created the schema via the deprecated
  `@app.on_event("startup")` handler. Under FastAPI's `TestClient` used without
  a context manager (as the Tester uses it), the startup event does not fire,
  so `init_db()` never ran and every request failed with
  `sqlite3.OperationalError: no such table: expenses`.
  - `src/main.py`: replaced `@app.on_event("startup")` with a
    `contextlib.asynccontextmanager` lifespan handler passed as
    `FastAPI(lifespan=...)`, still calling `db.init_db()` so normal `uvicorn`
    runs initialize the file DB.
  - `src/db.py`: added idempotent `ensure_schema(conn)` (the
    `CREATE TABLE/INDEX IF NOT EXISTS` statements) and call it inside
    `get_connection()` on every new connection, so every request connection —
    file-backed or in-memory — has the table regardless of how the app starts.
    `init_db()` now delegates to `ensure_schema`.
  - `src/db.py`: when `DATABASE_PATH=":memory:"`, route connections through a
    named shared-cache in-memory URI (`file:...?mode=memory&cache=shared`) with
    a process-lifetime keep-alive connection, so the separate per-request
    connections share one in-memory database (plain `:memory:` gives each
    connection its own empty DB, which broke DELETE-then-GET). File paths are
    unchanged.
  - Public API, request/response schemas, status codes, and repository SQL are
    unchanged — only connection/schema bootstrapping was modified. — FR-016.
