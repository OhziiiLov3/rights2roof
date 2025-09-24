FROM python:3.11-slim

# Avoid Python writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install OS dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# Ensure Poetry is in the PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy lockfiles first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Copy application source code
COPY app/ app/

# Default command (can be overridden)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
