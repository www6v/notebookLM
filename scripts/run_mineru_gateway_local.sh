#!/usr/bin/env bash
# Run MinerU gateway with local venv (no Docker). Requires: pip install -r backend/mineru-gateway/requirements.txt
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GW="${ROOT}/backend/mineru-gateway"
VENV="${GW}/.venv"
PORT="${MINERU_GATEWAY_PORT:-8765}"

# PyTorch has no cp313+ wheels on some platforms (e.g. macOS x86_64). Conda ``base`` often
# exposes ``python3`` as 3.13; prefer 3.12/3.11 so ``pip install torch`` can resolve.
pick_mineru_python() {
  if [[ -n "${MINERU_GATEWAY_PYTHON:-}" ]]; then
    if command -v "${MINERU_GATEWAY_PYTHON}" >/dev/null 2>&1; then
      echo "${MINERU_GATEWAY_PYTHON}"
      return 0
    fi
    echo "MINERU_GATEWAY_PYTHON=${MINERU_GATEWAY_PYTHON} not found in PATH." >&2
    exit 1
  fi
  local cand
  for cand in python3.12 python3.11 python3.10; do
    if command -v "${cand}" >/dev/null 2>&1; then
      echo "${cand}"
      return 0
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    local major minor
    major="$(python3 -c 'import sys; print(sys.version_info.major)')"
    minor="$(python3 -c 'import sys; print(sys.version_info.minor)')"
    if (( major > 3 || (major == 3 && minor >= 13) )); then
      echo "python3 is ${major}.${minor}; no PyTorch wheel for this interpreter on many hosts." >&2
      echo "Install Python 3.11 or 3.12, or set MINERU_GATEWAY_PYTHON to that executable." >&2
      exit 1
    fi
    echo python3
    return 0
  fi
  echo "No python3 found in PATH." >&2
  exit 1
}

PY_BIN="$(pick_mineru_python)"
if [[ -d "${VENV}/bin" && -x "${VENV}/bin/python" ]]; then
  v_maj="$("${VENV}/bin/python" -c 'import sys; print(sys.version_info.major)')"
  v_min="$("${VENV}/bin/python" -c 'import sys; print(sys.version_info.minor)')"
  if (( v_maj > 3 || (v_maj == 3 && v_min >= 13) )); then
    echo "Existing ${VENV} uses Python ${v_maj}.${v_min}; remove it and re-run:" >&2
    echo "  rm -rf \"${VENV}\"" >&2
    exit 1
  fi
fi

if [[ ! -d "${VENV}" ]]; then
  "${PY_BIN}" -m venv "${VENV}"
fi
# shellcheck source=/dev/null
source "${VENV}/bin/activate"
pip install -q -r "${GW}/requirements.txt" || {
  echo "pip install failed (e.g. disk full or index without torch). Install Docker and use ./scripts/deploy_mineru.sh instead." >&2
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
