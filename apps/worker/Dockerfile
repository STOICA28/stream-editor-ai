FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace files for dependency resolution
COPY pyproject.toml uv.lock* ./
COPY packages/ ./packages/
COPY apps/worker/ ./apps/worker/

# Install dependencies (frozen, no dev)
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "celery", "-A", "stream_editor.worker.celery_app", "worker", "--loglevel=info"]
