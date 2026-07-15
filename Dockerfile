# Stage 1: Base
FROM python:3.12-slim AS base

WORKDIR /app

# Install curl for healthcheck & build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /uvx /bin/

# Copy config files
COPY pyproject.toml uv.lock ./

# Setup virtual environment
ENV UV_PROJECT_ENVIRONMENT=/venv
RUN uv sync --frozen --no-install-project --no-dev


# Stage 2: Dev
FROM base AS dev

# Sync development dependencies
RUN uv sync --frozen --no-install-project

# Copy project files
COPY . .

ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Stage 3: Prod
FROM base AS prod

# Copy project files
COPY . .

# Sync all dependencies including current project
RUN uv sync --frozen

# Create system user & group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && chown -R appuser:appgroup /app /venv

USER appuser

ENV PATH="/venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
