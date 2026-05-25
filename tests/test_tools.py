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
        "version": "2026.1",
        "metadata": {
            "name": "test-node",
            "tier": "production-airgapped",
            "compliance_profile": "OASA-STRICT-GDPR-HIPAA"
        },
        "node_infrastructure": {
            "engine": "privatecloud-k8s",
            "air_gapped_enforcement": True,
            "storage": {
                "ephemeral_encrypted": True,
                "encryption_algorithm": "AES-256-GCM",
                "hardware_tpm_binding": False
            },
            "network_isolation": {
                "allow_wan": False,
                "dns_mode": "LOCAL_ONLY",
                "allowed_internal_cidrs": ["10.0.0.0/8"]
            }
        },
        "data_ingestion": {
            "service_name": "pdf2struct-pipeline",
            "max_parallel_workers": 4,
            "memory_processing_mode": "VOLATILE_RAM_ONLY",
            "input_formats": ["PDF", "DOCX"]
        },
        "cognitive_memory": {
            "backend": "local-json",
            "vector_dimensions": 4096,
            "encryption_at_rest": True,
            "context_ttl_seconds": 3600
        },
        "compute_execution": {
            "gateway": "vllm-openai",
            "optimization_engine": "vLLM",
            "precision": "INT4",
            "hardware": {
                "accelerator": "NVIDIA_CUDA",
                "vram_budget_gb": 24,
                "allow_cpu_fallback": False
            },
            "runtime_protection": {
                "enforce_compliance_lock": True,
                "memory_leak_threshold_mb": 512,
                "max_token_context": 8192
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
