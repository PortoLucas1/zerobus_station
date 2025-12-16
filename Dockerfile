FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./
COPY databricks_zerobus-0.0.17-py3-none-any.whl ./

RUN pip install --upgrade pip && \
    pip install fastapi uvicorn python-dotenv grpcio protobuf requests && \
    pip install databricks_zerobus-0.0.17-py3-none-any.whl

COPY app.py stream_manager.py config.json ./
COPY tables/ ./tables/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
