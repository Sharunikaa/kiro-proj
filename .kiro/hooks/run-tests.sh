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

if [[ -x "$TARGET/.venv/bin/pytest" ]]; then
  PYTEST="$TARGET/.venv/bin/pytest"
elif command -v pytest >/dev/null 2>&1; then
  PYTEST="pytest"
else
  echo "run-tests: pytest not installed; skipping test run." >&2
  exit 0
fi

if [[ ! -d "$TARGET/tests" ]]; then
  echo "run-tests: no tests/ directory in $TARGET; nothing to run." >&2
  exit 0
fi

echo "run-tests: executing $PYTEST in $TARGET" >&2
( cd "$TARGET" && "$PYTEST" -q ) 2>&1 | tail -40 >&2 || true
exit 0
