#!/bin/bash
set -e

echo "====================================================="
echo " SovereignStack v0.5 Clean-Room Verification Gate "
echo "====================================================="

# 1. Build Verification
echo "[1/7] Building SovereignStack..."
cargo build --release
echo "✅ Build PASS"

# 2. Rust Core Tests
echo "[2/7] Running Rust Core Tests..."
cargo test --workspace --quiet
echo "✅ Rust Core Tests PASS"

# 3. Python Core Setup
echo "[3/7] Setting up Python dependencies..."
pip install -q pytest pytest-asyncio requests pyyaml cryptography
echo "✅ Dependencies PASS"

# 4. Start Reference Node in background
echo "[4/7] Starting Reference Node..."
./target/release/ss-node --port 8546 > node.log 2>&1 &
NODE_PID=$!
sleep 2

# Check if node is running
if ! curl -s http://localhost:8546/sip/v1/ping > /dev/null; then
  echo "❌ Failed to start reference node."
  cat node.log
  kill $NODE_PID
  exit 1
fi
echo "✅ Reference Node PASS"

# 5. Core Contract Conformance Harness (7 deterministic vectors)
echo "[5/7] Executing Core Contract Conformance Harness (profile core-0.1)..."
python tools/ss-conformance.py --endpoint http://localhost:8546 --profile core-0.1 || {
  echo "❌ Core Contract Conformance Failed"
  kill $NODE_PID
  exit 1
}
echo "✅ Core Contract Vectors PASS"

# 6. Execute Security & Conformance Tests (incl. Morpheus integration)
echo "[6/7] Executing Security, Conformance & Integration Tests..."
pytest tests/ integrations/morpheus/tests -v --tb=short || {
  echo "❌ Security/Conformance/Integration Tests Failed"
  kill $NODE_PID
  exit 1
}
echo "✅ Security, Conformance & Integration PASS"

# 7. Execute Claims Validator (Proves tests ran and mapped to claims)
echo "[7/7] Verifying Claims Matrix..."
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
