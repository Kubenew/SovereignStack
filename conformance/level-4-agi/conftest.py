"""
Pytest configuration for Level 4 conformance tests.

Registers the --sovereign-node CLI option and provides the sovereign_node fixture.
"""

import httpx
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--sovereign-node",
        action="store",
        default="http://localhost:8080",
        help="URL of the SovereignStack node to test against",
    )
    parser.addoption(
        "--audit-log",
        action="store",
        default="/var/log/sovereignstack/audit.log",
        help="Path to the SovereignStack audit log",
    )


@pytest.fixture(scope="session")
def sovereign_node_url(request):
    return request.config.getoption("--sovereign-node")


@pytest.fixture(scope="session")
def audit_log_path(request):
    return request.config.getoption("--audit-log")


class SovereignNodeClient:
    """HTTP client wrapper for talking to a SovereignStack node."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str, **kwargs) -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as client:
            return client.get(f"{self.base_url}{path}", **kwargs)

    def post(self, path: str, json: dict | None = None, **kwargs) -> httpx.Response:
        with httpx.Client(timeout=self.timeout) as client:
            return client.post(f"{self.base_url}{path}", json=json, **kwargs)


@pytest.fixture(scope="session")
def sovereign_node(sovereign_node_url):
    """Provide a SovereignNodeClient connected to the target node."""
    return SovereignNodeClient(sovereign_node_url)
