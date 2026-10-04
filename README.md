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
- **MCP** — `.kiro/settings/mcp.json` configures a minimal `git` server; a
  `github` server is included but `disabled` until you set `GITHUB_TOKEN` and add
  its tools to an agent.

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
