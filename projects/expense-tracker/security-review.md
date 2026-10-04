<!--
artifact: security-review.md
created_by: security-reviewer
created_at: 2026-10-04T21:42:42+05:30
status: draft
version: 1
related: requirements.md, architecture.md, src/
-->

# Security Review — Student Expense Tracker

Read-only review of `projects/expense-tracker/src/`, `requirements.txt`, and
`tests/`, cross-checked against the approved `architecture.md` and
`requirements.md`. No source was modified.

## 1. Security Status

**PASS WITH FINDINGS**

The implementation shows strong security fundamentals: all SQL is
parameterized, inputs are validated via Pydantic with `extra="forbid"`,
amounts use `Decimal` (no float drift), config is read from the environment
with no hardcoded secrets, and error handlers return safe, generic messages.
The findings below are supply-chain hygiene and defense-in-depth items; none
is an exploitable vulnerability in the single-user MVP as scoped.

## 2. Findings

| id | severity | location | description | recommendation |
|----|----------|----------|-------------|----------------|
| SEC-01 | Medium | `requirements.txt:1-3` | Dependencies `fastapi`, `uvicorn`, `pydantic` are completely unpinned (no version specifiers). Builds are non-reproducible and a future malicious or breaking release would be pulled in silently — a supply-chain exposure. | Pin to known-good versions (e.g. `fastapi==0.115.*`, `uvicorn==0.30.*`, `pydantic==2.*`) and add a lockfile / hashes. Add `httpx` which tests require. |
| SEC-02 | Low | `src/main.py:34-41` | FastAPI interactive docs (`/docs`, `/redoc`) and OpenAPI schema are enabled by default. For a localhost single-user MVP this is acceptable, but it broadens surface if ever bound to a non-loopback interface. | If the app is ever exposed beyond localhost, disable docs in production (`docs_url=None, redoc_url=None`) or gate behind auth. Document the localhost-only binding assumption. |
| SEC-03 | Low | `src/db.py` (whole file) | No transport/listener hardening is codified. The app relies on the operator binding `uvicorn` to localhost; nothing enforces it. `check_same_thread=False` is used with per-request short-lived connections (safe here) but is worth noting. | Document that `uvicorn` must bind `127.0.0.1` for the single-user MVP; do not expose SQLite to a network. No code change required. |
| SEC-04 | Info | `src/schemas.py:70-73`, `architecture.md:187`, `requirements.md:43` | No authentication/authorization on any endpoint. This is explicitly out of scope — the MVP is single-user by design (`requirements.md:26,43`). Noted for completeness, not a defect. | None for the MVP. If multi-user is ever added, introduce authn + per-user data isolation before exposing the API. |
| SEC-05 | Info | `src/repository.py:106`, `src/repository.py:169` | f-strings build a `YYYY-MM` month prefix (`f"{year:04d}-{month:02d}"`). The f-string output is passed as a **bound parameter** (`params.append(prefix)` / `(prefix,)`), never concatenated into the SQL text, and the inputs are integers formatted with `:04d`/`:02d`. Not an injection vector. | No change. Verified safe — flagged only to document that the f-strings were reviewed. |

## 3. Checklist results

