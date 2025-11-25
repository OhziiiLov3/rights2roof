FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv uvicorn fastapi slack-sdk redis aiohttp

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen || pip install fastapi slack-sdk redis aiohttp

COPY app/ app/
COPY app/resources/files app/resources/files
COPY . .

# Default command (can be overridden in Railway service)
CMD ["uvicorn", "app.services.slack_webhook:app", "--host", "0.0.0.0", "--port", "8000"]
