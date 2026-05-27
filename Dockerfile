# =============================================================================
# SovereignStack — Multi-stage Production Dockerfile
# Reproducibility: pin base images via digest, hash-pin Python dependencies
# =============================================================================
# Stage 1: Build dependencies
# Pin base image digest: use `docker pull python:3.11.11-slim@sha256:...` and verify
FROM python:3.11.11-slim@sha256:2c0e7d4f6a1b8c9d0e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c AS builder

WORKDIR /app
COPY requirements-locked.txt requirements.txt
RUN pip install --no-cache-dir --user --require-hashes -r requirements-locked.txt

# Stage 2: Production runtime
FROM python:3.11.11-slim@sha256:2c0e7d4f6a1b8c9d0e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c AS runtime

# Security: run as non-root
RUN groupadd -r sovereign && useradd -r -g sovereign -d /app -s /sbin/nologin sovereign

WORKDIR /app

# Copy only installed packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create data directories with correct permissions
RUN mkdir -p /app/data /app/data/ingest /app/data/memory /app/data/audit && \
    chown -R sovereign:sovereign /app/data

USER sovereign

EXPOSE 8080 8081 8082 8083

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
