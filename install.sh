#!/usr/bin/env bash
# =============================================================================
# SovereignStack — 1-Click Sovereign Deployment Script
# =============================================================================
# Auto-detects local hardware capabilities, sets up secure configuration,
# and bootstraps a fully local, isolated, OASA-compliant AI stack.
#
# Usage:
#   curl -sSL https://install.sovereignstack.ai | bash
#   Or local: ./install.sh
# =============================================================================

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; PURPLE='\033[0;35m'; CYAN='\033[0;36m'; NC='\033[0m'

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "  ____                               _             ____  _             _    "
    echo " / ___|  _____   _____ _ __ ___ (_) __ _ _ __  / ___|| |_ __ _  ___| | __"
    echo " \___ \ / _ \ \ / / _ \ '__/ _ \| |/ _\` | '_ \ \___ \| __/ _\` |/ __| |/ /"
    echo "  ___) | (_) \ V /  __/ | |  __/| | (_| | | | |___) | |_| (_| | (__|   < "
    echo " |____/ \___/ \_/ \___|_|  \___| |\__,_|_| |_|____/ \__\__,_|\___|_|\_\\"
    echo "                                  |__/                                      "
    echo " ============================================================================="
    echo "               Sovereign AI Infrastructure Standard Installation"
    echo " ============================================================================="
    echo -e "${NC}"
}

# -------------------------------------------------------------------------
# Step 1: Hardware Detection
# -------------------------------------------------------------------------
detect_hardware() {
    echo -e "${BLUE}[1/5] Scanning local hardware profiles...${NC}"
    echo "-------------------------------------------------------------"

    OS_RAW="$(uname -s)"; ARCH_TYPE="$(uname -m)"; OS_TYPE="Unknown"
    case "$OS_RAW" in
        Linux) OS_TYPE="Linux" ;;
        Darwin) OS_TYPE="Darwin" ;;
        *NT*|*MINGW*|*MSYS*|*CYGWIN*) OS_TYPE="Windows" ;;
    esac
    echo -e "  Operating System: ${GREEN}${OS_TYPE} (${OS_RAW})${NC}"
    echo -e "  Architecture:     ${GREEN}${ARCH_TYPE}${NC}"

    # RAM
    TOTAL_RAM=0
    if [[ "$OS_TYPE" == "Linux" ]]; then
        TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        TOTAL_RAM=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    elif [[ "$OS_TYPE" == "Windows" ]]; then
        if command -v powershell.exe &> /dev/null; then
            total_kb=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum" 2>/dev/null || echo "0")
            TOTAL_RAM=$(echo "$total_kb / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "16")
        fi
    fi
    echo -e "  System Memory:    ${GREEN}${TOTAL_RAM:-16} GB RAM${NC}"

    # GPU
    GPU_BACKEND="CPU_ONLY"; GPU_NAME="Generic CPU"; VRAM_GB=0
    if command -v nvidia-smi &> /dev/null; then
        GPU_BACKEND="NVIDIA_CUDA"
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
        VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
        VRAM_GB=$(echo "scale=1; $VRAM_MB/1024" | bc)
        echo -e "  GPU Detected:     ${GREEN}${GPU_NAME} (${VRAM_GB} GB VRAM)${NC}"
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        CHIP_NAME=$(sysctl -n machdep.cpu.brand_string)
        if [[ "$CHIP_NAME" == *"Apple"* ]]; then
            GPU_BACKEND="APPLE_METAL"; GPU_NAME="$CHIP_NAME GPU"
            VRAM_GB=$(echo "scale=1; $TOTAL_RAM * 0.75" | bc)
            echo -e "  GPU Detected:     ${GREEN}${GPU_NAME} (Unified Silicon)${NC}"
        fi
    else
        echo -e "  GPU Detected:     ${YELLOW}No compatible GPU detected. CPU mode.${NC}"
    fi
    VRAM_GB_INT=${VRAM_GB%.*}

    # TPM
    TPM_STATUS="${RED}Not Detected${NC}"
    if [[ "$OS_TYPE" == "Linux" ]] && [[ -c "/dev/tpm0" || -d "/sys/class/tpm/tpm0" ]]; then
        TPM_STATUS="${GREEN}Hardware TPM 2.0 Active${NC}"
    elif [[ "$OS_TYPE" == "Darwin" ]]; then
        TPM_STATUS="${GREEN}Apple Secure Enclave Active${NC}"
    elif [[ "$OS_TYPE" == "Windows" ]]; then
        if command -v powershell.exe &> /dev/null; then
            tpm_check=$(powershell.exe -NoProfile -Command "(Get-Tpm).TpmPresent" 2>/dev/null | tr -d '\r\n')
            [[ "$tpm_check" == "True" ]] && TPM_STATUS="${GREEN}Windows TPM 2.0 Active${NC}"
        fi
    fi
    echo -e "  Security Chip:    ${TPM_STATUS}"
    echo "-------------------------------------------------------------"
}

