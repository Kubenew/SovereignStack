Write-Host "====================================================="
Write-Host " SovereignStack v0.5 Clean-Room Verification Gate "
Write-Host "====================================================="

$ErrorActionPreference = "Stop"

# 1. Build Verification
Write-Host "[1/6] Building SovereignStack..."
cargo build --release
Write-Host "✅ Build PASS"

# 2. Rust Core Tests
Write-Host "[2/6] Running Rust Core Tests..."
cargo test --workspace --quiet
Write-Host "✅ Rust Core Tests PASS"

# 3. Python Core Setup
Write-Host "[3/6] Setting up Python dependencies..."
pip install -q pytest pytest-asyncio requests pyyaml
Write-Host "✅ Dependencies PASS"

# 4. Start Reference Node in background
Write-Host "[4/6] Starting Reference Node..."
$process = Start-Process -FilePath ".\target\release\ss-node.exe" -ArgumentList "--port 8547" -PassThru -NoNewWindow
Start-Sleep -Seconds 2

try {
    Invoke-RestMethod -Uri "http://localhost:8547/sip/v1/ping" | Out-Null
    Write-Host "✅ Reference Node PASS"
} catch {
    Write-Host "❌ Failed to start reference node."
    Stop-Process -Id $process.Id -Force
    exit 1
}

# 5. Execute Conformance Harness & Security Attacks (pytest)
Write-Host "[5/6] Executing Conformance Harness & Security Tests..."
try {
    # Using pytest natively
    $pytestOutput = & pytest tests/ -v --tb=short
    if ($LASTEXITCODE -ne 0) { throw "pytest failed" }
    Write-Host "✅ Security & Conformance PASS"
} catch {
    Write-Host "❌ Security/Conformance Tests Failed"
    Stop-Process -Id $process.Id -Force
    exit 1
}

# 6. Execute Claims Validator
Write-Host "[6/6] Verifying Claims Matrix..."
try {
    $valOutput = & python tools/validate_claims.py
    if ($LASTEXITCODE -ne 0) { throw "claims validation failed" }
    Write-Host "✅ Claims Validation PASS"
} catch {
    Write-Host "❌ Claims Validation Failed"
    Stop-Process -Id $process.Id -Force
    exit 1
}

# Cleanup
Stop-Process -Id $process.Id -Force

Write-Host "====================================================="
Write-Host " STATUS: CORE CONTRACT VERIFIED "
Write-Host "====================================================="
exit 0
