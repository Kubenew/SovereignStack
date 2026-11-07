"""
Model Router and Registry integration for AWS Neuron accelerator.
Maps model requirements to optimal NeuronCore architectures and frameworks.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class RouteDecision:
    allowed: bool
    backend: str
    framework: str
    target_device: str
    required_cores: int
    estimated_memory_gb: float
    recommended_sku: str
    reason: str


class NeuronModelRouter:
    """
    Evaluates whether an inference or training workload should be scheduled
    on AWS Neuron, determining optimal core count and framework mode.
    """

    MODEL_SPECS = {
        # Model family estimates
        "llama-3.1-8b": {"params_b": 8.0, "min_cores": 2, "min_mem_gb": 16.0, "ideal_sku": "inf2.xlarge"},
        "llama-3.1-70b": {"params_b": 70.0, "min_cores": 8, "min_mem_gb": 140.0, "ideal_sku": "inf2.24xlarge"},
        "qwen-2.5-32b": {"params_b": 32.0, "min_cores": 4, "min_mem_gb": 64.0, "ideal_sku": "inf2.24xlarge"},
        "qwen-2.5-72b": {"params_b": 72.0, "min_cores": 12, "min_mem_gb": 144.0, "ideal_sku": "inf2.24xlarge"},
        "mistral-7b": {"params_b": 7.0, "min_cores": 2, "min_mem_gb": 14.0, "ideal_sku": "inf2.xlarge"},
        "bert-base": {"params_b": 0.11, "min_cores": 1, "min_mem_gb": 2.0, "ideal_sku": "inf1.xlarge"},
    }

    def route_workload(
        self,
        model_name: str,
        precision: str = "bfloat16",
        hardware_info: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> RouteDecision:
        """
        Determine placement and runtime parameters on Neuron accelerators.
        """
        norm_name = model_name.lower().strip()
        spec = None
        for key, candidate in self.MODEL_SPECS.items():
            if key in norm_name:
                spec = candidate
                break

        if spec is None:
            # Default fallback estimate for unknown models
            spec = {"params_b": 7.0, "min_cores": 2, "min_mem_gb": 16.0, "ideal_sku": "inf2.xlarge"}

        constraints = constraints or {}
        hardware_info = hardware_info or {}

        available_cores = hardware_info.get("total_cores", 0)
        available_mem = hardware_info.get("total_memory_gb", 0.0)
        hw_gen = hardware_info.get("generation", "NeuronCore-v2")

        # Multiplier based on precision
        prec_mult = 2.0 if precision in ("fp32", "float32") else (1.0 if precision in ("fp16", "bfloat16") else 0.5)
        needed_mem = spec["min_mem_gb"] * prec_mult

        # Check capacity if hardware info was provided
        if available_mem > 0 and needed_mem > available_mem:
            return RouteDecision(
                allowed=False,
                backend="aws-neuron",
                framework="unsupported",
                target_device="none",
                required_cores=spec["min_cores"],
                estimated_memory_gb=needed_mem,
                recommended_sku=spec["ideal_sku"],
                reason=f"Insufficient device memory: requires {needed_mem:.1f}GB, host has {available_mem:.1f}GB",
            )

        # Decide framework: Inf1 legacy vs modern native/xla
        if "inf1" in spec.get("ideal_sku", "") and hw_gen == "NeuronCore-v1":
            framework = "legacy"
            target_device = "neuron"
        elif hw_gen in ("NeuronCore-v2", "NeuronCore-v3"):
            framework = "native"
            target_device = "neuron"
        else:
            framework = "xla"
            target_device = "xla"

        return RouteDecision(
            allowed=True,
            backend="aws-neuron",
            framework=framework,
            target_device=target_device,
            required_cores=spec["min_cores"],
            estimated_memory_gb=needed_mem,
            recommended_sku=spec["ideal_sku"],
            reason="Workload fits within NeuronCore compute and memory specifications",
        )

