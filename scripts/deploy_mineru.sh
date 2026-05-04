#!/usr/bin/env bash
# Build and start the MinerU HTTP gateway (NotebookLM-compatible /v1/parse).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATEWAY_DIR="${ROOT}/services/mineru-gateway"
PORT="${MINERU_GATEWAY_PORT:-8765}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required. Install Docker Desktop or the Docker Engine CLI." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose v2 is required." >&2
  exit 1
fi

echo "==> Building MinerU gateway image (first run may take a long time)..."
cd "${GATEWAY_DIR}"
docker compose build

echo "==> Starting service on port ${PORT}..."
docker compose up -d

echo ""
echo "Gateway URL (set as notebookLM mineru_base_url):"
echo "  http://127.0.0.1:${PORT}"
echo ""
echo "Health check:"
curl -sf "http://127.0.0.1:${PORT}/health" && echo "" || {
  echo "Health check failed; see: docker compose -f ${GATEWAY_DIR}/docker-compose.yml logs -f" >&2
  exit 1
}

echo ""
echo "Optional: set MINERU_GATEWAY_API_KEY in docker-compose env and MINERU_API_KEY in notebookLM config."
echo "Stop with: cd ${GATEWAY_DIR} && docker compose down"
