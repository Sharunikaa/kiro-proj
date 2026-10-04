#!/usr/bin/env bash
# new-project.sh <slug> [title]
# Scaffolds a projects/<slug>/ workspace with empty artifact placeholders,
# src/ and tests/ directories, and an initialized status.json derived from
# scripts/status.template.json.

set -euo pipefail

SLUG="${1:-}"
TITLE="${2:-$SLUG}"

if [[ -z "$SLUG" ]]; then
  echo "usage: scripts/new-project.sh <slug> [title]" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/projects/$SLUG"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

mkdir -p "$DEST/src" "$DEST/tests" "$DEST/docs"

# Initialize status.json from the template with slug/title/timestamps filled in.
python3 - "$ROOT/scripts/status.template.json" "$DEST/status.json" "$SLUG" "$TITLE" "$TS" <<'PY'
import json, sys
tmpl, dest, slug, title, ts = sys.argv[1:6]
with open(tmpl) as f:
    data = json.load(f)
data["project"] = title
data["slug"] = slug
data["created_at"] = ts
data["updated_at"] = ts
with open(dest, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

echo "Scaffolded project workspace at projects/$SLUG"
echo "  status.json initialized (current_stage=requirements)"
echo "  directories: src/ tests/ docs/"
