#!/usr/bin/env bash
# block-src-write.sh
# preToolUse hook for the Security Reviewer agent (matcher: write).
# Enforces read-only-over-source: blocks any write whose target path is inside a
# project's src/ or tests/ directory. Exit 2 blocks the tool and returns stderr
# to the model; exit 0 allows (e.g., writing security-review.md).

set -uo pipefail

INPUT="$(cat || true)"   # hook event JSON on stdin

# Extract target path(s) from the write tool_input (best-effort, no jq).
PATHS=$(printf '%s' "$INPUT" | grep -oE '"path"[[:space:]]*:[[:space:]]*"[^"]+"' \
          | sed -E 's/.*"path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)

blocked=0
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  if printf '%s' "$p" | grep -qE '(^|/)(src|tests)/'; then
    echo "BLOCKED: Security Reviewer is read-only over source. Refusing to write: $p" >&2
    echo "Report findings in security-review.md instead of editing code or tests." >&2
    blocked=1
  fi
done <<< "$PATHS"

if (( blocked == 1 )); then
  exit 2   # block tool execution
fi
exit 0
