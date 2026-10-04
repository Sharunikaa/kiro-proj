#!/usr/bin/env bash
# update-status.sh
# Stop-hook helper: records that the agent finished a turn.
# Reads the hook event JSON from stdin (hook_event_name, cwd, assistant_response).
# This is intentionally lightweight: it appends a heartbeat to a per-project log
# if a KIRO_PROJECT_SLUG is set, otherwise it is a no-op success.
#
# The authoritative status.json is written by the agents themselves (via the
# write tool) using the schema in scripts/status.template.json. This hook only
# provides an audit heartbeat and never fails the turn.

set -euo pipefail

# Drain stdin (the hook event). We don't require it, but must consume it.
INPUT="$(cat || true)"

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SLUG="${KIRO_PROJECT_SLUG:-}"

if [[ -n "$SLUG" && -d "projects/$SLUG" ]]; then
  echo "[$TS] turn complete (session=${KIRO_SESSION_ID:-unknown})" \
    >> "projects/$SLUG/.status-heartbeat.log" 2>/dev/null || true
fi

# Always succeed so we never block the agent.
exit 0
