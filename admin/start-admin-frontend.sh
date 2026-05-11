#!/bin/bash

# Start admin Vite dev server. Run from anywhere; cwd becomes admin/frontend.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend" || exit 1

if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to start the admin frontend."
    exit 1
fi

npm run dev
