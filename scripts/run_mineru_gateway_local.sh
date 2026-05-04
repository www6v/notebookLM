#!/usr/bin/env bash
# Run MinerU gateway with local venv (no Docker). Requires: pip install -r services/mineru-gateway/requirements.txt
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GW="${ROOT}/services/mineru-gateway"
VENV="${GW}/.venv"
PORT="${MINERU_GATEWAY_PORT:-8765}"

if [[ ! -d "${VENV}" ]]; then
  python3 -m venv "${VENV}"
fi
# shellcheck source=/dev/null
source "${VENV}/bin/activate"
pip install -q -r "${GW}/requirements.txt" || {
  echo "pip install failed (e.g. disk full). Install Docker and use ./scripts/deploy_mineru.sh instead." >&2
  exit 1
}

cd "${GW}"
# Pipeline weights default to Hugging Face; many networks cannot reach it.
# ModelScope hosts the same OpenDataLab kit — override with MINERU_MODEL_SOURCE=huggingface if needed.
if [[ -z "${MINERU_MODEL_SOURCE:-}" ]]; then
  export MINERU_MODEL_SOURCE=modelscope
fi
# macOS: MinerU pipeline often hits MPS OOM (Metal memory cap). Default to CPU
# like docker-compose unless the user already chose a device.
if [[ "$(uname -s)" == "Darwin" ]]; then
  if [[ -z "${MINERU_GATEWAY_DEVICE:-}" && -z "${MINERU_DEVICE_MODE:-}" ]]; then
    export MINERU_GATEWAY_DEVICE=cpu
  fi
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
