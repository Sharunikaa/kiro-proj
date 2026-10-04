# AI Software Engineering Team (Kiro-native)

Seven specialized Kiro custom agents collaborate to turn a software project idea
into requirements, architecture, tasks, source code, tests, a security review,
and documentation. **Kiro CLI itself is the orchestration runtime** — there is no
separate backend server. This project is a demonstration of Kiro's capabilities:
Steering, Specs, Skills, Hooks, MCP, Custom Agents, and Sub-agents.

## The team

| Agent | Role | Writes |
|---|---|---|
| `orchestrator` | Project Manager / pipeline driver (only agent that spawns sub-agents) | `status.json` |
| `requirements-analyst` | Requirements & user stories | `requirements.md` |
| `software-architect` | Architecture, API & data design | `architecture.md` |
| `developer` | Source code | `tasks.md`, `src/` |
| `tester` | Tests + run report | `tests/`, `test-report.md` |
| `security-reviewer` | Read-only security review | `security-review.md` |
| `documentation-agent` | Project docs | `README.md`, `docs/` |

## Lifecycle (phased, with human approval gates)

```
IDEA → REQUIREMENTS → DESIGN → TASKS → IMPLEMENTATION → TESTING → SECURITY REVIEW → DOCUMENTATION
            │ gate         │ gate
            ▼              ▼
       you approve    you approve
```

The orchestrator pauses after **Requirements** and after **Architecture** so you
can review and approve before it proceeds. Phases 3–6 (developer → tester →
security-reviewer → documentation-agent) run as a dependent chain after you
approve the architecture.

## How Kiro capabilities are used

- **Custom Agents** — `.kiro/agents/*.json`, each least-privilege (scoped tools,
  write-path restrictions, role prompt in `.kiro/agents/prompts/*.md`).
- **Sub-agents** — the orchestrator uses the `subagent` tool to run each role as
  a DAG stage (`toolsSettings.crew` restricts which agents are allowed).
- **Steering** — `.kiro/steering/*.md` (product, technology, architecture,
  coding-standards, workflow) loaded into every agent.
- **Skills** — `.kiro/skills/*/SKILL.md` domain playbooks, loaded on demand and
  invocable as `/requirements-authoring`, `/software-architecture`, `/testing`,
  `/security-review`, `/documentation`.
- **Hooks** — `.kiro/hooks/*.sh`: lint & run-tests after writes, a `stop`
  heartbeat, an artifact-header validator, and a `preToolUse` guard that blocks
  the Security Reviewer from writing to `src/`.
- **Specs** — `.kiro/specs/expense-tracker/{requirements,design,tasks}.md`.
- **MCP** — the **orchestrator** runs a minimal `git` MCP server (`uvx
  mcp-server-git`) pinned to this repository. It uses Git MCP meaningfully during
  the pipeline (see "Git MCP workflow" below). A `github` server stub exists in
  `.kiro/settings/mcp.json` but is `disabled` until you set `GITHUB_TOKEN`.

## Git MCP workflow

The orchestrator integrates Git MCP as the system of record for pipeline
progress. Only the orchestrator has git tools; the six role agents do not.

Tools and trust:

| Tool | When used | Trust |
|---|---|---|
| `@git/git_status` | At project start, before scaffolding | Auto-approved (read-only) |
| `@git/git_diff` | After a stage writes artifacts, to show real changes | Auto-approved (read-only) |
| `@git/git_log` | When reporting progress / history | Auto-approved (read-only) |
| `@git/git_add` | After a phase completes (and is approved) | **Requires confirmation** |
| `@git/git_commit` | To record an approved phase as a commit | **Requires confirmation** |

Branch/checkout/reset/init operations are **disabled** (`disabledTools`) to keep
scope minimal and avoid destructive actions. The server is restricted to this
repo via `--repository`.

Typical flow per phase: stage runs → `git_diff` shows what changed → phase
summary → (at Requirements/Architecture gates) you approve → orchestrator asks to
`git_add` + `git_commit` the approved artifact with a conventional message.

Requirements: `uvx` (from `uv`) and `git` must be on PATH, and the project
directory must be a git repository. The orchestrator's `agentSpawn` hook prints
`git repo: OK/MISSING` and flags a missing `uvx` at startup.

## Prerequisites

- Kiro CLI installed (`kiro-cli`).
- Python 3.11+ and `pytest` (so the Tester agent can actually run tests):
  `pip install pytest`.
- Optional: `ruff` or `black` for richer linting (the lint hook falls back to
  `python -m py_compile`).
- Optional MCP: `uvx` (for `mcp-server-git`) if you enable the git server.

## Run the demo

1. Scaffold a project workspace (the orchestrator can also do this):
   ```bash
   ./scripts/new-project.sh expense-tracker "Student Expense Tracker"
   ```
2. Start the orchestrator and give it the idea:
   ```bash
   kiro-cli chat --agent orchestrator "Build a student expense tracking application"
   ```
3. The orchestrator runs **Phase 1 (Requirements)** and pauses. Review
   `projects/expense-tracker/requirements.md` and approve or request changes.
4. It runs **Phase 2 (Architecture)** and pauses. Review
   `projects/expense-tracker/architecture.md` and approve.
5. It runs **Phases 3–6** (develop → test → security review → document).
6. Check progress anytime:
   ```bash
   ./scripts/status-view.sh expense-tracker
   ```

## Validate the agents

```bash
for a in .kiro/agents/*.json; do echo "== $a =="; kiro-cli agent validate --path "$a"; done
```

## Repository layout

```
.kiro/
  agents/        orchestrator + 6 role agents (JSON) and prompts/
  steering/      always-on project rules
  skills/        on-demand domain playbooks
  hooks/         shell hooks (lint, tests, status, validation, src guard)
  specs/         spec-driven feature docs
  settings/      mcp.json
projects/<slug>/ per-idea workspace (artifacts + src/ + tests/)
scripts/         new-project.sh, status-view.sh, status.template.json
spec.md          product spec
```

## Notes & limitations

- Approval gates are **phased** (human-in-the-loop between stages), because the
  `subagent` tool runs stages to completion and cannot pause mid-stage for input.
- Sub-agent sessions are ephemeral; all durable state lives in files.
- The generated-project stack is **configurable** via `.kiro/steering/technology.md`
  (default: Python/FastAPI/pytest/SQLite). A web dashboard is a planned stretch
  goal; the MVP ships the terminal status view.
