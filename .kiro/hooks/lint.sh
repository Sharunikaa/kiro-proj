#!/usr/bin/env bash
# lint.sh
# postToolUse helper for the Developer agent (matcher: write).
# Provides a lightweight syntax/lint gate for generated Python code.
# Prefers ruff, then black --check, and always falls back to py_compile.
# Reporting-only: exits 0 so it never blocks the write that already happened.

set -uo pipefail

INPUT="$(cat || true)"   # drain hook event JSON

SLUG="${KIRO_PROJECT_SLUG:-}"
if [[ -n "$SLUG" && -d "projects/$SLUG" ]]; then
  TARGET="projects/$SLUG/src"
else
  TARGET="src"
fi

[[ -d "$TARGET" ]] || { echo "lint: no $TARGET directory; skipping." >&2; exit 0; }

if command -v ruff >/dev/null 2>&1; then
  echo "lint: running ruff on $TARGET" >&2
  ruff check "$TARGET" 2>&1 | tail -30 >&2 || true
elif command -v black >/dev/null 2>&1; then
  echo "lint: running black --check on $TARGET" >&2
  black --check "$TARGET" 2>&1 | tail -30 >&2 || true
fi

# Minimum gate: byte-compile every .py to catch syntax errors.
echo "lint: py_compile syntax check on $TARGET" >&2
find "$TARGET" -name '*.py' -print0 2>/dev/null \
  | xargs -0 -I{} python -m py_compile "{}" 2>&1 | tail -30 >&2 || true

exit 0
