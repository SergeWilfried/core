# Multi-stage Dockerfile for BaaS Core Banking

# Stage 1: Build stage
FROM python:3.13-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime stage
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Create non-root user
RUN groupadd -r banking && useradd -r -g banking banking

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=banking:banking /app/.venv /app/.venv

# Copy application code
COPY --chown=banking:banking . .

# Switch to non-root user
USER banking

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run the application
CMD ["uvicorn", "core.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
