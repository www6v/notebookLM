# syntax=docker/dockerfile:1.7
# Supplier stage: COPY --from only accepts a fixed stage name here (ARG in
# --from is not expanded on some BuildKit/docker versions).
ARG BUN_IMAGE=oven/bun:latest
FROM ${BUN_IMAGE} AS bun_upstream

# Compile wheels and install deps; final image drops build toolchain.
FROM python:3.11-slim AS builder

WORKDIR /app

ARG UV_HTTP_TIMEOUT=180
ARG UV_HTTP_RETRIES=5
ARG UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=${UV_HTTP_TIMEOUT} \
    PIP_INDEX_URL=${UV_DEFAULT_INDEX}

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml ./
RUN python -c "from pathlib import Path; import tomllib; pyproject = tomllib.loads(Path('pyproject.toml').read_text()); dependencies = pyproject['project']['dependencies']; Path('requirements.docker.txt').write_text('\\n'.join(dependencies) + '\\n')"
# rapidocr declares opencv-python; keep a single headless install for smaller
# wheels and no GUI stack. Uninstall then force-reinstall headless restores cv2.
RUN python -m pip install --retries ${UV_HTTP_RETRIES} -r requirements.docker.txt \
    && (python -m pip uninstall -y opencv-python || true) \
    && python -m pip install --no-cache-dir --force-reinstall \
        'opencv-python-headless>=4.8.0,<4.13'


FROM python:3.11-slim

WORKDIR /app

ARG UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=${UV_DEFAULT_INDEX} \
    PATH="/opt/venv/bin:$PATH"

# Runtime libs only (no compiler). libpq-dev removed: stack uses MySQL async.
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    libglib2.0-0 \
    libgomp1 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY --from=bun_upstream /usr/local/bin/bun /usr/local/bin/bun
RUN ln -sf bun /usr/local/bin/bunx

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
