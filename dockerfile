FROM python:3.11-slim

# Avoid Python writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install uv via pip
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy lockfiles first (for Docker caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-cache

# Copy application code
COPY app/ app/
COPY . .

# Default command (can still be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "app.services.slack_webhook:app", "--host", "0.0.0.0", "--port", "8000"]
