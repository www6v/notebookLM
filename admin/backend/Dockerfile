# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

ARG PIP_DEFAULT_TIMEOUT=180
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT} \
    PIP_INDEX_URL=${PIP_INDEX_URL}

# Install shared package (for layer caching, copy before source)
COPY shared /shared
RUN pip install /shared

# Install admin backend runtime dependencies
# notebooklm-shared is already installed above; pyproject [tool.uv.sources]
# is for local dev only — Docker installs shared from /shared first.
COPY admin/backend/pyproject.toml /tmp/pyproject.toml
RUN pip install \
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
