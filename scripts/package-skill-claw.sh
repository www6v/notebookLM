#!/usr/bin/env bash
# Package skill-claw for Agent Interface download (frontend/public/skills).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(node -e "console.log(require('$ROOT/skill-claw/meta.json').version)")"
OUT_DIR="$ROOT/frontend/public/skills"
OUT_ZIP="$OUT_DIR/notebooklm-skills-${VERSION}.zip"

mkdir -p "$OUT_DIR"
rm -f "$OUT_ZIP"
(
  cd "$ROOT/skill-claw"
  zip -r "$OUT_ZIP" . -x '*.DS_Store' -x '__MACOSX/*'
)

echo "Created $OUT_ZIP ($(du -h "$OUT_ZIP" | cut -f1))"
