#!/usr/bin/env python3
"""
OASA VRAM & KV Cache Calculator
================================
Estimates the precise VRAM requirements for running quantized LLMs on sovereign hardware.
Calculates weights, KV cache, and runtime activation memory overhead.

Evaluates model parameter size (e.g. 8B, 32B, 70B, 123B), precision/quantization formats
(FP16, INT8, INT4, AWQ, GGUF, INT2), context window overhead (KV Cache memory consumption),
and batch size overhead. Provides green/yellow/red compliance statuses against local GPU budgets.

Usage:
    python tools/vram_calculator.py --params 70B --quant INT4 --context 8192 --batch 2
    python tools/vram_calculator.py --params 70B --quant INT4 --context 8192 --budget 24
    python tools/vram_calculator.py --autodetect
    python tools/vram_calculator.py --params 8B --quant GGUF --context 4096 --batch 4 --budget 12
"""

import argparse
import sys
import re
import subprocess
import math
from pathlib import Path
from typing import Dict, Any, Optional

# Fix Windows console encoding
import io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Standard bytes per parameter per precision/quantization format
QUANT_PRECISIONS = {
    "FP16": 2.0,
    "INT8": 1.0,
    "INT4": 0.5,
    "AWQ": 0.5,
    "GPTQ": 0.5,
    "GGUF": 0.5,  # Q4 average
    "INT2": 0.25,
}

# Preconfigured popular LLM architectures for high-fidelity KV Cache calculations
MODEL_TEMPLATES = {
    "8B": {"layers": 32, "kv_heads": 8, "head_dim": 128, "name": "Llama-3-8B / Qwen-8B class"},
    "14B": {"layers": 40, "kv_heads": 8, "head_dim": 128, "name": "Phi-3-Medium / Qwen-14B class"},
    "32B": {"layers": 64, "kv_heads": 8, "head_dim": 128, "name": "Qwen-2.5-32B class"},
    "70B": {"layers": 80, "kv_heads": 8, "head_dim": 128, "name": "Llama-3-70B / Qwen-72B class"},
    "123B": {"layers": 80, "kv_heads": 8, "head_dim": 128, "name": "Mistral-Large-123B class"},
}

# Common GPU models with known VRAM for reference display
GPU_REFERENCE = {
    4:  "GTX 1650 / RTX 3050 (4 GB)",
    6:  "RTX 2060 / RTX 4050 (6 GB)",
    8:  "RTX 3060 Ti / RTX 4060 (8 GB)",
    10: "RTX 3080 (10 GB)",
    12: "RTX 3060 12GB / RTX 4070 (12 GB)",
    16: "RTX 4080 / A4000 (16 GB)",
    24: "RTX 3090 / RTX 4090 / A5000 (24 GB)",
    32: "V100 32GB (32 GB)",
    40: "A100 40GB (40 GB)",
    48: "A6000 / RTX 6000 Ada (48 GB)",
    80: "A100 80GB / H100 (80 GB)",
}


def parse_param_size(param_str: str) -> float:
    """Parse parameter size from strings like '70B', '8b', '3.8B', '7B' to raw billions float."""
    match = re.match(r"^([\d\.]+)\s*([mMbB]?)$", param_str.strip())
    if not match:
        raise ValueError(f"Could not parse parameter size '{param_str}'. Use format like '70B' or '8B'.")
    
    val = float(match.group(1))
    unit = match.group(2).upper()
    
    if unit in ("M", "MILLION"):
        return val / 1000.0  # Expressed in billions
    return val  # Default to billions (B)


def detect_local_vram() -> float:
    """Attempts to auto-detect total physical VRAM on local host GPU(s) in GB."""
    # 1. NVIDIA CUDA
    try:
        raw_vram = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        )
        total_vram_mb = sum(int(line.strip()) for line in raw_vram.strip().split("\n") if line.strip())
        return round(total_vram_mb / 1024.0, 1)
    except Exception:
        pass

    # 2. Apple Silicon
    try:
        import json as _json
        res = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True, text=True, timeout=5, stderr=subprocess.DEVNULL
        )
        if res.returncode == 0:
            data = _json.loads(res.stdout)
            total_vram_gb = 0.0
            for d in data.get("SPDisplaysDataType", []):
                vram_shared = d.get("spdisplays_vram_shared") or d.get("spdisplays_vram")
                if vram_shared:
                    m = re.search(r"(\d+)", str(vram_shared))
                    if m:
                        total_vram_gb += int(m.group(1)) / 1024.0
            if total_vram_gb > 0:
                return round(total_vram_gb, 1)
    except Exception:
        pass

    return 0.0


