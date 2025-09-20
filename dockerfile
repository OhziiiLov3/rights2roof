FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


#dont save the downloaded package files
RUN pip install --no-cache-dir uv


WORKDIR /app


#copy our lock files
COPY pyproject.toml uv.lock ./

#our lockfiles dont change so this way we can use the same lock files for both the mcp server and our slack webhook service
RUN uv sync --frozen --no-cache

COPY . .

