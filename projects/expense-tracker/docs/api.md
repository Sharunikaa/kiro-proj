<!--
artifact: docs/api.md
created_by: documentation-agent
created_at: 2026-10-04T21:54:32+05:30
status: draft
version: 1
related: README.md, architecture.md, src/routes.py, src/schemas.py
-->

# API Reference — Student Expense Tracker

Detailed endpoint and schema reference. All bodies are JSON; non-2xx responses
return `{"detail": "<message>"}` (Pydantic validation errors use FastAPI's
structured 422 body). The API is served at the root path (no prefix); interactive
docs are at `/docs` when the app is running.

## Schemas

### ExpenseIn (request)

| Field | Type | Required | Rules |
|---|---|---|---|
| `amount` | number | yes | Strictly `> 0`; at most 2 decimal places (excess precision → 422) |
| `category` | string | yes | Non-empty after trimming whitespace; stored trimmed |
| `date` | string (`YYYY-MM-DD`) | yes | Valid ISO calendar date; impossible dates (e.g. `2026-02-30`) rejected |
| `note` | string | no | Max 500 characters; omitted/`null` allowed |

Unknown or extra fields are rejected with `422` (`extra="forbid"`).

### ExpenseOut (response)

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Primary key, assigned on create |
| `amount` | number | Canonical 2-decimal value |
| `category` | string | Trimmed |
| `date` | string (`YYYY-MM-DD`) | |
| `note` | string \| null | |
| `created_at` | string (ISO-8601 datetime) | Set at insert time (UTC) |

### MonthlySummaryOut (response)

| Field | Type | Notes |
|---|---|---|
| `year` | integer | Echo of the requested year |
| `month` | integer | Echo of the requested month (1–12) |
| `total` | number | Grand total for the month (2 decimals) |
| `by_category` | array of `CategoryTotal` | `[]` when the month has no expenses |

`CategoryTotal`: `{ "category": string, "total": number }`.

## Endpoints

### 1. Create an expense

```
POST /expenses
```

- Body: `ExpenseIn`
- Success: `201 Created` → `ExpenseOut`
- Errors: `422` for invalid amount/category/date/note or unknown fields

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.50, "category": "Groceries", "date": "2026-10-04", "note": "weekly shop"}'
```

### 2. Get an expense

```
GET /expenses/{id}
```

- Path: `id` (integer)
- Success: `200 OK` → `ExpenseOut`
- Errors: `404` not found; `422` non-integer id

```bash
curl http://127.0.0.1:8000/expenses/1
```

### 3. List / filter expenses

```
GET /expenses
```

Query parameters (all optional, AND-combined):

| Param | Type | Notes |
|---|---|---|
| `category` | string | Exact match |
| `start_date` | `YYYY-MM-DD` | Inclusive lower bound |
| `end_date` | `YYYY-MM-DD` | Inclusive upper bound |
| `year` | integer | Must be supplied together with `month` |
| `month` | integer (1–12) | Must be supplied together with `year` |

- Success: `200 OK` → `[ExpenseOut]` (empty list when nothing matches)
- Errors: `422` for malformed date, `start_date > end_date`, `year`/`month` not
  supplied together, or `month` outside 1–12

```bash
curl "http://127.0.0.1:8000/expenses?category=Groceries&start_date=2026-10-01&end_date=2026-10-31"
curl "http://127.0.0.1:8000/expenses?year=2026&month=10"
```

### 4. Update an expense

```
PUT /expenses/{id}
```

- Path: `id` (integer); Body: `ExpenseIn` (full replacement; same rules as create)
- Success: `200 OK` → updated `ExpenseOut`
- Errors: `404` not found; `422` same validation as create

```bash
curl -X PUT http://127.0.0.1:8000/expenses/1 \
  -H "Content-Type: application/json" \
  -d '{"amount": 15.00, "category": "Groceries", "date": "2026-10-04", "note": "corrected"}'
```

### 5. Delete an expense

```
DELETE /expenses/{id}
```

- Path: `id` (integer)
- Success: `204 No Content`
- Errors: `404` not found; `422` non-integer id

```bash
curl -X DELETE http://127.0.0.1:8000/expenses/1 -i
```

### 6. Monthly summary

```
GET /summary/monthly?year=&month=
```

- Query (required): `year` (integer), `month` (integer 1–12)
- Success: `200 OK` → `MonthlySummaryOut`
- Errors: `422` missing/invalid `year` or `month`; a valid but empty month
  returns a zeroed summary (`total = 0.00`, `by_category = []`), not an error

```bash
curl "http://127.0.0.1:8000/summary/monthly?year=2026&month=10"
```
