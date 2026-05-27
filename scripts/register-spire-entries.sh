#!/bin/bash
# register-spire-entries.sh — Register SPIRE workload entries for SovereignStack services
# Run after SPIRE server is healthy.

set -euo pipefail

SPIRE_SERVER="${SPIRE_SERVER:-spire-server:8084}"
TRUST_DOMAIN="${TRUST_DOMAIN:-sovereign.stack}"
TTL="${TTL:-3600}"

# Gateway — any process running as the gateway service user
echo "Registering gateway workload entry..."
./bin/spire-server entry create \
    -serverAddress "$SPIRE_SERVER" \
    -parentID "spiffe://$TRUST_DOMAIN/spire/agent/join_token" \
    -spiffeID "spiffe://$TRUST_DOMAIN/service/gateway" \
    -selector "unix:uid:1001" \
    -ttl "$TTL"

# Memory service
echo "Registering memory workload entry..."
./bin/spire-server entry create \
    -serverAddress "$SPIRE_SERVER" \
    -parentID "spiffe://$TRUST_DOMAIN/spire/agent/join_token" \
    -spiffeID "spiffe://$TRUST_DOMAIN/service/memory" \
    -selector "unix:uid:1002" \
    -ttl "$TTL"

# Ingest service
echo "Registering ingest workload entry..."
./bin/spire-server entry create \
    -serverAddress "$SPIRE_SERVER" \
    -parentID "spiffe://$TRUST_DOMAIN/spire/agent/join_token" \
    -spiffeID "spiffe://$TRUST_DOMAIN/service/ingest" \
    -selector "unix:uid:1003" \
    -ttl "$TTL"

# Admin — allow management operations
echo "Registering admin workload entry..."
./bin/spire-server entry create \
    -serverAddress "$SPIRE_SERVER" \
    -parentID "spiffe://$TRUST_DOMAIN/spire/agent/join_token" \
    -spiffeID "spiffe://$TRUST_DOMAIN/admin" \
    -selector "unix:uid:0" \
    -ttl "$TTL"

echo "All workload entries registered."
echo ""
echo "Verify with: ./bin/spire-server entry list -serverAddress $SPIRE_SERVER"
