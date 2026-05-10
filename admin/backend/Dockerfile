FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

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
