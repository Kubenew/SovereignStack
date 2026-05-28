import json
import os
import subprocess
import sys
from pathlib import Path

def test_certification_flow(tmp_path):
    """End-to-end test of the certification issuance and verification CLI tools."""
    report_path = tmp_path / "report.json"
    attestation_path = tmp_path / "attestation.json"
    
    # 1. Create a mock passing report
    mock_report = {
        "oasa_version": "2026.1",
        "level": "L2",
        "report_version": "1.0",
        "summary": {
            "total": 10,
            "passed": 10,
            "failed": 0,
            "skipped": 0
        },
        "results": []
    }
    report_path.write_text(json.dumps(mock_report))
    
    # 2. Issue certification
    issue_cmd = [
        sys.executable, "tools/issue_certification.py",
        "--report", str(report_path),
        "--level", "L2",
        "--subject-name", "Test Node",
        "--subject-type", "node",
        "--output", str(attestation_path)
    ]
    
    result = subprocess.run(issue_cmd, capture_output=True, text=True, cwd="C:/Users/Orcl/.gemini/antigravity-ide/scratch/SovereignStack")
    assert result.returncode == 0, f"Issuance failed: {result.stderr}"
    assert attestation_path.exists()
    
    # Check contents
    attestation = json.loads(attestation_path.read_text())
    assert attestation["certification"]["level"] == "L2"
    assert attestation["subject"]["name"] == "Test Node"
    assert "signature" in attestation
    
    # 3. Verify certification
    verify_cmd = [
        sys.executable, "tools/verify_certification.py",
        "--attestation", str(attestation_path)
    ]
    result = subprocess.run(verify_cmd, capture_output=True, text=True, cwd="C:/Users/Orcl/.gemini/antigravity-ide/scratch/SovereignStack")
    assert result.returncode == 0, f"Verification failed: {result.stderr}"
    assert "VERIFIED" in result.stdout
    
    # 4. Tamper with the attestation
    attestation["certification"]["level"] = "L3" # Fake an upgrade
    attestation_path.write_text(json.dumps(attestation))
    
    # 5. Verify tampered certification (should fail)
    result = subprocess.run(verify_cmd, capture_output=True, text=True, cwd="C:/Users/Orcl/.gemini/antigravity-ide/scratch/SovereignStack")
    assert result.returncode == 1
    assert "FAILED" in result.stdout

def test_certification_rejection(tmp_path):
    """Ensure the issuer refuses to sign a failing report."""
    report_path = tmp_path / "failing_report.json"
    attestation_path = tmp_path / "failing_attestation.json"
    
    mock_report = {
        "summary": {
            "total": 10,
            "passed": 9,
            "failed": 1, # Fails!
            "skipped": 0
        }
    }
    report_path.write_text(json.dumps(mock_report))
    
    issue_cmd = [
        sys.executable, "tools/issue_certification.py",
        "--report", str(report_path),
        "--level", "L2",
        "--subject-name", "Test Node",
        "--subject-type", "node",
        "--output", str(attestation_path)
    ]
    
    result = subprocess.run(issue_cmd, capture_output=True, text=True, cwd="C:/Users/Orcl/.gemini/antigravity-ide/scratch/SovereignStack")
    assert result.returncode == 1
    assert "Cannot issue certification for a report with 1 failing tests" in result.stdout
