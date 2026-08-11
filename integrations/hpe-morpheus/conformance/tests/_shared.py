"""Shared request vectors for the OASA-MORPHEUS-CORE-0.1 conformance suite."""

COMPLIANT_SPEC = {
    "cpu": 8,
    "memory_gb": 32,
    "network": "prod-vlan-42",
    "image": "ubuntu-22.04-lts",
    "environment": "production",
}

OVERSIZED_SPEC = {
    "cpu": 64,
    "memory_gb": 512,
    "network": "unapproved-network",
    "image": "ubuntu-22.04-lts",
    "environment": "production",
}

PROD_NET_DEV_ENV = {
    "cpu": 8,
    "memory_gb": 32,
    "network": "prod-vlan-42",
    "image": "ubuntu-22.04-lts",
    "environment": "dev",
}

DEFAULT_QUOTA = {"cpu_remaining": 16, "memory_gb_remaining": 64, "running_vms": 3}

AGENT_URI = "agent://ml-platform"
COMPUTE_PROVISION = "capability://compute/provision"
