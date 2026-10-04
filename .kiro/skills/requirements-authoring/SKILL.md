---
name: requirements-authoring
description: Playbook for turning a software idea into functional requirements, user stories, and acceptance criteria. Use when generating or refining requirements.md.
---

# Requirements Authoring

Produce a `requirements.md` that a human can approve and an architect can design from.

## Structure to produce

1. **Overview** — one paragraph restating the idea and target users.
2. **Scope** — in-scope and out-of-scope bullet lists.
3. **Functional requirements** — numbered `FR-001`, `FR-002`, ...
4. **User stories** — `US-001` in the form:
   > As a `<role>`, I want `<capability>`, so that `<benefit>`.
   Each with **Acceptance Criteria** as a checklist.
5. **Edge cases & validation rules** — explicit list.
6. **Non-functional requirements** — performance, security, usability (brief).

## Quality bar

- Every user story has testable acceptance criteria.
- Include at least one failure/edge case per core capability (e.g., invalid input).
- No implementation detail (no framework/library choices — that is the architect's job).
- Keep it concise; prefer lists over prose.

## Remember

- Write the artifact metadata header (see coding-standards steering).
- Do not design the system or pick technologies here.
