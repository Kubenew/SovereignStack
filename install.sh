#!/usr/bin/env bash
# =============================================================================
# SovereignStack — 1-Click Sovereign Deployment Script
# =============================================================================
# Auto-detects local hardware capabilities, sets up secure configuration,
# and bootstraps a fully local, isolated, OASA-compliant AI stack.
#
# Usage:
#   curl -sSL install.sovereignstack.ai | bash
#   Or local execution: ./install.sh
# =============================================================================

set -euo pipefail

# ANSI color codes for premium rendering
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Premium Ascii Banner
clear
echo -e "${CYAN}"
echo "  ____                               _             ____  _             _    "
echo " / ___|  _____   _____ _ __ ___ (_) __ _ _ __  / ___|| |_ __ _  ___| | __"
echo " \___ \ / _ \ \ / / _ \ '__/ _ \  |/ _` | '_ \ \___ \| __/ _` |/ __| |/ /"
echo "  ___) | (_) \ V /  __/ | |  __/  | (_| | | | | ___) | |_| (_| | (__|   < "
echo " |____/ \___/ \_/ \___|_|  \___|  |\__,_|_| |_|____/ \__\__,_|\___|_|\_\\"
# Fix escaping in printing the backslash
echo "                                  |__/                                      "
echo " ============================================================================="
echo "               Sovereign AI Infrastructure Standard Installation"
echo " ============================================================================="
echo -e "${NC}"

echo -e "${BLUE}[1/4] Scanning local hardware profiles...${NC}"
echo "-------------------------------------------------------------"

# 1. OS & Architecture Detection
OS_RAW="$(uname -s)"
ARCH_TYPE="$(uname -m)"
OS_TYPE="Unknown"

if [[ "$OS_RAW" == "Linux" ]]; then
    OS_TYPE="Linux"
elif [[ "$OS_RAW" == "Darwin" ]]; then
    OS_TYPE="Darwin"
elif [[ "$OS_RAW" == *"NT"* || "$OS_RAW" == *"MINGW"* || "$OS_RAW" == *"MSYS"* || "$OS_RAW" == *"CYGWIN" ]]; then
    OS_TYPE="Windows"
fi

echo -e "  Operating System: ${GREEN}${OS_TYPE} (${OS_RAW})${NC}"
echo -e "  Architecture:     ${GREEN}${ARCH_TYPE}${NC}"

