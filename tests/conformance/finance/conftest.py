"""Pytest config for Finance Reference Node conformance tests."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--report-dir",
        action="store",
        default="reports",
        help="Directory for conformance reports",
    )


@pytest.fixture(scope="session")
def report_dir(request) -> Path:
    return Path(request.config.getoption("--report-dir"))


@pytest.fixture(scope="session")
def save_report(report_dir):
    """Factory fixture: save_report(report_name, data) writes JSON report."""
    report_dir.mkdir(parents=True, exist_ok=True)

    def _save(name: str, data: dict) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = report_dir / f"{name}-{ts}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return path

    return _save