def detect_gpu_name() -> Optional[str]:
    """Attempts to auto-detect the GPU model name."""
    try:
        name = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().split("\n")[0].strip()
        return name
    except Exception:
        pass

    try:
        import platform
        if platform.system() == "Darwin":
            chip = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if "Apple" in chip:
                return f"{chip} (Unified Metal)"
    except Exception:
        pass

    return None


def calculate_vram(
    params_b: float,
    quant: str,
    context_tokens: int,
    batch_size: int,
    layers: int = 32,
    kv_heads: int = 8,
    head_dim: int = 128
) -> Dict[str, Any]:
    """
    Computes VRAM allocations in GB.
    - Weights size (in GB)
    - KV Cache size (in GB)
    - Activation / Execution overhead approximation (in GB)
    """
    bytes_per_param = QUANT_PRECISIONS.get(quant.upper(), 0.5)
    
    # 1. Weight Size
    # parameters * 10^9 * bytes_per_param / 10^9 = parameter size in GB directly
    weight_vram = params_b * bytes_per_param

    # 2. KV Cache Size
    # Formula for modern GQA context cache (using FP16/BF16 representation = 2 bytes/element):
    # 2 (for Key and Value) * layers * kv_heads * head_dim * 2 bytes * context_tokens * batch_size
    # Then convert bytes to GB (1024^3)
    bytes_per_token = 2 * layers * kv_heads * head_dim * 2
    total_kv_bytes = bytes_per_token * context_tokens * batch_size
    kv_cache_vram = total_kv_bytes / (1024**3)

    # 3. Activation & Engine Context Overhead
    # Approximated based on context size and parameter scales
    activation_overhead = 1.0 + (params_b * 0.01) + (context_tokens / 8192.0)

    total_required = weight_vram + kv_cache_vram + activation_overhead

    return {
        "params_b": params_b,
        "quant": quant,
        "bytes_per_param": bytes_per_param,
        "weight_vram_gb": round(weight_vram, 2),
        "kv_cache_vram_gb": round(kv_cache_vram, 2),
        "activation_vram_gb": round(activation_overhead, 2),
        "total_required_gb": round(total_required, 2),
        "bytes_per_token": bytes_per_token,
        "context_tokens": context_tokens,
        "batch_size": batch_size,
    }


def find_nearest_gpu(budget_gb: float) -> Optional[str]:
    """Find the closest matching GPU reference for a given VRAM budget."""
    if budget_gb <= 0:
        return None
    closest = min(GPU_REFERENCE.keys(), key=lambda k: abs(k - budget_gb))
    if abs(closest - budget_gb) <= 4:
        return GPU_REFERENCE[closest]
    return None


