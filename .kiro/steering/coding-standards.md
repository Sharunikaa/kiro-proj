---
inclusion: always
---

# Coding Standards

## Artifact metadata header (required on every generated .md artifact)

Every markdown artifact (requirements.md, architecture.md, tasks.md,
test-report.md, security-review.md, README.md) must begin with this header:

```
<!--
artifact: <artifact-name>
created_by: <agent-name>
created_at: <ISO-8601 timestamp>
status: <draft | approved | final>
version: <integer, starts at 1>
related: <requirement/task id or "-">
-->
```

The `validate-artifacts.sh` hook checks for this header.

## Python code standards (default stack)

- Target Python 3.11+.
- Use type hints on public functions.
- Validate all external input (FastAPI: use Pydantic models).
- No hardcoded secrets. Read config from environment variables.
- Use parameterized queries / an ORM layer; never string-concatenate SQL.
- Handle errors explicitly; return meaningful HTTP status codes.
- Keep functions focused; prefer small, testable units.

## Testing standards

- Every feature gets at least one happy-path and one failure-path test.
- Tests live under the project `tests/` directory and run with `pytest`.
- Tests must be runnable without network access for the MVP demo.

## Documentation standards

- README includes: overview, setup, how to run, how to test, project structure.
- API docs list each endpoint, method, inputs, outputs, and error cases.

## Agent conduct

- Do not skip lifecycle stages.
- Do not modify an upstream artifact you did not produce without explicit approval.
- Keep outputs concise and structured.