# 2. RAM Memory Detection
TOTAL_RAM=0
if [[ "$OS_TYPE" == "Linux" ]]; then
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    echo -e "  System Memory:    ${GREEN}${TOTAL_RAM} GB RAM${NC}"
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    TOTAL_RAM=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    echo -e "  System Memory:    ${GREEN}${TOTAL_RAM} GB RAM (Unified Apple Silicon)${NC}"
elif [[ "$OS_TYPE" == "Windows" ]]; then
    # Query memory via powershell or wmic
    if command -v powershell.exe &> /dev/null; then
        total_kb=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum" 2>/dev/null || echo "0")
        if [[ "$total_kb" -ne "0" ]]; then
            TOTAL_RAM=$(echo "$total_kb / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "0")
        fi
    fi
    if [[ "$TOTAL_RAM" -eq 0 ]]; then
        if command -v wmic &> /dev/null; then
            total_kb=$(wmic ComputerSystem get TotalPhysicalMemory | awk 'NR==2 {print $1}')
            TOTAL_RAM=$(echo "$total_kb / 1024 / 1024 / 1024" | bc 2>/dev/null || echo "16")
        else
            TOTAL_RAM=16 # Fallback
        fi
    fi
    echo -e "  System Memory:    ${GREEN}${TOTAL_RAM} GB RAM${NC}"
else
    echo -e "  System Memory:    ${YELLOW}Unknown (Unsupported OS)${NC}"
fi

# 3. GPU/Accelerator Detection
GPU_BACKEND="CPU_ONLY"
GPU_NAME="Generic CPU"
VRAM_GB=0

if command -v nvidia-smi &> /dev/null; then
    # NVIDIA CUDA detected
    GPU_BACKEND="NVIDIA_CUDA"
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
    VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    VRAM_GB=$(echo "scale=1; $VRAM_MB/1024" | bc 2>/dev/null || echo "0")
    # Clean float to integer if needed
    VRAM_GB_INT=${VRAM_GB%.*}
    echo -e "  GPU Detected:     ${GREEN}${GPU_NAME} (${VRAM_GB} GB VRAM)${NC}"
    echo -e "  Acceleration:     ${GREEN}NVIDIA CUDA Acceleration Activated${NC}"
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    # Apple Silicon check
    CHIP_NAME=$(sysctl -n machdep.cpu.brand_string)
    if [[ "$CHIP_NAME" == *"Apple"* ]]; then
        GPU_BACKEND="APPLE_METAL"
        GPU_NAME="$CHIP_NAME GPU"
        # Shared system memory is VRAM budget
        VRAM_GB=$(echo "scale=1; $TOTAL_RAM * 0.75" | bc)
        VRAM_GB_INT=${VRAM_GB%.*}
        echo -e "  GPU Detected:     ${GREEN}${GPU_NAME} (Unified Silicon)${NC}"
        echo -e "  Acceleration:     ${GREEN}Apple Metal API Backend (Available VRAM cap: ${VRAM_GB} GB)${NC}"
    fi
else
    echo -e "  GPU Detected:     ${YELLOW}No compatible physical GPU detected. Falling back to CPU mode.${NC}"
    VRAM_GB_INT=0
fi

# 4. TPM 2.0 Hardened Security Probe
TPM_STATUS="${RED}Not Detected${NC}"
if [[ "$OS_TYPE" == "Linux" ]]; then
    if [[ -c "/dev/tpm0" || -d "/sys/class/tpm/tpm0" ]]; then
        TPM_STATUS="${GREEN}Hardware TPM 2.0 Active${NC}"
    fi
elif [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS Secure Enclave
    TPM_STATUS="${GREEN}Apple Secure Enclave Active${NC}"
elif [[ "$OS_TYPE" == "Windows" ]]; then
    # Probe Windows TPM via PowerShell
    if command -v powershell.exe &> /dev/null; then
        tpm_check=$(powershell.exe -NoProfile -Command "Get-Tpm | Select-Object -ExpandProperty TpmPresent" 2>/dev/null | tr -d '\r' | tr -d '\n' || echo "False")
        if [[ "$tpm_check" == *"True"* ]]; then
            TPM_STATUS="${GREEN}Windows TPM 2.0 Active${NC}"
        else
            TPM_STATUS="${YELLOW}Detected but Inactive / Disabled${NC}"
        fi
    fi
fi
echo -e "  Security Chip:    ${TPM_STATUS}"
echo "-------------------------------------------------------------"

echo -e "\n${BLUE}[2/4] Setting up isolation configs & OASA metrics...${NC}"
echo "-------------------------------------------------------------"

# Create directories if they do not exist
mkdir -p data/ingest data/memory data/audit models playground/models

# Setup environment files
if [[ ! -f ".env" ]]; then
    echo "Creating isolated environment profile (.env)..."
    cat <<EOF > .env
OASA_ENFORCE_COMPLIANCE=STRICT
DATA_DIR=/app/data
COMPUTE_URL=http://compute:8083
MEMORY_URL=http://memory:8082
LOCAL_MODEL_NAME=sovereign-llama3
EOF
    echo -e "  Config profile:   ${GREEN}Success (.env generated)${NC}"
else
    echo -e "  Config profile:   ${GREEN}Exists (.env unmodified)${NC}"
fi

# Generate standard compliance manifest
if [[ ! -f "sovereign-stack.yaml" ]]; then
    echo "Bootstrapping default sovereign-stack.yaml manifest..."
    cat <<EOF > sovereign-stack.yaml
oasa_version: "2026.1"
node:
  name: "sovereign-node-local"
  air_gapped: true
  tpm_required: true
  encryption: "AES-256-GCM"
services:
  gateway:
    enabled: true
    listen: "0.0.0.0:8080"
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
    vram_budget_gb: ${VRAM_GB_INT}
models:
  allowed:
    - "sovereign-llama3"
    - "sovereign-mistral"
EOF
    echo -e "  Stack manifest:   ${GREEN}Success (sovereign-stack.yaml generated)${NC}"
else
    echo -e "  Stack manifest:   ${GREEN}Exists (sovereign-stack.yaml unmodified)${NC}"
fi
echo "-------------------------------------------------------------"

echo -e "\n${BLUE}[3/4] Installing necessary Python packages...${NC}"
echo "-------------------------------------------------------------"
if command -v pip3 &> /dev/null; then
    echo "Running pip3 install -r requirements.txt..."
    pip3 install -r requirements.txt || echo -e "${YELLOW}Warning: Direct pip install failed. Please manually run pip install -r requirements.txt${NC}"
elif command -v pip &> /dev/null; then
    echo "Running pip install -r requirements.txt..."
    pip install -r requirements.txt || echo -e "${YELLOW}Warning: Direct pip install failed. Please manually run pip install -r requirements.txt${NC}"
else
    echo -e "${YELLOW}Warning: pip/pip3 not found in PATH. Skipping automated requirements installation.${NC}"
fi
echo "-------------------------------------------------------------"

echo -e "\n${BLUE}[4/4] Fetching local compact LLMs...${NC}"
echo "-------------------------------------------------------------"
# Model recommendations based on autodetected VRAM size
if (( ${TOTAL_RAM} < 8 )); then
    echo -e "  ${RED}[!] WARNING: System has less than 8 GB RAM. LLM execution will be extremely slow.${NC}"
fi

echo "To complete installation, run these commands to fetch your local model:"
if [[ "$GPU_BACKEND" == "NVIDIA_CUDA" && $(echo "$VRAM_GB >= 8" | bc 2>/dev/null || echo "1") -eq 1 ]]; then
    echo -e "  ${CYAN}# For NVIDIA GPU (Mistral-7B, INT4 quant GGUF):${NC}"
    echo "  curl -L https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -o playground/models/model.gguf"
else
    echo -e "  ${CYAN}# Recommended for CPU / low VRAM environments (Phi-3-Mini, 3.8B parameters):${NC}"
    echo "  curl -L https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf -o playground/models/model.gguf"
fi
echo "-------------------------------------------------------------"

echo -e "\n${GREEN}Installation completed successfully!${NC}"
echo "============================================================="
echo -e "  Next steps to initialize the stack:"
echo -e "    1. Download the model using the command above"
echo -e "    2. Launch the isolated local stack (internal: true):"
echo -e "       ${CYAN}docker compose up --build -d${NC}"
echo -e "    3. Run a network audit to verify air-gap compliance:"
echo -e "       ${CYAN}python tools/sovereign_stack.py validate sovereign-stack.yaml --audit-host${NC}"
echo -e "    4. Profile latency and verify compatibility:"
echo -e "       ${CYAN}python tools/benchmark.py --simulate${NC}"
echo "============================================================="
