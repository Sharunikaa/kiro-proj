#!/usr/bin/env bash
# status-view.sh [slug]
# Renders the terminal agent status board from projects/<slug>/status.json.
# If no slug is given and exactly one project exists, uses that one.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="${1:-}"

if [[ -z "$SLUG" ]]; then
  mapfile -t PROJECTS < <(ls -1 "$ROOT/projects" 2>/dev/null || true)
  if [[ ${#PROJECTS[@]} -eq 1 ]]; then
    SLUG="${PROJECTS[0]}"
  else
    echo "usage: scripts/status-view.sh <slug>" >&2
    echo "available projects: ${PROJECTS[*]:-none}" >&2
    exit 1
  fi
fi

STATUS="$ROOT/projects/$SLUG/status.json"
[[ -f "$STATUS" ]] || { echo "no status.json for project '$SLUG'" >&2; exit 1; }

python3 - "$STATUS" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    s = json.load(f)
legend = s.get("legend", {})
order = ["project-manager","requirements","architecture","development",
         "testing","security","documentation"]
labels = {
    "project-manager":"Project Manager",
    "requirements":"Requirements Analyst",
    "architecture":"Software Architect",
    "development":"Developer",
    "testing":"Tester",
    "security":"Security Reviewer",
    "documentation":"Documentation Agent",
}
WIDTH = 52
print()
print("AI SOFTWARE ENGINEERING TEAM")
print()
print(f"Project: {s.get('project','?')}  ({s.get('slug','?')})")
print("+" + "-"*WIDTH + "+")
for key in order:
    st = s.get("stages", {}).get(key, "pending")
    icon = legend.get(st, "?")
    row = f" {icon} {labels[key]:<22} {st:<14}"
    print("|" + row.ljust(WIDTH) + "|")
print("+" + "-"*WIDTH + "+")
print(f"Current stage: {s.get('current_stage','?')}")
print(f"Progress: {s.get('progress_percent',0)}%")
print(f"Updated: {s.get('updated_at','?')}")
print()
PY
