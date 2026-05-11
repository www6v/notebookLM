# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ARG UV_HTTP_TIMEOUT=180
ARG UV_HTTP_RETRIES=5
ARG UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple

# Align with backend/Dockerfile: PyPI mirror + timeouts (pip compatibility + uv).
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=${UV_HTTP_TIMEOUT} \
    PIP_INDEX_URL=${UV_DEFAULT_INDEX} \
    UV_DEFAULT_INDEX=${UV_DEFAULT_INDEX} \
    UV_HTTP_TIMEOUT=${UV_HTTP_TIMEOUT} \
    UV_HTTP_RETRIES=${UV_HTTP_RETRIES}

# Install uv from official image (avoids `pip install uv` when PyPI is unreachable).
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

# Install shared package (for layer caching, copy before source)
COPY shared /shared
RUN uv pip install --system /shared

# Install admin backend runtime dependencies
# notebooklm-shared is already installed above; the [tool.uv.sources] path entry
# is a local-dev hint only — we skip it here by not running `uv pip install -e .`
COPY admin/backend/pyproject.toml /tmp/pyproject.toml
RUN uv pip install --system \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "pydantic>=2.10.0" \
    "email-validator>=2.1.0" \
    "python-multipart>=0.0.18"

# Copy admin backend source (uvicorn resolves app.main via WORKDIR in sys.path)
COPY admin/backend/ .

# Tell config.py where to find config.yaml (mounted by docker-compose)
ENV NOTEBOOKLM_CONFIG_PATH=/app/config.yaml

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
