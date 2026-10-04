#!/usr/bin/env bash
# run-tests.sh
# postToolUse helper for the Tester/Developer agents.
# Runs the project's pytest suite and prints a short summary.
# Exit 0 always (reporting hook, not a gate): failures are surfaced as text so
# the agent can read and react, but the turn is not aborted.
#
# Honors KIRO_PROJECT_SLUG to locate the workspace; falls back to CWD.

set -uo pipefail

INPUT="$(cat || true)"   # drain hook event JSON

SLUG="${KIRO_PROJECT_SLUG:-}"
if [[ -n "$SLUG" && -d "projects/$SLUG" ]]; then
  TARGET="projects/$SLUG"
else
  TARGET="."
fi

if [[ -x "$TARGET/.venv/bin/python" ]]; then
  # Execution below cd's into $TARGET, so reference the venv relative to it.
  PYTEST=(".venv/bin/python" -m pytest)
elif command -v pytest >/dev/null 2>&1; then
  PYTEST=(pytest)
elif command -v python3 >/dev/null 2>&1; then
  PYTEST=(python3 -m pytest)
else
  echo "run-tests: no pytest/python available; skipping test run." >&2
  exit 0
fi

if [[ ! -d "$TARGET/tests" ]]; then
  echo "run-tests: no tests/ directory in $TARGET; nothing to run." >&2
  exit 0
fi

echo "run-tests: executing (${PYTEST[*]}) -q in $TARGET" >&2
( cd "$TARGET" && "${PYTEST[@]}" -q ) 2>&1 | tail -40 >&2 || true
exit 0
