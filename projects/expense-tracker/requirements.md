<!--
artifact: requirements.md
created_by: requirements-analyst
created_at: 2026-10-04T20:39:47+05:30
status: draft
version: 1
related: -
-->

# Student Expense Tracker — Requirements

## Overview

The Student Expense Tracker is a backend application (Python + FastAPI,
tested with pytest, persisting to SQLite) that lets college students record
and understand their personal spending. A student can add an expense (amount,
category, date, and an optional note), list and filter their recorded
expenses, and view monthly spending summaries broken down by category. The
goal is a simple, reliable tool that helps budget-conscious students see where
their money goes each month.

### Target users

- **College students** managing limited budgets who want to log day-to-day
  spending and review monthly totals.
- (Implied operator) A single-user MVP; multi-user accounts are out of scope.

## Scope

### In scope

- Create an expense with amount, category, date, and optional note.
- Retrieve a single expense by its identifier.
- List all expenses, with optional filters (category, date range, month).
- Update an existing expense.
- Delete an expense.
- Monthly spending summary aggregated by category for a given month.
- Input validation and meaningful error responses.
- Local persistence in SQLite.

### Out of scope

- User authentication, accounts, or multi-user data isolation.
- Budgets, limits, alerts, or recurring expenses.
- Currency conversion / multi-currency handling (single implicit currency).
- Income tracking, reports export (CSV/PDF), or charts/visualizations.
- Web/mobile UI, notifications, and third-party integrations (banks, etc.).

## Functional requirements

- **FR-001** The system shall create a new expense given an amount, category,
  date, and an optional note, and assign it a unique identifier.
- **FR-002** The system shall reject an expense whose amount is missing, zero,
  negative, or non-numeric.
- **FR-003** The system shall reject an expense whose category is missing or
  empty.
- **FR-004** The system shall reject an expense whose date is missing or not a
  valid calendar date.
- **FR-005** The system shall treat the note field as optional and accept its
  absence.
- **FR-006** The system shall retrieve a single expense by its unique
  identifier and return a not-found result when no such expense exists.
- **FR-007** The system shall list all recorded expenses.
- **FR-008** The system shall allow listing to be filtered by category.
- **FR-009** The system shall allow listing to be filtered by a date range
  (start date and/or end date).
- **FR-010** The system shall allow listing to be filtered by a specific month
  (year + month).
- **FR-011** The system shall update an existing expense's fields and reject
  updates to a non-existent expense.
- **FR-012** The system shall apply the same validation rules on update as on
  create (FR-002 through FR-005).
- **FR-013** The system shall delete an expense by its identifier and report a
  not-found result when the expense does not exist.
- **FR-014** The system shall produce a monthly spending summary for a given
  month, grouping total amount spent by category.
- **FR-015** The system shall return a zero/empty summary for a month that has
  no recorded expenses.
- **FR-016** The system shall persist all expenses so that data survives
  application restarts.
- **FR-017** The system shall return meaningful error responses with
  appropriate status codes for invalid input and not-found conditions.

## User stories

### US-001 — Add an expense
> As a student, I want to add an expense with an amount, category, date, and
> optional note, so that I can record what I spent.

Acceptance Criteria:
- [ ] Submitting amount, category, and date creates an expense and returns it
      with a unique identifier.
- [ ] An optional note is stored when provided and omitted cleanly when absent.
- [ ] Submitting a missing/zero/negative/non-numeric amount is rejected with a
      validation error.
- [ ] Submitting a missing/empty category is rejected with a validation error.
- [ ] Submitting a missing or invalid date is rejected with a validation error.

### US-002 — View a single expense
> As a student, I want to retrieve one expense by its identifier, so that I can
> check its details.

Acceptance Criteria:
- [ ] Requesting an existing expense returns all its stored fields.
- [ ] Requesting a non-existent identifier returns a not-found response.

### US-003 — List and filter expenses
> As a student, I want to list my expenses and filter them, so that I can find
> specific spending.

Acceptance Criteria:
- [ ] Listing with no filters returns all recorded expenses.
- [ ] Filtering by category returns only expenses in that category.
- [ ] Filtering by a date range returns only expenses within the range
      (inclusive of boundaries).
- [ ] Filtering by a specific month returns only expenses in that month.
- [ ] A filter matching no expenses returns an empty list, not an error.
- [ ] An invalid filter value (e.g., malformed date) is rejected with a
      validation error.

### US-004 — Update an expense
> As a student, I want to edit an existing expense, so that I can correct
> mistakes.

Acceptance Criteria:
- [ ] Updating an existing expense persists the changed fields and returns the
      updated expense.
- [ ] Updating a non-existent expense returns a not-found response.
- [ ] Updates violating validation rules (FR-002–FR-005) are rejected.

### US-005 — Delete an expense
> As a student, I want to delete an expense, so that I can remove entries I no
> longer want.

Acceptance Criteria:
- [ ] Deleting an existing expense removes it and confirms success.
- [ ] A subsequent retrieval of the deleted expense returns not-found.
- [ ] Deleting a non-existent expense returns a not-found response.

### US-006 — Monthly summary by category
> As a student, I want a monthly summary of spending grouped by category, so
> that I can see where my money goes.

Acceptance Criteria:
- [ ] Requesting a summary for a month returns total amount spent per category.
- [ ] Category totals equal the sum of that category's expenses for the month.
- [ ] A month with no expenses returns an empty/zero summary, not an error.
- [ ] An invalid month input is rejected with a validation error.

### US-007 — Data persistence
> As a student, I want my expenses saved, so that they remain available after I
> restart the app.

Acceptance Criteria:
- [ ] Expenses created in one session are retrievable after an application
      restart.

## Edge cases & validation rules

- Amount must be a positive number; reject zero, negative, non-numeric, and
  missing values.
- Amount precision: amounts represent currency; fractional values (e.g., two
  decimal places) are allowed. Reject values with excessive/invalid precision
  per the architect's chosen rule.
- Category must be a non-empty string after trimming whitespace.
- Date must be a valid calendar date; reject malformed or impossible dates
  (e.g., `2026-02-30`).
- Note is optional; when present it must be a string within a reasonable length
  limit (exact limit to be set during design).
- Date-range filter: if both start and end are given, start must not be after
  end; otherwise reject with a validation error.
- Month filter: month must be a valid year/month; reject out-of-range months.
- Retrieving, updating, or deleting a non-existent identifier returns a
  not-found result (never a server error).
- Empty result sets (no expenses, no matches, empty month) return successfully
  with empty data, not errors.
- Unknown or extra input fields should be handled consistently (ignored or
  rejected) per the architect's decision.

## Non-functional requirements

- **Performance** — Typical single-user operations (create, list, summary over
  a student's dataset) respond in well under one second on a local machine.
- **Reliability** — Data persists durably in SQLite and survives restarts;
  invalid operations never corrupt existing data.
- **Security** — Validate all external input; use parameterized queries / an
  ORM layer (no string-concatenated SQL); no hardcoded secrets; configuration
  via environment variables.
- **Usability** — API returns clear, meaningful error messages and appropriate
  status codes for validation and not-found conditions.
- **Testability** — Every capability has at least one happy-path and one
  failure-path test, runnable with pytest without network access.
- **Maintainability** — Code uses type hints on public functions and small,
  focused, testable units.
