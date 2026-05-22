#!/usr/bin/env python3
"""
SovereignStack — Client Integration Example
============================================

Demonstrates how standard client libraries (e.g. LangChain, OpenAI Python SDK)
can route completions to a SovereignStack node by modifying the API endpoint,
supplying the OASA Compliance Lock, and attaching OIDC/OpenTelemetry headers.
"""

import os
import sys
import json
import requests

def run_sovereign_completion():
    print("=================================================================")
    print("  OASA Sovereign Client Integration Simulator")
    print("=================================================================")

    # 1. Base URL override (pointing to local gateway proxy)
    gateway_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8080/v1")
    endpoint = f"{gateway_url}/chat/completions"

    # 2. OIDC Token & OpenTelemetry Trace Headers
    # In production, retrieve the token from a local OIDC OAuth2 client flow
    bearer_token = os.getenv("OASA_OIDC_TOKEN", "mock-valid-token")
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "x-trace-id": "4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d", # Correlates logs
        "x-span-id": "9f8e7d6c5b4a3210",
        "Content-Type": "application/json"
    }

    # 3. Payload with OASA Compliance Extensions
    payload = {
        "model": "sovereign-llama3",
        "messages": [
            {
                "role": "system", 
                "content": "You are a private LLM bound by strict regional jurisdiction rules."
            },
            {
                "role": "user", 
                "content": "Process this confidential report: Local disk storage must remain encrypted."
            }
        ],
        # Compliance Lock (Essential to prevent silent WAN failover to public cloud APIs)
        "oasa_compliance_lock": True,
        # Audit logging tag to associate requests with regulatory compliance cases
        "oasa_audit_tag": "AUDIT-CASE-4096-GDPR",
        # Region verification requirement
        "oasa_jurisdiction": "EU-GDPR"
    }

    print(f"Targeting Gateway Endpoint: {endpoint}")
    print(f"Headers:\n  Authorization: Bearer [REDACTED]\n  x-trace-id: {headers['x-trace-id']}")
    print(f"Request Payload (OASA Extensions Active):\n{json.dumps(payload, indent=2)}")
    print("-" * 65)

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=5)
        print(f"Gateway Response Code: {response.status_code}")
        
        if response.status_code == 200:
            res_json = response.json()
            answer = res_json["choices"][0]["message"]["content"]
            print(f"\nModel Answer:\n{answer}\n")
            print("Audit Log Reference ID:", res_json.get("id"))
            return 0
        else:
            print(f"\n[ERROR] Request rejected by Sovereign Gateway:")
            print(response.text)
            return 1
            
    except requests.exceptions.ConnectionError:
        print("\n[CONNECTION ERROR] Sovereign Gateway service is offline.")
        print("Start the services first: docker-compose up -d")
        return 1

if __name__ == "__main__":
    sys.exit(run_sovereign_completion())
