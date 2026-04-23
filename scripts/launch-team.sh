#!/usr/bin/env bash
# Launch a DaVinci Resolve MCP agent team (macOS/Linux).
# See launch-team.ps1 for the Windows equivalent.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$PROJECT_ROOT/venv/bin/python"
MAIN="$PROJECT_ROOT/src/main.py"

if [ ! -x "$PY" ]; then
    echo "venv not found at $PY" >&2
    exit 1
fi

if [ -z "${MCP_AUTH_TOKEN:-}" ] && [ -z "${MCP_AUTH_TOKENS:-}" ]; then
    echo "Set MCP_AUTH_TOKEN=<t> or MCP_AUTH_TOKENS=role:tok,role:tok" >&2
    exit 2
fi

declare -A TEAM=(
    [media]=8100
    [edit]=8101
    [color]=8102
    [fusion]=8103
    [fairlight]=8104
    [deliver]=8105
    [director]=8106
)

pids=()
for role in "${!TEAM[@]}"; do
    port="${TEAM[$role]}"
    echo "-> Starting $role on port $port"
    "$PY" "$MAIN" --role "$role" --transport http --port "$port" &
    pids+=($!)
done

cleanup() {
    echo ""
    echo "Stopping team..."
    for pid in "${pids[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

echo ""
echo "Agent team running. PIDs: ${pids[*]}"
wait
