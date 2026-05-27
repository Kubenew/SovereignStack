# Production Deployment Templates

This directory contains production-ready deployment configurations for SovereignStack.

---

## Contents

| Template | Profile | Description |
|---|---|---|
| [docker-compose.prod.yml](docker-compose.prod.yml) | Air-Gapped | Production Docker Compose with resource limits |
| [prometheus.yml](prometheus.yml) | All | Prometheus scrape config |
| [otel-collector.yml](otel-collector.yml) | All | OpenTelemetry pipeline |

---

## Usage

```bash
# Production deployment
docker compose -f deploy/docker-compose.prod.yml up -d

# With custom env
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod up -d
```

---

## Profiles

See [Deployment Profiles](/docs/deployment/profiles.md) for details on Edge, Air-Gapped, Datacenter, and Personal profiles.