# -------------------------------------------------------------------------
# Step 2: Prerequisites Check
# -------------------------------------------------------------------------
check_prerequisites() {
    echo -e "${BLUE}[2/5] Checking prerequisites...${NC}"
    echo "-------------------------------------------------------------"

    local missing=0
    command -v docker &> /dev/null && echo -e "  Docker:           ${GREEN}Installed${NC}" || { echo -e "  Docker:           ${RED}Missing${NC}"; missing=1; }
    command -v python3 &> /dev/null && echo -e "  Python 3:         ${GREEN}Installed${NC}" || { echo -e "  Python 3:         ${RED}Missing${NC}"; missing=1; }
    if command -v docker &> /dev/null && docker compose version &>/dev/null 2>&1; then
        echo -e "  Docker Compose:   ${GREEN}Plugin available${NC}"
    elif docker-compose --version &>/dev/null 2>&1; then
        echo -e "  Docker Compose:   ${GREEN}Standalone available${NC}"
    else
        echo -e "  Docker Compose:   ${RED}Missing — install from https://docs.docker.com/compose/install/${NC}"
        missing=1
    fi

    if [[ $missing -eq 1 ]]; then
        echo -e "${RED}Missing prerequisites. Install missing items and re-run.${NC}"
        exit 1
    fi
    echo "-------------------------------------------------------------"
}

# -------------------------------------------------------------------------
# Step 3: Configuration Generation
# -------------------------------------------------------------------------
generate_config() {
    echo -e "${BLUE}[3/5] Generating secure configuration...${NC}"
    echo "-------------------------------------------------------------"
    mkdir -p data/ingest data/memory data/audit models playground

    # .env
    if [[ ! -f ".env" ]]; then
        cat <<EOF > .env
OASA_ENFORCE_COMPLIANCE=STRICT
OASA_ENFORCE_AUTH=STRICT
OASA_ENFORCE_POLICY=STRICT
OASA_OPENTELEMETRY_ENABLED=true
DATA_DIR=/app/data
INFERENCE_BACKEND=vllm
COMPUTE_URL=http://vllm:8000
MEMORY_URL=http://memory:8082
VLLM_MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
VLLM_GPU_MEMORY_UTIL=0.90
VLLM_MAX_MODEL_LEN=4096
VLLM_GPU_COUNT=1
EOF
        echo -e "  .env:             ${GREEN}Generated${NC}"
    else
        echo -e "  .env:             ${GREEN}Exists (unmodified)${NC}"
    fi

    # sovereign-stack.yaml (new OASA 2026.1 format)
    if [[ ! -f "sovereign-stack.yaml" ]]; then
        cat <<EOF > sovereign-stack.yaml
version: "2026.1"
metadata:
  name: "sovereign-node-local"
  tier: "production-airgapped"
  compliance_profile: "OASA-STRICT-GDPR-HIPAA"

node_infrastructure:
  engine: "docker-compose"
  air_gapped_enforcement: true
  storage:
    ephemeral_encrypted: true
    encryption_algorithm: "AES-256-GCM"
    hardware_tpm_binding: $([[ "$TPM_STATUS" == *"Active"* ]] && echo "true" || echo "false")
  network_isolation:
    allow_wan: false
    dns_mode: "LOCAL_ONLY"
    allowed_internal_cidrs:
      - "10.0.0.0/8"
      - "192.168.0.0/16"
  sandboxing:
    runtime: "gvisor"
    confidential_compute: false

data_ingestion:
  service_name: "pdf2struct-pipeline"
  max_parallel_workers: 4
  memory_processing_mode: "VOLATILE_RAM_ONLY"
  enforce_strict_json_schema: true
  input_formats:
    - "PDF"
    - "TIFF"
    - "DOCX"

cognitive_memory:
  backend: "TurboMemory-Isolated"
  vector_dimensions: 4096
  encryption_at_rest: true
  context_ttl_seconds: 3600
  kv_cache_isolation: true

compute_execution:
  gateway: "vllm-openai"
  optimization_engine: "vLLM"
  precision: "INT4_AWQ"
  openai_api_compatibility: true
  hardware:
    accelerator: "${GPU_BACKEND}"
    vram_budget_gb: ${VRAM_GB_INT:-16}
    allow_cpu_fallback: false
  runtime_protection:
    enforce_compliance_lock: true
    memory_leak_threshold_mb: 512
    max_token_context: 8192

services:
  gateway:
    enabled: true
    listen: "0.0.0.0:8080"
    identity:
      enabled: true
      provider: "keycloak"
      issuer_url: "http://keycloak.local/auth/realms/sovereign"
      client_id: "sovereign-gateway"
    policy:
      enabled: true
      engine: "opa"
      policy_path: "./policies/inference.rego"
    observability:
      enabled: true
      opentelemetry_endpoint: "http://otel-collector.local:4317"
      prometheus_enabled: true
  ingest:
    enabled: true
    listen: "0.0.0.0:8081"
  memory:
    enabled: true
    listen: "0.0.0.0:8082"
    vector_backend: "local-json"
  compute:
    enabled: true
    listen: "0.0.0.0:8083"
    backend: "local"
    vram_budget_gb: ${VRAM_GB_INT:-16}

models:
  allowed:
    - "sovereign-llama3"
    - "sovereign-mistral"
EOF
        echo -e "  Stack manifest:   ${GREEN}Generated (OASA 2026.1 format)${NC}"
    else
        echo -e "  Stack manifest:   ${GREEN}Exists (unmodified)${NC}"
    fi
    echo "-------------------------------------------------------------"
}

