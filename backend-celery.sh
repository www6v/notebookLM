#!/bin/bash

# Script directory = repo root (same level as root .env). App reads that .env
# via backend/app/config.py; cwd must be backend for imports and local startup.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend" || exit 1

if [ -x "$PWD/.venv/bin/python" ]; then
    PYTHON_BIN="$PWD/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "Python is required to start the Celery worker."
    exit 1
fi

# Preferred runtime environment source.
if [ -f "$PWD/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PWD/.env"
    set +a
fi

"$PYTHON_BIN" -m celery -A app.tasks.celery_app:celery_app \
    worker --loglevel=info
