# =============================================================================
# SovereignStack — Multi-stage Production Dockerfile
# =============================================================================
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runtime
FROM python:3.11-slim AS runtime

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
