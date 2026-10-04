---
name: software-architecture
description: Playbook for turning requirements into a system architecture, API design, and data model. Use when generating or refining architecture.md or a spec design.md.
---

# Software Architecture

Produce an `architecture.md` the Developer can implement directly, targeting the
stack defined in the technology steering file (default: Python/FastAPI/pytest/SQLite).

## Structure to produce

1. **Overview** — the chosen architecture style in 2-3 sentences.
2. **Components** — list each component and its responsibility.
3. **Layering** — Routes/API -> Service -> Data. Show the flow.
4. **API design** — table of endpoints: method, path, request, response, errors.
5. **Data model** — entities, fields, types, relationships (SQLite-friendly).
6. **Dependencies** — libraries required (keep minimal).
7. **Technical risks** — short list with mitigations.
8. **Traceability** — map each component/endpoint back to FR/US ids.

## Quality bar

- Every functional requirement is covered by at least one component or endpoint.
- The design is minimal and testable; avoid speculative abstraction.
- Respect the configurable stack from steering; do not invent a different stack.

## Remember

- Write the artifact metadata header.
- Read `requirements.md` first; if it is missing, stop and report it.
