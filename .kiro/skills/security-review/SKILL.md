---
name: security-review
description: Checklist-driven playbook for reviewing generated code for security issues. Use when producing security-review.md. Read-only over source code.
---

# Security Review

Review the generated code read-only and produce `security-review.md`. Do NOT edit
source code — report findings only.

## Checklist

- **Secrets**: no hardcoded API keys, passwords, tokens; config from env vars.
- **Input validation**: all external inputs validated (Pydantic models, bounds checks).
- **Injection**: parameterized queries / ORM; no string-concatenated SQL or shell.
- **AuthN/AuthZ**: protected endpoints require authentication; access checks present where relevant.
- **Error handling**: no stack traces or secrets leaked in responses.
- **Dependencies**: no obviously unmaintained or typosquatted packages; versions pinned.
- **Transport/data**: sensitive data not logged; safe defaults.

## security-review.md structure

1. **Security Status** — PASS / PASS WITH FINDINGS / FAIL.
2. **Findings** — table: id, severity (High/Med/Low), location, description, recommendation.
3. **Checklist results** — each checklist item with pass/fail and a note.
4. **Summary** — overall risk and the top remediation priorities.

## Quality bar

- Be specific: cite file and line where possible.
- Severity reflects real impact; avoid false alarms.
- If no code exists yet, stop and report the missing dependency.

## Remember

- Write the artifact metadata header.
- You are read-only over `src/`; a hook enforces this.
