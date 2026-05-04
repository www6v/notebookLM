# MinerU + small FastAPI gateway. Build is heavy (torch/layout deps).
# For GPU hosts, use NVIDIA Container Toolkit and a CUDA base if needed.
FROM python:3.11-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MINERU_MODEL_SOURCE=modelscope

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
    && pip install --force-reinstall --no-cache-dir \
        torch==2.2.2 torchvision==0.17.2 \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -c "import torch; assert hasattr(torch, 'Tensor')" \
    && python -c "from importlib.metadata import version; print('mineru', version('mineru'))"

COPY app ./app

EXPOSE 8765

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8765"]
