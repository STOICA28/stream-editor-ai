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
COPY apps/api/ ./apps/api/

# Install dependencies (frozen, no dev)
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "stream_editor.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
