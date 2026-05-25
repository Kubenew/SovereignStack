"""
Runtime Shield & Exfiltration Prevention Tests — OASA Conformance L1/L2
"""

import pytest
import socket
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_network_policy_exists():
    """Verify that a NetworkPolicy manifest exists for air-gap enforcement."""
    k8s_dir = Path(__file__).resolve().parent.parent.parent / "k8s"
    policy_files = [
        k8s_dir / "sovereign-network-policy.yaml",
        k8s_dir / "network-policy.yaml",
    ]
    found = any(f.exists() for f in policy_files)
    assert found, f"No network policy found in {k8s_dir}"


def test_helm_network_policy_exists():
    """Verify the Helm chart includes a NetworkPolicy template."""
    helm_dir = Path(__file__).resolve().parent.parent.parent / "charts/sovereignstack/templates"
    policy_file = helm_dir / "network-policy.yaml"
    assert policy_file.exists(), f"Helm NetworkPolicy template not found at {policy_file}"


@patch("socket.create_connection")
def test_network_isolation_detection(mock_connect):
    """Runtime shield must detect when network isolation is breached."""
    from tools.runtime_shield import RuntimeShield

    mock_connect.side_effect = OSError("Connection blocked")
    shield = RuntimeShield.__new__(RuntimeShield)
    shield.air_gapped = True
    shield.mem_threshold_mb = 512
    shield.compliance_lock = True

    result = shield.verify_network_isolation()
    assert result is True, f"Expected True (isolated), got {result}"


@patch("socket.create_connection")
def test_network_isolation_breach(mock_connect):
    """Runtime shield must identify when network isolation is breached."""
    from tools.runtime_shield import RuntimeShield

    mock_connect.return_value = MagicMock()
    shield = RuntimeShield.__new__(RuntimeShield)
    shield.air_gapped = True
    shield.mem_threshold_mb = 512
    shield.compliance_lock = True

    result = shield.verify_network_isolation()
    assert result is False, f"Expected False (breach detected), got {result}"


@pytest.mark.level("L2")
def test_exfiltration_blocked_domains():
    """Verify the blocked AI API domains list is comprehensive."""
    from tools.sovereign_stack import BLOCKED_DOMAINS

    required_domains = [
        "api.openai.com",
        "api.anthropic.com",
        "api.cohere.ai",
        "api.mistral.ai",
        "api.deepseek.com",
    ]
    for domain in required_domains:
        assert domain in BLOCKED_DOMAINS, f"Missing required blocked domain: {domain}"
    assert len(BLOCKED_DOMAINS) >= 10, "Blocked domains list should have 10+ entries"
