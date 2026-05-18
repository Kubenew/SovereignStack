#!/usr/bin/env bash
# =============================================================================
# OASA — OpenAI-Compatible Proxy Request Examples
# =============================================================================
# These examples demonstrate the drop-in replacement capability (Axiom 3).
# Simply change OPENAI_BASE_URL to your Sovereign Node and existing tooling
# (LangChain, AutoGPT, internal apps) works without code changes.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OASA_BASE_URL="${OPENAI_BASE_URL:-http://localhost:8080/v1}"
OASA_API_KEY="${OPENAI_API_KEY:-YOUR_API_KEY}"
OASA_MODEL="${OASA_MODEL:-sovereign-llama3-70b-turboquant}"

# ---------------------------------------------------------------------------
# 1. Chat Completion (non-streaming)
# ---------------------------------------------------------------------------
echo "==> Chat Completion (non-streaming)"
curl -s -X POST "${OASA_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OASA_API_KEY}" \
  -d '{
    "model": "'"${OASA_MODEL}"'",
    "messages": [
      {"role": "system", "content": "You are a confidential enterprise assistant running on a Sovereign Node."},
      {"role": "user", "content": "Summarize the key risks in our Q4 audit report."}
    ],
    "temperature": 0.3,
    "max_tokens": 1024,
    "oasa_compliance_lock": true,
    "oasa_audit_tag": "AUDIT-2026-00042"
  }' | python3 -m json.tool 2>/dev/null || true

echo ""

# ---------------------------------------------------------------------------
# 2. Chat Completion (streaming)
# ---------------------------------------------------------------------------
echo "==> Chat Completion (streaming)"
curl -s -N -X POST "${OASA_BASE_URL}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OASA_API_KEY}" \
  -d '{
    "model": "'"${OASA_MODEL}"'",
    "messages": [
      {"role": "user", "content": "List three GDPR compliance risks for AI-powered document processing."}
    ],
    "stream": true,
    "oasa_compliance_lock": true
  }'

echo ""
echo ""

# ---------------------------------------------------------------------------
# 3. Embeddings
# ---------------------------------------------------------------------------
echo "==> Embeddings"
curl -s -X POST "${OASA_BASE_URL}/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OASA_API_KEY}" \
  -d '{
    "model": "sovereign-embedding-v1",
    "input": "Confidential financial projection for FY2027."
  }' | python3 -m json.tool 2>/dev/null || true

echo ""

# ---------------------------------------------------------------------------
# 4. Health Check
# ---------------------------------------------------------------------------
echo "==> Health Check"
curl -s "${OASA_BASE_URL%/v1}/health" | python3 -m json.tool 2>/dev/null || true

echo ""
echo "Done. All requests routed through Sovereign Node at ${OASA_BASE_URL}"