| Item | Result | Note |
|------|--------|------|
| **Secrets** — no hardcoded keys/passwords/tokens; config from env | **PASS** | `src/config.py:16-18` reads `DATABASE_PATH` from `os.environ` with a safe local default (`expenses.db`). No secrets anywhere in `src/`. Repo `.gitignore:1` ignores `.env`; `projects/*/*.db` is also ignored. The app embeds no secrets. |
| **Input validation** — all external inputs validated, bounds checks | **PASS** | `src/schemas.py`: `ExpenseIn` uses `extra="forbid"` (line 40); amount `> 0` and `<= 2dp` (`_validate_amount` 48-57, `quantize_amount` 28-35); category non-empty after trim (60-66); date is a real calendar date via `datetime.date` typing; note `<= 500` chars (69-75). Query params bounded: `month` is `ge=1, le=12` (`src/routes.py:65`, `:112`). Cross-field checks in `src/service.py` (date-range order 60, month/year pairing 63-71). |
| **Injection** — parameterized queries, no string-built SQL/shell | **PASS** | Every statement in `src/repository.py` uses `?` placeholders: insert (46-58), get (69-74), dynamic filter list (`list_expenses` 94-116 builds only parameterized `clauses` joined with `AND`), update (124-141), delete (147), summary (159-167). No f-string/`%`/`+` concatenation of user values into SQL. No shell/`subprocess`/`os.system` usage. |
| **AuthN/AuthZ** — protected endpoints require auth | **N/A (by design)** | No auth — explicitly out of scope for the single-user MVP (`requirements.md:26,43`). Recorded as SEC-04 (Info), not a failure. |
| **Error handling** — no stack traces or secrets in responses | **PASS** | `src/routes.py:register_exception_handlers` (118-137) maps `NotFoundError`→404 and `DomainValidationError`→422 with a fixed `{"detail": <safe message>}` body. Messages are domain strings (e.g. `"Expense {id} not found"`), no internals leaked. Pydantic 422s are framework-standard. |
| **Dependencies** — no unmaintained/typosquatted packages; versions pinned | **PARTIAL / FAIL** | `fastapi`, `uvicorn`, `pydantic` are all legitimate, widely used, actively maintained, non-typosquatted packages. However they are **unpinned** (`requirements.txt:1-3`) — see SEC-01. Also `httpx` (used by the test client) is not declared. |
| **Transport/data** — sensitive data not logged; safe defaults | **PASS** | No `logging`/`print`/`logger` calls in `src/` (grep: 0 matches); nothing logs request bodies or amounts. Amounts stored/returned as `Decimal` (canonical 2-dp TEXT in `src/repository.py:21-23`, `_row_to_dict:28`) — no float drift, no PII beyond user's own expense notes. Default DB is a local file. |

## 4. Summary

Overall risk: **Low**. The code is well-structured and follows secure
defaults for a single-user local MVP. SQL injection, secret leakage, input
validation, and error-leak classes are all handled correctly and verified
against real line numbers.

Top remediation priorities:
1. **SEC-01 (Medium)** — Pin dependency versions in `requirements.txt` and add
   the missing `httpx` test dependency. This is the one finding with a
   concrete supply-chain impact and should be fixed before any release.
2. **SEC-02 / SEC-03 (Low)** — Document the localhost-only deployment
   assumption; disable interactive docs if the service is ever exposed beyond
   loopback.
3. **SEC-04 (Info)** — Revisit authentication and per-user isolation only if
   the product moves beyond the single-user MVP.

## 5. Required fixes for developer

Only one finding warrants a code/config change at this stage:

- **SEC-01 (Medium)** — `requirements.txt`: pin `fastapi`, `uvicorn`, and
  `pydantic` to specific known-good versions and add `httpx` (required by the
  FastAPI `TestClient` used in `tests/`). No change to application logic is
  needed. All other findings are Low/Info and require documentation or no
  action for the current MVP scope.

(SEC-02 and SEC-03 are optional hardening/documentation items, not blocking
code changes for the localhost single-user MVP.)

## 6. Remediation status (post-review)

| id | severity | status | verification |
|----|----------|--------|--------------|
| SEC-01 | Medium | **FIXED** | requirements.txt pinned (fastapi==0.142.2, uvicorn==0.54.0, pydantic==2.13.5); requirements-dev.txt adds pytest==9.1.1 + httpx==0.28.1. Independently verified: clean install from pinned manifest into a fresh venv succeeded and the full test suite passed 42/42. |
| SEC-02 | Low | Deferred (documentation) | Optional hardening; localhost-only MVP. To be noted in docs. |
| SEC-03 | Low | Deferred (documentation) | Optional; document localhost binding assumption. |
| SEC-04 | Info | Accepted (by design) | No auth is out of scope for single-user MVP. |
| SEC-05 | Info | Verified safe | Month-prefix f-string passed as bound parameter; not injectable. |

Post-remediation status: **PASS WITH FINDINGS** — the one actionable Medium
(SEC-01) is fixed and verified; remaining items are Low/Info and non-blocking
for the MVP.
