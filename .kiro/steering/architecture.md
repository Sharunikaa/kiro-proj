---
inclusion: always
---

# Architecture

## Orchestration shape

One orchestrator agent receives the idea and runs the pipeline as discrete,
human-gated phases using the `subagent` tool. Each role agent is a sub-agent
stage. Because the `subagent` tool runs stages to completion (sub-agents cannot
pause for input and cannot spawn their own sub-agents), the orchestrator runs
one phase, returns control to the human for approval where required, then
proceeds.

## Phased execution with approval gates

Phase 1: requirements-analyst  -> writes requirements.md  [APPROVAL GATE]
Phase 2: software-architect    -> writes architecture.md  [APPROVAL GATE]
Phase 3: developer             -> writes tasks.md + src/
Phase 4: tester                -> writes tests/ + test-report.md
Phase 5: security-reviewer     -> writes security-review.md
Phase 6: documentation-agent   -> writes README.md + docs/

After Requirements (Phase 1) and Architecture (Phase 2), the orchestrator stops
and asks the human to approve before continuing. Phases 3-6 may run as a
dependent chain once Architecture is approved.

## Artifact-based communication

Agents never pass data through session memory across stages. Each stage:
1. Reads the upstream artifact(s) it depends on.
2. Produces its own artifact(s) with a metadata header (see coding-standards).
3. Updates `status.json` via the update-status hook.

## Status tracking

`projects/<slug>/status.json` records the state of each stage:
`pending | in_progress | completed | failed | needs_approval`.
The terminal status view renders this file.

## Least-privilege tool boundaries

- Only the orchestrator may use the `subagent` tool.
- Developer may write only under its project `src/` (and tasks.md).
- Security Reviewer is read-only over source; a preToolUse hook blocks writes.
- Tester may run only test commands via shell.

## Generated-project architecture (default stack)

A simple layered FastAPI app:
Routes/API layer -> Service layer -> Data layer (SQLite). Keep it minimal and
testable. See technology.md for the configurable stack.
