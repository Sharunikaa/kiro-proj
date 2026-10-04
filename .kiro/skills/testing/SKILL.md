---
name: testing
description: Playbook for generating and running automated tests for the generated project. Use when writing tests or producing test-report.md.
---

# Testing

Generate and run tests for the generated project (default: pytest).

## Process

1. Read `requirements.md` (acceptance criteria) and the code under `src/`.
2. For each core capability, write at least one happy-path and one failure-path test.
3. Place tests under the project `tests/` directory.
4. Run the suite from the project workspace: `pytest -q`.
5. Produce `test-report.md` summarizing results.

## test-report.md structure

1. **Summary** — total / passed / failed / skipped.
2. **Per-test results** — table: test name, what it checks, expected, result.
3. **Failures** — for each failure, the error and a suggested fix (do not fix code yourself; report it).
4. **Coverage notes** — which requirements are/ aren't covered.

## Quality bar

- Tests must be runnable without network access.
- Prefer `pytest` fixtures over duplicated setup.
- Each acceptance criterion maps to at least one test where feasible.

## Remember

- Write the artifact metadata header on `test-report.md`.
- If `src/` is missing or empty, stop and report the missing dependency.
