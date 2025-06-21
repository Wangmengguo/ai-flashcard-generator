# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder stage
COPY --from=builder /venv /venv

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser index.html .
COPY --chown=appuser:appuser local_index.html .
COPY --chown=appuser:appuser logging.json .
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser docker-health-check.sh ./

# Create logs directory
RUN mkdir -p /app/logs && chown appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s \
  --start-period=5s --retries=3 \
  CMD ./docker-health-check.sh quick || exit 1

# Expose port
EXPOSE 8000

# Start the application
# Use uvicorn with built-in multiprocess support (recommended for 2025)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log", "--log-config", "/app/logging.json"]