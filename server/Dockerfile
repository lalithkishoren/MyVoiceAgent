# Multi-stage Docker build for Sutherland Voice Agent Server
# Optimized for production deployment

# =============================================================================
# Build Stage
# =============================================================================
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Production Stage
# =============================================================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    PYTHONPATH="/app/src:$PYTHONPATH"

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory and set ownership
RUN mkdir -p /app/src /app/logs && \
    chown -R appuser:appuser /app

# Switch to app directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser .env.example ./

# Create .env file from example if it doesn't exist
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Switch to non-root user
USER appuser

# Expose ports
# 8080: WebSocket server
# 8081: HTTP API server
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Default command
CMD ["python", "src/main.py"]

# =============================================================================
# Development Stage (optional)
# =============================================================================
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    ipython \
    debugpy \
    pytest-cov

# Switch back to appuser
USER appuser

# Override command for development
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "src/main.py"]

# =============================================================================
# Labels and Metadata
# =============================================================================
LABEL maintainer="Sutherland Voice Agent Team" \
      version="1.0.0" \
      description="Sutherland Voice Agent Server - Self-hosted WebRTC voice agent backend" \
      org.opencontainers.image.title="Sutherland Voice Agent Server" \
      org.opencontainers.image.description="Self-hosted WebRTC voice agent backend powered by Pipecat" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Pipecat" \
      org.opencontainers.image.licenses="MIT"

# =============================================================================
# Build Arguments and Environment Variables
# =============================================================================
ARG BUILD_DATE
ARG GIT_COMMIT
ARG VERSION=1.0.0

ENV BUILD_DATE=${BUILD_DATE} \
    GIT_COMMIT=${GIT_COMMIT} \
    VERSION=${VERSION}