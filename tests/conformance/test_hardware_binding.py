"""
Hardware Security & TPM Binding Tests — OASA Conformance L2/L3
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_tpm_detection_linux():
    """TPM must be detectable on Linux via /dev/tpm0."""
    tpm_path = Path("/dev/tpm0")
    # In CI, this will likely not exist — test the logic, not the hardware
    from tools.sovereign_stack import _detect_tpm
    with patch("platform.system", return_value="Linux"):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value="2.0\n"):
                result = _detect_tpm()
                assert result["present"] == True
                assert result["version"] == "2.0"


def test_tpm_detection_windows():
    """TPM must be detectable on Windows via PowerShell."""
    from tools.sovereign_stack import _detect_tpm
    with patch("platform.system", return_value="Windows"):
        mock_result = MagicMock()
        mock_result.stdout = "IsEnabled_InitialValue: True\nSpecVersion: 2.0\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _detect_tpm()
            assert result["present"] == True, "TPM should be detected as present"


def test_tpm_not_detected():
    """When TPM is absent, detection must return present=False."""
    from tools.sovereign_stack import _detect_tpm
    with patch("platform.system", return_value="Linux"):
        with patch("pathlib.Path.exists", return_value=False):
            result = _detect_tpm()
            assert result["present"] == False, "TPM should not be detected"


def test_cpu_fallback_config():
    """Config must specify allow_cpu_fallback."""
    import yaml
    config_path = Path(__file__).resolve().parent.parent.parent / "sovereign-stack.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    compute = config.get("compute_execution", {})
    hw = compute.get("hardware", {})
    assert "allow_cpu_fallback" in hw, "Missing allow_cpu_fallback in compute_execution.hardware"


@pytest.mark.level("L2")
@patch("platform.system")
@patch("subprocess.run")
def test_windows_tpm_audit(mock_run, mock_system):
    """L2: Verify TPM audit on Windows works correctly."""
    mock_system.return_value = "Windows"
    mock_result = MagicMock()
    mock_result.stdout = "IsEnabled_InitialValue: True"
    mock_run.return_value = mock_result

    from tools.sovereign_stack import audit_host_infrastructure

    config = {"node": {"tpm_required": True}}
    errors = audit_host_infrastructure(config)
    hw_errors = [e for e in errors if "[HARDWARE]" in e]
    assert len(hw_errors) == 0, f"Unexpected hardware errors: {hw_errors}"
