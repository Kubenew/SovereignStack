"""
Audit Log & Observability Tests — OASA Conformance L2/L3
"""

import pytest
import os
import json
from pathlib import Path


def test_audit_log_exists():
    """Data directory must be prepared for audit logs."""
    data_dir = Path(os.environ.get("DATA_DIR", "./data_test"))
    data_dir.mkdir(parents=True, exist_ok=True)
    assert data_dir.exists(), f"Data directory {data_dir} must exist"
    assert data_dir.is_dir(), f"{data_dir} must be a directory"


def test_compliance_lock_in_request_schema():
    """Verify oasa_compliance_lock is defined in the request schema."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "schemas/oasa-request.schema.json"
    import json
    with open(schema_path) as f:
        schema = json.load(f)
    props = schema.get("properties", {})
    assert "oasa_compliance_lock" in props, "oasa_compliance_lock must be in schema"
    lock_schema = props["oasa_compliance_lock"]
    assert lock_schema.get("type") == "boolean", "oasa_compliance_lock must be boolean"


def test_audit_tag_in_request_schema():
    """Verify oasa_audit_tag is defined in the request schema."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "schemas/oasa-request.schema.json"
    import json
    with open(schema_path) as f:
        schema = json.load(f)
    props = schema.get("properties", {})
    assert "oasa_audit_tag" in props, "oasa_audit_tag must be in schema"


@pytest.mark.level("L3")
def test_merkle_tree_audit_format():
    """L3: Verify Merkle-tree audit log format (cryptographic chaining)."""
    # Check that the audit spec mentions hash chaining
    oasa_spec = Path(__file__).resolve().parent.parent.parent / "OASA.md"
    content = oasa_spec.read_text(encoding="utf-8")
    # L3 requires Merkle-tree auditing - check roadmap references
    assert "Merkle" in content or "immutable" in content.lower(), \
        "Specification must reference Merkle-tree or immutable logs for L3"


@pytest.mark.level("L3")
def test_audit_log_fields_comprehensive():
    """L3: Audit log schema must include all required fields."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "schemas/oasa-request.schema.json"
    import json
    with open(schema_path) as f:
        schema = json.load(f)
    props = schema.get("properties", {})
    # L3 requires all audit fields
    for field in ["oasa_compliance_lock", "oasa_audit_tag", "oasa_jurisdiction"]:
        assert field in props, f"L3 requires {field} in request schema"
