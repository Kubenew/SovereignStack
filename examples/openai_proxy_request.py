#!/usr/bin/env python3
"""
OASA — OpenAI-Compatible Proxy Request (Python)
================================================

Demonstrates Axiom 3 (API Idempotency): the official ``openai`` Python SDK
works unchanged against a Sovereign Node.  Just set the base URL.

Usage:
    pip install openai
    export OPENAI_BASE_URL="http://localhost:8080/v1"
    export OPENAI_API_KEY="your-key"
    python openai_proxy_request.py

Alternatively, use plain ``requests`` (no SDK dependency) — see the
``requests_example()`` function below.
"""

from __future__ import annotations

import json
import os
import sys

# ── Configuration ────────────────────────────────────────────────────────────
OASA_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1")
OASA_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
OASA_MODEL = os.getenv("OASA_MODEL", "sovereign-llama3-70b-turboquant")


# ── Example 1: Using the official OpenAI SDK ─────────────────────────────────
def openai_sdk_example() -> None:
    """Chat completion via the official openai package."""
    try:
        from openai import OpenAI  # noqa: WPS433
    except ImportError:
        print("⚠  'openai' package not installed. Run: pip install openai")
        return

    client = OpenAI(
        base_url=OASA_BASE_URL,
        api_key=OASA_API_KEY,
    )

    print("─── OpenAI SDK: Chat Completion ───")
    response = client.chat.completions.create(
        model=OASA_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a confidential enterprise assistant running "
                    "on a Sovereign Node."
                ),
            },
            {
                "role": "user",
                "content": "Summarize the key risks in our Q4 audit report.",
            },
        ],
        temperature=0.3,
        max_tokens=1024,
        extra_body={
            "oasa_compliance_lock": True,
            "oasa_audit_tag": "AUDIT-2026-00042",
        },
    )

    print(f"Model:  {response.model}")
    print(f"Usage:  {response.usage}")
    print(f"Answer: {response.choices[0].message.content[:200]}...")
    print()


# ── Example 2: Using plain requests (no SDK dependency) ─────────────────────
def requests_example() -> None:
    """Chat completion via the standard requests library."""
    try:
        import requests  # noqa: WPS433
    except ImportError:
        print("⚠  'requests' package not installed. Run: pip install requests")
        return

    print("─── Requests: Chat Completion ───")
    resp = requests.post(
        f"{OASA_BASE_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OASA_API_KEY}",
        },
        json={
            "model": OASA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "List three GDPR compliance risks for AI-powered "
                        "document processing."
                    ),
                },
            ],
            "temperature": 0.5,
            "max_tokens": 512,
            "oasa_compliance_lock": True,
            "oasa_jurisdiction": "EU-GDPR",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data, indent=2))
    print()


# ── Example 3: Embeddings ───────────────────────────────────────────────────
def embeddings_example() -> None:
    """Generate embeddings for confidential text."""
    try:
        import requests  # noqa: WPS433
    except ImportError:
        print("⚠  'requests' package not installed.")
        return

    print("─── Requests: Embeddings ───")
    resp = requests.post(
        f"{OASA_BASE_URL}/embeddings",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OASA_API_KEY}",
        },
        json={
            "model": "sovereign-embedding-v1",
            "input": "Confidential financial projection for FY2027.",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    vector = data["data"][0]["embedding"]
    print(f"Dimensions: {len(vector)}")
    print(f"Preview:    {vector[:5]}...")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"OASA Sovereign Node: {OASA_BASE_URL}")
    print(f"Model:               {OASA_MODEL}")
    print()

    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("sdk", "all"):
        openai_sdk_example()
    if mode in ("requests", "all"):
        requests_example()
    if mode in ("embeddings", "all"):
        embeddings_example()

    print("✓ All requests routed through the Sovereign Node.")
