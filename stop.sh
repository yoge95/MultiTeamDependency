#!/bin/bash
# stop.sh — Stop ONLY the services started by start.sh (uses .pids file)
# IMPORTANT: Only kills PIDs recorded in .pids — never uses pkill/killall
# which could accidentally kill other processes (e.g. the SDLC backend server).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Stopping Multi-team Knowledge Assistant services..."

if [ -f .pids ]; then
    while IFS= read -r pid; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && echo "  ✓ Stopped PID $pid" || echo "  ⚠ PID $pid already stopped"
        fi
    done < .pids
    rm -f .pids
    echo ""
    echo "All services stopped successfully"
else
    echo "No .pids file found — services may not be running or were stopped already"
fi