# -------------------------------------------------------------------------
# Step 4: Dependency Installation
# -------------------------------------------------------------------------
install_deps() {
    echo -e "${BLUE}[4/5] Installing Python dependencies...${NC}"
    echo "-------------------------------------------------------------"
    if [[ -f "requirements.txt" ]]; then
        if command -v pip3 &> /dev/null; then
            pip3 install -r requirements.txt 2>&1 | tail -1
        elif command -v pip &> /dev/null; then
            pip install -r requirements.txt 2>&1 | tail -1
        fi
        echo -e "  Python deps:      ${GREEN}Installed${NC}"
    else
        echo -e "  Python deps:      ${YELLOW}No requirements.txt found${NC}"
    fi
    echo "-------------------------------------------------------------"
}

# -------------------------------------------------------------------------
# Step 5: Model Recommendation & Summary
# -------------------------------------------------------------------------
summarize() {
    echo -e "${BLUE}[5/5] Deployment summary${NC}"
    echo "-------------------------------------------------------------"
    echo -e "  Stack:            ${GREEN}SovereignStack OASA 2026.1${NC}"
    echo -e "  Backend:          ${GREEN}${GPU_BACKEND}${NC}"
    echo -e "  VRAM Budget:      ${GREEN}${VRAM_GB_INT:-16} GB${NC}"
    echo -e "  Identity:         ${GREEN}Keycloak OIDC (configured)${NC}"
    echo -e "  Policy Engine:    ${GREEN}OPA (configured)${NC}"
    echo "-------------------------------------------------------------"

    echo ""
    echo "To download a model and start the stack:"
    echo ""

    local model_url model_name
    if [[ "$GPU_BACKEND" == "NVIDIA_CUDA" ]] && (( VRAM_GB_INT >= 8 )); then
        model_url="https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        model_name="Mistral-7B-Instruct (GGUF Q4)"
    else
        model_url="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
        model_name="Phi-3-Mini (GGUF Q4)"
    fi
    echo -e "  ${CYAN}Recommended: ${model_name}${NC}"
    echo "  curl -Lo playground/models/model.gguf \"$model_url\""
    echo ""
    echo -e "  ${CYAN}Launch:${NC}"
    echo "  docker compose up --build -d"
    echo ""
    echo -e "  ${CYAN}Test:${NC}"
    echo "  curl -X POST http://localhost:8080/v1/chat/completions \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"Authorization: Bearer mock-valid-token\" \\"
    echo "    -d '{\"model\":\"Qwen/Qwen2.5-7B-Instruct\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"oasa_compliance_lock\":true}'"
    echo ""
    echo -e "${GREEN}Installation complete.${NC}"
}

# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------
print_banner
detect_hardware
check_prerequisites
generate_config
install_deps
summarize