def print_calculator_result(res: Dict[str, Any], budget_gb: float, gpu_name: Optional[str] = None):
    """Render the full VRAM estimation report to the console."""
    bits = res['bytes_per_param'] * 8

    print("=" * 65)
    print("            OASA SOVEREIGN VRAM & CONTEXT ESTIMATOR")
    print("=" * 65)

    # Hardware section
    if gpu_name:
        print(f"  Detected GPU:        {gpu_name}")
    ref_gpu = find_nearest_gpu(budget_gb)
    if ref_gpu and not gpu_name:
        print(f"  Reference GPU:       {ref_gpu}")
    print(f"  Target VRAM Budget:  {budget_gb:.1f} GB")
    print("-" * 65)

    # Model section
    print(f"  Model Size:          {res['params_b']:.1f} Billion parameters")
    print(f"  Quantization Format: {res['quant']} ({bits:.0f}-bit execution)")
    print(f"  Context Window:      {res['context_tokens']:,} tokens")
    print(f"  Batch Size:          {res['batch_size']}")
    print("-" * 65)

    # Memory breakdown
    total = res["total_required_gb"]
    bar_width = 40

    print("  MEMORY BREAKDOWN:")
    print()

    # Weight bar
    w_pct = (res['weight_vram_gb'] / total * 100) if total > 0 else 0
    w_bar = int(w_pct / 100 * bar_width)
    print(f"  1. Model Weights:     {res['weight_vram_gb']:6.2f} GB  ({w_pct:.0f}%)")
    print(f"     [{'#' * w_bar}{'-' * (bar_width - w_bar)}]")

    # KV Cache bar
    k_pct = (res['kv_cache_vram_gb'] / total * 100) if total > 0 else 0
    k_bar = int(k_pct / 100 * bar_width)
    print(f"  2. KV Cache:          {res['kv_cache_vram_gb']:6.2f} GB  ({k_pct:.0f}%)")
    print(f"     [{'#' * k_bar}{'-' * (bar_width - k_bar)}]")

    # Activation bar
    a_pct = (res['activation_vram_gb'] / total * 100) if total > 0 else 0
    a_bar = int(a_pct / 100 * bar_width)
    print(f"  3. Activations:       {res['activation_vram_gb']:6.2f} GB  ({a_pct:.0f}%)")
    print(f"     [{'#' * a_bar}{'-' * (bar_width - a_bar)}]")

    print()
    print("-" * 65)
    print(f"  TOTAL VRAM REQUIRED: {total:6.2f} GB")
    print("-" * 65)

    if budget_gb <= 0:
        print("  [INFO] No VRAM hardware target specified. Use --budget or --autodetect.")
        print("=" * 65)
        return

    # Budget utilization
    utilization = (total / budget_gb) * 100
    margin = budget_gb - total

    # Visual budget bar
    used_blocks = min(int(utilization / 100 * bar_width), bar_width)
    budget_bar = '#' * used_blocks + '-' * (bar_width - used_blocks)
    print(f"  Budget Utilization:  {utilization:.1f}%")
    print(f"     [{budget_bar}] {total:.1f} / {budget_gb:.1f} GB")
    print()

    if total <= budget_gb:
        print(f"  VERDICT: \033[92m[PASS] GREEN ZONE\033[0m")
        print(f"           Fits within budget with {margin:.1f} GB headroom.")
        print(f"           COMPLIANT with OASA strict local-compute budgets.")
    elif total <= (budget_gb * 1.15):
        print(f"  VERDICT: \033[93m[WARNING] YELLOW ZONE\033[0m")
        print(f"           Tight fit — shortfall of {abs(margin):.1f} GB ({utilization:.0f}% utilization).")
        print()
        print("  RECOMMENDATIONS:")
        if res['batch_size'] > 1:
            print(f"    - Reduce batch size from {res['batch_size']} to 1  (saves ~{res['kv_cache_vram_gb'] * (1 - 1/res['batch_size']):.1f} GB)")
        if res['context_tokens'] > 2048:
            half_ctx = res['context_tokens'] // 2
            print(f"    - Reduce context window from {res['context_tokens']:,} to {half_ctx:,} tokens")
        if res['quant'] != "INT2":
            print(f"    - Increase quantization density (e.g., {res['quant']} -> INT2)")
    else:
        print(f"  VERDICT: \033[91m[FAIL] RED ZONE — OUT OF MEMORY RISK\033[0m")
        print(f"           Shortfall of {abs(margin):.1f} GB ({utilization:.0f}% utilization).")
        print(f"           Model execution WILL crash without a larger GPU or smaller model.")
        print()
        print("  RECOMMENDATIONS:")
        # Calculate what quant would fit
        for q_name, q_bytes in sorted(QUANT_PRECISIONS.items(), key=lambda x: x[1]):
            alt_weight = res['params_b'] * q_bytes
            alt_total = alt_weight + res['kv_cache_vram_gb'] + res['activation_vram_gb']
            if alt_total <= budget_gb:
                print(f"    - Use {q_name} quantization ({q_bytes*8:.0f}-bit) -> ~{alt_total:.1f} GB total")
                break
        # Suggest smaller models
        for size_label, template in sorted(MODEL_TEMPLATES.items(), key=lambda x: parse_param_size(x[0])):
            alt_params = parse_param_size(size_label)
            if alt_params < res['params_b']:
                alt_weight = alt_params * res['bytes_per_param']
                if alt_weight < budget_gb * 0.8:
                    print(f"    - Use {template['name']} (~{alt_weight:.0f} GB weights at {res['quant']})")
                    break
        # Suggest GPU upgrade
        for vram_size in sorted(GPU_REFERENCE.keys()):
            if vram_size >= total * 1.1:
                print(f"    - Upgrade to {GPU_REFERENCE[vram_size]}")
                break

    print("=" * 65)


