import os
import sys
import json
import yaml
import pytest
from pathlib import Path
from argparse import Namespace
from unittest.mock import patch, MagicMock

# Add tools to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from tools.sovereign_stack import cmd_validate, audit_host_infrastructure

@pytest.fixture
def temp_files(tmp_path):
    # Create sample configuration files for testing schema auto-detection
    stack_yaml = tmp_path / "sovereign-stack.yaml"
    stack_data = {
        "oasa_version": "2026.1",
        "node": {
            "name": "test-node",
            "air_gapped": True,
            "tpm_required": False,
            "encryption": "AES-256-GCM",
            "sandboxing": {
                "runtime": "none",
                "confidential_compute": False
            }
        },
        "services": {
            "gateway": {
                "enabled": True,
                "listen": "0.0.0.0:8080",
                "identity": {
                    "enabled": False,
                    "provider": "mock",
                    "issuer_url": "http://mock",
                    "client_id": "mock"
                },
                "policy": {
                    "enabled": False,
                    "engine": "mock",
                    "policy_path": "mock"
                },
                "observability": {
                    "enabled": False,
                    "opentelemetry_endpoint": "http://mock",
                    "prometheus_enabled": False
                }
            },
            "ingest": {
                "enabled": True,
                "listen": "0.0.0.0:8081"
            },
            "memory": {
                "enabled": True,
                "listen": "0.0.0.0:8082",
                "vector_backend": "local-json"
            },
            "compute": {
                "enabled": True,
                "listen": "0.0.0.0:8083",
                "backend": "local",
                "vram_budget_gb": 24,
                "registry": {
                    "enabled": False,
                    "registry_url": "http://mock",
                    "require_signed_weights": False
                }
            }
        },
        "models": {
            "allowed": ["test-model"]
        }
    }
    with open(stack_yaml, "w", encoding="utf-8") as f:
        yaml.dump(stack_data, f)

    compliance_json = tmp_path / "compliance.json"
    compliance_data = {
        "oasa_version": "2026.1",
        "enforce_zero_exfiltration": True,
        "oasa_compliance_lock": True,
        "compliance_level": "STRICT",
        "air_gapped": True,
        "encryption": {
            "algorithm": "AES-256-GCM",
            "key_management": "TPM_2.0",
            "key_rotation_days": 90
        },
        "compute": {
            "vram_budget_gb": 24
        }
    }
    with open(compliance_json, "w", encoding="utf-8") as f:
        json.dump(compliance_data, f)

    node_manifest = tmp_path / "node-manifest.json"
    node_data = {
        "node_id": "sn-0a1b2c3d4e5f",
        "hostname": "test-host",
        "oasa_version": "2026.1",
        "location": {
            "country_code": "US",
            "jurisdiction": "US-HIPAA"
        },
        "hardware": {
            "ram_gb": 32,
            "tpm_present": True
        }
    }
    with open(node_manifest, "w", encoding="utf-8") as f:
        json.dump(node_data, f)

    return {
        "stack_yaml": stack_yaml,
        "compliance_json": compliance_json,
        "node_manifest": node_manifest
    }

def test_schema_auto_detection_stack(temp_files):
    # Testing that sovereign-stack.yaml auto-detects sovereign-stack.schema.json
    args = Namespace(files=[str(temp_files["stack_yaml"])], schema=None, audit_host=False)
    
    with patch("tools.sovereign_stack.print") as mock_print:
        exit_code = cmd_validate(args)
        assert exit_code == 0
        
        # Check if the printed schema matches sovereign-stack.schema.json
        any_schema_check = any("sovereign-stack.schema.json" in str(call) for call in mock_print.mock_calls)
        assert any_schema_check

def test_schema_auto_detection_compliance(temp_files):
    # Testing that compliance.json auto-detects oasa-compliance.schema.json
    args = Namespace(files=[str(temp_files["compliance_json"])], schema=None, audit_host=False)
    
    with patch("tools.sovereign_stack.print") as mock_print:
        exit_code = cmd_validate(args)
        assert exit_code == 0
        
        any_schema_check = any("oasa-compliance.schema.json" in str(call) for call in mock_print.mock_calls)
        assert any_schema_check

def test_schema_auto_detection_node_manifest(temp_files):
    # Testing that node-manifest.json auto-detects oasa-node-manifest.schema.json
    args = Namespace(files=[str(temp_files["node_manifest"])], schema=None, audit_host=False)
    
    with patch("tools.sovereign_stack.print") as mock_print:
        exit_code = cmd_validate(args)
        assert exit_code == 0
        
        any_schema_check = any("oasa-node-manifest.schema.json" in str(call) for call in mock_print.mock_calls)
        assert any_schema_check

@patch("platform.system")
@patch("subprocess.run")
def test_windows_tpm_probing_success(mock_run, mock_system):
    mock_system.return_value = "Windows"
    
    # Mock powershell command returning TPM true
    mock_result = MagicMock()
    mock_result.stdout = "IsEnabled_InitialValue: True"
    mock_run.return_value = mock_result

    config = {
        "hardware_security": {
            "tpm_required": True
        }
    }
    
    errors = audit_host_infrastructure(config)
    # Since TPM is detected, there should be no hardware errors
    assert not any("[HARDWARE]" in err for err in errors)

@patch("platform.system")
@patch("subprocess.run")
def test_windows_tpm_probing_failure(mock_run, mock_system):
    mock_system.return_value = "Windows"
    
    # Mock powershell command returning TPM false
    mock_result = MagicMock()
    mock_result.stdout = "IsEnabled_InitialValue: False"
    mock_run.return_value = mock_result

    config = {
        "hardware_security": {
            "tpm_required": True
        }
    }
    
    errors = audit_host_infrastructure(config)
    # TPM is required but reported False, so error should be appended
    assert any("Windows TPM verification failed" in err for err in errors)
