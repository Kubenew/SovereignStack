"""
OASA Conformance Test Suite — Shared Configuration and Fixtures
"""

import os
import sys
import json
import yaml
import pytest
from pathlib import Path


def pytest_configure(config):
    """Register custom markers for conformance levels."""
    config.addinivalue_line("markers", "level(level_name): mark test for a specific conformance level (L1, L2, L3)")


def pytest_addoption(parser):
    parser.addoption(
        "--level",
        action="store",
        default="L1",
        choices=["L1", "L2", "L3"],
        help="OASA conformance level to test",
    )
    parser.addoption(
        "--config",
        action="store",
        default="sovereign-stack.yaml",
        help="Path to sovereign-stack.yaml config file",
    )


@pytest.fixture
def config_path(request):
    return Path(request.config.getoption("--config"))


@pytest.fixture
def conformance_level(request):
    return request.config.getoption("--level")


@pytest.fixture
def stack_config(config_path):
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def schema_store():
    """Load all OASA JSON schemas for testing."""
    schemas_dir = Path(__file__).resolve().parent.parent.parent / "schemas"
    schemas = {}
    for f in schemas_dir.glob("*.json"):
        schemas[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    for f in (schemas_dir / "certification").glob("*.json"):
        schemas[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return schemas
