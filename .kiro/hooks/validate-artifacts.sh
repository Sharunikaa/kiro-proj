#!/usr/bin/env bash
# validate-artifacts.sh
# postToolUse helper (matcher: write).
# When an agent writes a markdown artifact, verify it carries the required
# metadata header (artifact/created_by/created_at/status/version). Reporting
# only (exit 0): warns via stderr so the agent can self-correct.

set -uo pipefail

INPUT="$(cat || true)"   # hook event JSON on stdin

# Try to extract the written path from the tool_input JSON (best-effort, no jq dependency).
# Supports keys "path" used by the write tool.
PATHS=$(printf '%s' "$INPUT" | grep -oE '"path"[[:space:]]*:[[:space:]]*"[^"]+"' \
          | sed -E 's/.*"path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' || true)

REQUIRED=(artifact created_by created_at status version)

check_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  case "$f" in
    *.md) ;;
    *) return 0 ;;  # only markdown artifacts
  esac
  # Only enforce on known artifact names.
  case "$(basename "$f")" in
    requirements.md|architecture.md|tasks.md|test-report.md|security-review.md|README.md) ;;
    *) return 0 ;;
  esac
  local head
  head="$(head -n 15 "$f" 2>/dev/null || true)"
  local missing=()
  for key in "${REQUIRED[@]}"; do
    printf '%s' "$head" | grep -q "$key:" || missing+=("$key")
  done
  if (( ${#missing[@]} > 0 )); then
    echo "validate-artifacts: $f is missing metadata header fields: ${missing[*]}" >&2
    echo "  Add the artifact metadata header (see .kiro/steering/coding-standards.md)." >&2
  else
    echo "validate-artifacts: $f header OK." >&2
  fi
}

if [[ -n "$PATHS" ]]; then
  while IFS= read -r p; do
    [[ -n "$p" ]] && check_file "$p"
  done <<< "$PATHS"
fi

exit 0
