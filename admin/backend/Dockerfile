FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

# Copy and install shared package first (for layer caching)
COPY ../shared /shared
RUN uv pip install --system /shared

# Install admin backend dependencies
COPY backend/pyproject.toml .
RUN uv pip install --system -e .

# Copy admin backend source
COPY backend/ .

# Tell config.py where to find config.yaml (mounted by docker-compose)
ENV NOTEBOOKLM_CONFIG_PATH=/app/config.yaml

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
