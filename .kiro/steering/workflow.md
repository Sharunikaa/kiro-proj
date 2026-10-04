---
inclusion: always
---

# Workflow

## The lifecycle is strict and ordered

IDEA -> REQUIREMENTS -> DESIGN -> TASKS -> IMPLEMENTATION -> TESTING ->
SECURITY REVIEW -> DOCUMENTATION -> COMPLETED

An agent must not skip a prior stage. If an upstream artifact is missing, the
stage must stop and report the missing dependency rather than inventing it.

## Approval gates (phased execution)

The orchestrator runs the pipeline in phases and PAUSES for human approval:

- After Phase 1 (Requirements): orchestrator sets requirements stage to
  `needs_approval`, presents a summary, and waits. It must NOT start Architecture
  until the human approves.
- After Phase 2 (Architecture): orchestrator sets architecture stage to
  `needs_approval`, presents a summary, and waits. It must NOT start Development
  until the human approves.

If the human rejects an artifact, the orchestrator re-runs that stage with the
feedback and asks again. It does not proceed on rejection.

## Status values

`pending` (○) | `in_progress` (●) | `completed` (✓) | `failed` (✕) |
`needs_approval` (⚠)

## How a stage runs

1. Orchestrator spawns the role agent as a sub-agent with a prompt that names
   the project slug and the artifacts to read/write.
2. The role agent reads upstream artifacts, does its work, writes its artifact(s)
   with the required metadata header, and updates status.json.
3. Control returns to the orchestrator, which either pauses for approval or
   continues to the next phase.

## Sub-agent constraints to respect

- Only the orchestrator calls `subagent`. Role agents never spawn sub-agents.
- Sub-agent sessions are ephemeral; persist everything to files.
- Keep each stage scoped to finish within a bounded number of turns.
