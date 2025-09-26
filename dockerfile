FROM python:3.11-slim

# Avoid Python writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install build deps and uv/uvicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv uvicorn

WORKDIR /app

# Copy lockfiles first (for Docker caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache || pip install fastapi slack-sdk redis aiohttp

# Copy application code
COPY app/ app/
COPY . .

# Default command (overridden by docker-compose per service)
CMD ["uvicorn", "app.services.slack_webhook:app", "--host", "0.0.0.0", "--port", "8000"]
