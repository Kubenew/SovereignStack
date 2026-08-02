FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY libs/ss-core/ /app/libs/ss-core/
COPY libs/ss-crypto/ /app/libs/ss-crypto/
COPY libs/ss-cas/ /app/libs/ss-cas/
COPY gateway/ /app/gateway/

RUN pip install --no-cache-dir \
    /app/libs/ss-core \
    /app/libs/ss-crypto \
    /app/libs/ss-cas \
    /app/gateway

# Create data directory
RUN mkdir -p /app/oasa-data

ENV OASA_HOST=0.0.0.0
ENV OASA_PORT=8080
ENV OASA_DATA_DIR=/app/oasa-data
ENV OASA_KEYPAIR_PATH=/app/oasa-data/gateway-key.json

EXPOSE 8080

CMD ["uvicorn", "oasa_gateway.app:app", "--host", "0.0.0.0", "--port", "8080"]
