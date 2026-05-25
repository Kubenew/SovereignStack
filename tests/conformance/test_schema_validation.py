"""
Schema Validation Tests — OASA Conformance L1
"""

import yaml
import json
import pytest

def test_sovereign_stack_yaml_exists(stack_config):
    assert stack_config is not None, "sovereign-stack.yaml could not be loaded"

def test_sovereign_stack_yaml_has_version(stack_config):
    assert "version" in stack_config, "Missing 'version' field"
    assert str(stack_config["version"]).startswith("2026"), f"Expected 2026.x, got {stack_config['version']}"

def test_sovereign_stack_yaml_has_metadata(stack_config):
    assert "metadata" in stack_config, "Missing 'metadata' section"
    assert "name" in stack_config["metadata"], "Missing metadata.name"

def test_sovereign_stack_yaml_has_node_infrastructure(stack_config):
    assert "node_infrastructure" in stack_config, "Missing 'node_infrastructure' section"
    infra = stack_config["node_infrastructure"]
    assert "engine" in infra, "Missing node_infrastructure.engine"

def test_sovereign_stack_yaml_air_gapped(stack_config):
    infra = stack_config.get("node_infrastructure", {})
    assert infra.get("air_gapped_enforcement", False), "Air-gap enforcement not enabled"

def test_sovereign_stack_yaml_has_network_isolation(stack_config):
    infra = stack_config.get("node_infrastructure", {})
    net = infra.get("network_isolation", {})
    assert net.get("allow_wan") == False, "WAN access must be disabled for air-gap"

def test_sovereign_stack_yaml_has_data_ingestion(stack_config):
    assert "data_ingestion" in stack_config, "Missing 'data_ingestion' section"

def test_sovereign_stack_yaml_has_cognitive_memory(stack_config):
    assert "cognitive_memory" in stack_config, "Missing 'cognitive_memory' section"

def test_sovereign_stack_yaml_has_compute_execution(stack_config):
    assert "compute_execution" in stack_config, "Missing 'compute_execution' section"

def test_all_json_schemas_valid(schema_store):
    assert len(schema_store) > 0, "No schemas found"
    for name, schema in schema_store.items():
        assert "$schema" in schema, f"Schema '{name}' missing $schema field"
        assert "type" in schema, f"Schema '{name}' missing type field"
        assert schema.get("type") == "object", f"Schema '{name}' root type must be object"

@pytest.mark.level("L2")
def test_l2_encryption_algorithm(stack_config):
    infra = stack_config.get("node_infrastructure", {})
    storage = infra.get("storage", {})
    algo = storage.get("encryption_algorithm", "")
    assert algo == "AES-256-GCM", f"Encryption must be AES-256-GCM, got {algo}"

@pytest.mark.level("L2")
def test_l2_tpm_binding(stack_config):
    infra = stack_config.get("node_infrastructure", {})
    storage = infra.get("storage", {})
    assert storage.get("hardware_tpm_binding") == True, "TPM binding must be enabled for L2"

@pytest.mark.level("L2")
def test_l2_volatile_memory_mode(stack_config):
    ingest = stack_config.get("data_ingestion", {})
    mode = ingest.get("memory_processing_mode", "")
    assert mode == "VOLATILE_RAM_ONLY", f"Ingestion must use VOLATILE_RAM_ONLY, got {mode}"

@pytest.mark.level("L3")
def test_l3_runtime_protection(stack_config):
    compute = stack_config.get("compute_execution", {})
    runtime = compute.get("runtime_protection", {})
    assert runtime.get("enforce_compliance_lock") == True, "Compliance lock must be enforced for L3"
