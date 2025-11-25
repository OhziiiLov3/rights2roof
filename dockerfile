FROM python:3.11-slim

# Avoid Python writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install build deps and uv/uvicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv uvicorn fastapi slack-sdk redis aiohttp

WORKDIR /app

# Copy lockfiles first (for Docker caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache || pip install fastapi slack-sdk redis aiohttp fastmcp

# Copy application code
COPY app/ app/
# Make sure your PDFs are included
COPY app/resources/files app/resources/files
COPY . .

# Default command; overridden in docker-compose for specific services
CMD ["uvicorn", "app.services.slack_webhook:app", "--host", "0.0.0.0", "--port", "8000"]