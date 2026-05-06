# syntax=docker/dockerfile:1.7
# Supplier stage: COPY --from only accepts a fixed stage name here (ARG in
# --from is not expanded on some BuildKit/docker versions).
ARG BUN_IMAGE=oven/bun:latest
FROM ${BUN_IMAGE} AS bun_upstream

FROM python:3.11-slim

WORKDIR /app

ARG UV_HTTP_TIMEOUT=180
ARG UV_HTTP_RETRIES=5
ARG UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=${UV_HTTP_TIMEOUT} \
    PIP_INDEX_URL=${UV_DEFAULT_INDEX}

# Install system dependencies (use Aliyun mirror for China)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    curl \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies from pyproject.toml without uv
COPY pyproject.toml ./
RUN python -c "from pathlib import Path; import tomllib; pyproject = tomllib.loads(Path('pyproject.toml').read_text()); dependencies = pyproject['project']['dependencies']; Path('requirements.docker.txt').write_text('\\n'.join(dependencies) + '\\n')"
RUN python -m pip install --retries ${UV_HTTP_RETRIES} -r requirements.docker.txt

# Bun for slide-deck merge scripts: copy binary from bun_upstream (see top).
COPY --from=bun_upstream /usr/local/bin/bun /usr/local/bin/bun
RUN ln -sf bun /usr/local/bin/bunx

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
