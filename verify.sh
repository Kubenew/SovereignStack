#!/bin/bash
set -e

echo "====================================================="
echo " SovereignStack v0.5 Clean-Room Verification Gate "
echo "====================================================="

# 1. Build Verification
echo "[1/6] Building SovereignStack..."
cargo build --release
echo "✅ Build PASS"

# 2. Rust Core Tests
echo "[2/6] Running Rust Core Tests..."
cargo test --workspace --quiet
echo "✅ Rust Core Tests PASS"

# 3. Python Core Setup
echo "[3/6] Setting up Python dependencies..."
pip install -q pytest pytest-asyncio requests pyyaml
echo "✅ Dependencies PASS"

# 4. Start Reference Node in background
echo "[4/6] Starting Reference Node..."
./target/release/ss-node --port 8547 > node.log 2>&1 &
NODE_PID=$!
sleep 2

# Check if node is running
if ! curl -s http://localhost:8547/sip/v1/ping > /dev/null; then
  echo "❌ Failed to start reference node."
  cat node.log
  kill $NODE_PID
  exit 1
fi
echo "✅ Reference Node PASS"

# 5. Execute Conformance Harness & Security Attacks (pytest)
echo "[5/6] Executing Conformance Harness & Security Tests..."
pytest tests/ -v --tb=short || {
  echo "❌ Security/Conformance Tests Failed"
  kill $NODE_PID
  exit 1
}
echo "✅ Security & Conformance PASS"

# 6. Execute Claims Validator (Proves tests ran and mapped to claims)
echo "[6/6] Verifying Claims Matrix..."
python tools/validate_claims.py || {
  echo "❌ Claims Validation Failed"
  kill $NODE_PID
  exit 1
}
echo "✅ Claims Validation PASS"

# Cleanup
kill $NODE_PID

echo "====================================================="
echo " STATUS: CORE CONTRACT VERIFIED "
echo "====================================================="
exit 0
