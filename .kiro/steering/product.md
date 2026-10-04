---
inclusion: always
---

# Product: AI Software Engineering Team

## What this product is

A Kiro-native system where seven specialized AI agents collaborate to turn a
software project idea into a structured, tested, and documented project. Kiro
CLI itself is the orchestration runtime — there is no separate backend server.

## The seven roles

1. Project Manager (orchestrator) — drives the pipeline and approval gates.
2. Requirements Analyst — turns the idea into functional requirements and user stories.
3. Software Architect — turns requirements into an architecture and API/data design.
4. Developer — turns the design and tasks into source code.
5. Tester — writes and runs tests, reports pass/fail.
6. Security Reviewer — reviews code read-only and reports findings.
7. Documentation Agent — produces README and project docs.

## Lifecycle (never skip a stage)

IDEA -> REQUIREMENTS -> DESIGN -> TASKS -> IMPLEMENTATION -> TESTING ->
SECURITY REVIEW -> DOCUMENTATION -> COMPLETED

## Core principles

- Artifacts on disk are the single source of truth. Each stage reads the prior
  stage's artifacts and writes its own. Sub-agent sessions are ephemeral, so
  nothing durable may live only in session memory.
- Human approval is required after Requirements and after Architecture before
  proceeding.
- Least privilege: each role agent gets only the tools it needs.
- Downstream agents must not modify upstream artifacts without approval. The
  Developer must not rewrite requirements; the Security Reviewer must not edit code.

## Per-project workspace

Each idea produces a workspace under `projects/<project-slug>/` containing:
`status.json`, `requirements.md`, `architecture.md`, `tasks.md`,
`security-review.md`, `test-report.md`, `README.md`, `src/`, `tests/`.

## MVP success criteria

A user enters an idea; the system generates requirements, architecture, tasks,
source code, runnable tests, a security review, and documentation; the user can
see each agent's status; all artifacts are preserved.
