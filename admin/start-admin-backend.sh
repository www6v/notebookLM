#!/bin/bash

# Start admin FastAPI (dev). Run from anywhere; cwd becomes admin/backend.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend" || exit 1

if [ -f "$PWD/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PWD/.env"
    set +a
fi

ADMIN_PORT="${ADMIN_PORT:-8001}"

# Optional first argument overrides ADMIN_PORT for this run (1–65535).
if [ -n "${1:-}" ]; then
    if [[ "$1" =~ ^[0-9]+$ ]] && ((10#$1 >= 1 && 10#$1 <= 65535)); then
        ADMIN_PORT="$1"
    else
        echo "Usage: $(basename "$0") [PORT]" >&2
        echo "  PORT: 1-65535, optional. Else use ADMIN_PORT or default 8001." >&2
        echo "  Example: ADMIN_PORT=8020 $(basename "$0")   or   $(basename "$0") 8020" >&2
        exit 1
    fi
fi

echo "Starting admin API on 0.0.0.0:${ADMIN_PORT} (set ADMIN_PORT or pass PORT as first arg)"

if command -v uv >/dev/null 2>&1; then
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port "$ADMIN_PORT"
elif [ -x "$PWD/.venv/bin/python" ]; then
    "$PWD/.venv/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$ADMIN_PORT"
elif command -v python3 >/dev/null 2>&1; then
    "$(command -v python3)" -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$ADMIN_PORT"
else
    echo "Need uv or Python 3 with uvicorn in admin/backend (.venv)."
    exit 1
fi
