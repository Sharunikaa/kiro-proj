---
inclusion: always
---

# Technology

## Orchestration runtime (fixed)

- Kiro CLI custom agents in `.kiro/agents/`.
- The orchestrator agent drives a sub-agent DAG via the `subagent` tool.
- Steering (`.kiro/steering/`), skills (`.kiro/skills/`), hooks (`.kiro/hooks/`),
  specs (`.kiro/specs/`), and MCP (`.kiro/settings/mcp.json`) configure behavior.

## Generated-project stack (configurable)

The DEFAULT stack for generated projects is:

- Language: Python 3.11+
- Backend framework: FastAPI
- Test framework: pytest
- Package/deps: a `requirements.txt` (or `pyproject.toml`) inside the project workspace
- Database (if needed): SQLite for the MVP demo (no external server required)

This default is chosen so the Tester agent can actually run the test suite with
one toolchain and hooks can execute tests end-to-end.

### How to change the stack

To target a different stack (e.g., React + FastAPI + PostgreSQL), override the
values in this file. All role agents read this steering file, so changing the
stack here changes what the Architect and Developer agents target. Keep exactly
one stack active per project to keep the demo verifiable.

## Commands the agents may rely on

- Run tests: `pytest` (run from the project workspace directory)
- Lint/format: `python -m py_compile` for a syntax gate; `ruff` or `black` if available
- Version check: `python --version`, `pytest --version`

Agents must degrade gracefully if an optional tool (ruff/black) is not installed:
fall back to `python -m py_compile` as the minimum syntax gate.
