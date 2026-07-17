#!/usr/bin/env bash
# ==============================================================================
# SovereignStack - Cognition-Native Infrastructure Deployment & Hardening Engine
# Script: deploy-hardened-mesh.sh
# Purpose: Auto-provisions the entire AGI/ASI-ready P2P orchestration architecture.
# ==============================================================================

set -euo pipefail

# Visual ANSI Formatting Colors
export GREEN='\033[0;32m'
export RED='\033[0;31m'
export BLUE='\033[0;34m'
export YELLOW='\033[1;33m'
export NC='\033[0;3m' # No Color

log_info() { echo -e "${BLUE}[INFO] $(date +'%H:%M:%S')${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS] $(date +'%H:%M:%S')${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN] $(date +'%H:%M:%S')${NC} $1"; }
log_error() { echo -e "${RED}[ERROR] $(date +'%H:%M:%S')${NC} $1"; exit 1; }

echo -e "${BLUE}"
echo "======================================================================"
echo "      SOVEREIGNSTACK COGNITION-NATIVE FABRIC LIVE TEST INSTALLER       "
echo "======================================================================"
echo -e "${NC}"

# ==============================================================================
# STEP 1: Pre-Flight Dependency and Environment Checks
# ==============================================================================
log_info "Executing local host architectural validation checks..."

command -v cargo >/dev/null 2>&1 || log_error "Rust/Cargo toolchain is missing. Please install via rustup."
command -v python3 >/dev/null 2>&1 || log_error "Python3 runtime environment is missing."
command -v docker >/dev/null 2>&1 || log_error "Docker Engine daemon is missing or not running."
command -v kubectl >/dev/null 2>&1 || log_warn "kubectl CLI missing. Skipping local Kubernetes cluster tasks."
command -v helm >/dev/null 2>&1 || log_warn "Helm package orchestrator missing. Skipping cluster deployments."

log_success "Host environmental validation complete."

# ==============================================================================
# STEP 2: Compile Rust Workspace with Release Optimizations
# ==============================================================================
log_info "Compiling the SovereignStack kernel space workspace binaries..."

# Explicitly enforce Protocol Buffer compilation via tonic-build hooks
export PROTOC_NO_VENDOR=1

if cargo build --workspace --release; then
    log_success "Rust workspace successfully compiled into optimized release artifacts."
else
    log_error "Rust compilation failed. Check code formatting, lints, or missing dependencies."
fi

# Run the local unit and mathematical verification test suites
log_info "Executing core unit testing matrix (ZK verifiers, URI parsers, and Leases)..."
cargo test --workspace

# ==============================================================================
# STEP 3: Setup Python Telemetry & Microservices Layer
# ==============================================================================
log_info "Initializing Python runtime dependencies & executing degradation tests..."

python3 -m venv .venv
# Ensure virtual environment can execute cleanly matching execution context profiles
source .venv/bin/activate || . .venv/bin/activate

python3 -m pip install --upgrade pip --quiet
python3 -m pip install regex grpcio grpcio-tools --quiet

# Run the Python multi-agent MCTS branching and network degradation tests
if python3 scripts/test_mesh_degradation.py && python3 scripts/test_cognitive_leases.py; then
    log_success "Python verification loops passed successfully."
else
    log_error "Simulation error detected inside the Python microservices testing suite."
fi

# ==============================================================================
# STEP 4: Build Isolation Container Assets
# ==============================================================================
log_info "Building the secure, multi-stage non-root deployment Docker container..."

docker build -t kubenew/sovereignstack-kernel:v0.3.0 .
log_success "Docker compilation complete: image tagged as kubenew/sovereignstack-kernel:v0.3.0"

# ==============================================================================
# STEP 5: Kubernetes Cluster Orchestration & Deployment
# ==============================================================================
if command -v kubectl >/dev/null 2>&1 && command -v helm >/dev/null 2>&1; then
    log_info "Deploying Cognitive Infrastructure Mesh to the local cluster space..."

    # Secure the execution target namespace
    kubectl create namespace sovereignstack --dry-run=client -o yaml | kubectl apply -f -

    # Initialize deployment package parameters using your custom Helm configuration rules
    helm upgrade --install sovereignstack ./charts/sovereignstack \
        --namespace sovereignstack \
        --set nodeConfig.trustLevel="L3-Strict-Sovereign" \
        --set gateway.strictComplianceLocking=true

    log_success "SovereignStack has been securely deployed onto your live Kubernetes infrastructure!"
    log_info "To view live agent session allocations, execute: kubectl get pods -n sovereignstack"
else
    log_warn "Kubernetes or Helm tools were missing; container built locally but cluster deployment steps were skipped."
fi

echo -e "${GREEN}"
echo "======================================================================"
echo " 🎉 COGNITION-NATIVE ENVIRONMENT PROVISIONING COMPLETE SUCCESSFULLY   "
echo "======================================================================"
echo -e "${NC}"