def run_comparison_table(params_b: float, context_tokens: int, batch_size: int, layers: int, kv_heads: int, head_dim: int, budget_gb: float):
    """Print a comparison table across all quantization formats for the given model."""
    print()
    print("=" * 65)
    print("       QUANTIZATION FORMAT COMPARISON TABLE")
    print("=" * 65)
    print(f"  Model: {params_b:.1f}B | Context: {context_tokens:,} tokens | Batch: {batch_size}")
    if budget_gb > 0:
        print(f"  VRAM Budget: {budget_gb:.1f} GB")
    print("-" * 65)
    print(f"  {'Format':<8} {'Bits':>5} {'Weights':>10} {'KV Cache':>10} {'Total':>10} {'Status':>10}")
    print("-" * 65)

    for q_name in ["FP16", "INT8", "INT4", "AWQ", "GPTQ", "GGUF", "INT2"]:
        res = calculate_vram(params_b, q_name, context_tokens, batch_size, layers, kv_heads, head_dim)
        total = res['total_required_gb']
        bits = QUANT_PRECISIONS[q_name] * 8

        if budget_gb > 0:
            if total <= budget_gb:
                status = "\033[92mPASS\033[0m"
            elif total <= budget_gb * 1.15:
                status = "\033[93mWARN\033[0m"
            else:
                status = "\033[91mFAIL\033[0m"
        else:
            status = "—"

        print(f"  {q_name:<8} {bits:>4.0f}b {res['weight_vram_gb']:>9.1f}G {res['kv_cache_vram_gb']:>9.1f}G {total:>9.1f}G {status:>10}")

    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        description="Estimate VRAM required for deploying quantized local models under OASA standards."
    )
    parser.add_argument("--params", type=str, default="8B", help="Model size in billions of parameters (e.g. 8B, 32B, 70B, 123B)")
    parser.add_argument("--quant", type=str, default="INT4", choices=list(QUANT_PRECISIONS.keys()), help="Model quantization layout format")
    parser.add_argument("--context", type=int, default=4096, help="Maximum context window in tokens")
    parser.add_argument("--batch", type=int, default=1, help="Expected pipeline batch size")
    parser.add_argument("--budget", type=float, default=0.0, help="Specify VRAM target hardware budget in GB manually")
    parser.add_argument("--autodetect", action="store_true", help="Auto-detect local host GPU VRAM and run simulation against it")
    parser.add_argument("--compare", action="store_true", help="Show comparison table across all quantization formats")
    parser.add_argument("--budget-context", action="store_true", help="Calculate maximum context window size for given VRAM budget")
    
    args = parser.parse_args()

    # Hardware Autodetection
    detected_vram = 0.0
    gpu_name = None
    if args.autodetect or args.budget == 0.0:
        detected_vram = detect_local_vram()
        gpu_name = detect_gpu_name()
        if args.autodetect:
            print(f"\n[HARDWARE] Autodetected total local GPU VRAM: {detected_vram} GB")
            if gpu_name:
                print(f"[HARDWARE] GPU Model: {gpu_name}")

    budget = args.budget if args.budget > 0.0 else detected_vram

    # Determine templates
    params_b = 8.0
    layers, kv_heads, head_dim = 32, 8, 128
    
    clean_params = args.params.upper().strip()
    if clean_params in MODEL_TEMPLATES:
        t = MODEL_TEMPLATES[clean_params]
        layers = t["layers"]
        kv_heads = t["kv_heads"]
        head_dim = t["head_dim"]
        params_b = parse_param_size(clean_params)
        print(f"\n[INFO] Applying preconfigured model template: {t['name']}")
    else:
        try:
            params_b = parse_param_size(clean_params)
            # Extrapolate template parameters based on size
            if params_b >= 100:
                layers, kv_heads, head_dim = 80, 8, 128
            elif params_b >= 60:
                layers, kv_heads, head_dim = 80, 8, 128
            elif params_b >= 30:
                layers, kv_heads, head_dim = 64, 8, 128
            elif params_b >= 10:
                layers, kv_heads, head_dim = 40, 8, 128
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    result = calculate_vram(
        params_b=params_b,
        quant=args.quant,
        context_tokens=args.context,
        batch_size=args.batch,
        layers=layers,
        kv_heads=kv_heads,
        head_dim=head_dim
    )

    print_calculator_result(result, budget, gpu_name)

    # Comparison table
    if args.compare:
        run_comparison_table(params_b, args.context, args.batch, layers, kv_heads, head_dim, budget)

    # Dynamic context window sizing from budget
    if args.budget_context and budget > 0:
        weight_vram = params_b * QUANT_PRECISIONS.get(args.quant.upper(), 0.5)
        act_overhead = 1.0 + (params_b * 0.01) + (args.context / 8192.0)
        remaining = budget - weight_vram - act_overhead
        if remaining > 0:
            bytes_per_token = 2 * layers * kv_heads * head_dim * 2
            tokens_per_gb = (1024**3) / bytes_per_token
            max_context = int(remaining * tokens_per_gb)
            batch_factor = args.batch
            max_context = max_context // batch_factor
            print(f"\n  Dynamic Context Sizing ({budget} GB budget):")
            print(f"  {'-'*45}")
            print(f"  Weights ({args.quant:<4}):       {weight_vram:>6.1f} GB")
            print(f"  Activation overhead:  {act_overhead:>6.1f} GB")
            print(f"  Available for KV:     {remaining:>6.1f} GB")
            print(f"  Max context window:   {max_context:>6,} tokens (batch={args.batch})")
            print(f"  {'-'*45}")
        else:
            print(f"\n  [FAIL] Model weights ({weight_vram:.1f} GB) exceed budget ({budget} GB)")

if __name__ == "__main__":
    main()
