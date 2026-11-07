"""
Optional AWS Neuron backend; safe to import without Neuron installed.
Provides SovereignStack integration for Native TorchNeuron, torch-neuronx (XLA/Trace),
and legacy Inf1 torch-neuron architectures with OASA policy, provenance, and verification.
"""

from dataclasses import dataclass, field
from importlib.util import find_spec
from typing import Any, Literal, Optional, Dict, Tuple, List
import uuid

from .policy import NeuronPolicyAdapter, NeuronAuthorizationError
from .provenance import (
    NeuronProvenanceRecorder,
    NeuronVerificationAdapter,
    compute_object_digest,
)
from .hardware import NeuronHardwareDetector


class NeuronUnavailable(RuntimeError):
    """Raised when AWS Neuron hardware or required dependencies are unavailable."""
    pass


class NeuronCompilationError(RuntimeError):
    """Raised when compilation or tracing fails on Neuron compiler."""
    pass


@dataclass(frozen=True)
class NeuronConfig:
    mode: Literal["auto", "native", "xla", "legacy"] = "auto"
    compile_model: bool = False
    allow_cpu_fallback: bool = False
    compiler_args: Dict[str, Any] = field(default_factory=dict)
    target_instance_sku: str = "auto"
    enforce_policy: bool = False
    record_provenance: bool = True


class NeuronModelWrapper:
    """
    Managed execution wrapper for models running on AWS Neuron accelerators.
    Handles device placement, XLA step synchronization, and output formatting.
    """

    def __init__(
        self,
        model: Any,
        backend: "NeuronBackend",
        framework: str,
        device: Any = "neuron",
        artifact_digest: Optional[str] = None,
    ):
        self.raw_model = model
        self.backend = backend
        self.framework = framework
        self.device = device
        self.artifact_digest = artifact_digest or compute_object_digest(model)

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):
        # Move inputs to target device if supported
        t = self.backend._torch_opt()
        if t is not None:
            new_args = []
            for arg in args:
                if hasattr(arg, "to") and self.device not in (None, "cpu"):
                    try:
                        new_args.append(arg.to(self.device))
                    except Exception:
                        new_args.append(arg)
                else:
                    new_args.append(arg)
            args = tuple(new_args)

        # Call underlying model
        output = self.raw_model(*args, **kwargs)

        # If XLA execution, synchronize graph execution
        if self.framework == "xla":
            try:
                import sys
                xm = sys.modules.get("torch_xla.core.xla_model")
                if xm is None:
                    import torch_xla.core.xla_model as xm
                xm.mark_step()
            except (ImportError, AttributeError):
                pass

        return output

    def __getattr__(self, name: str) -> Any:
        return getattr(self.raw_model, name)


class NeuronBackend:
    name = "aws-neuron"
    version = "0.2.0"

    def __init__(
        self,
        config: Optional[NeuronConfig] = None,
        torch_module: Optional[Any] = None,
        module_finder: Any = find_spec,
        hardware_detector: Optional[NeuronHardwareDetector] = None,
        policy_adapter: Optional[NeuronPolicyAdapter] = None,
        provenance_recorder: Optional[NeuronProvenanceRecorder] = None,
    ):
        self.config = config or NeuronConfig()
        self.torch = torch_module
        self.find = module_finder
        self.kind = None
        self.hardware_detector = hardware_detector or NeuronHardwareDetector()
        self.policy_adapter = policy_adapter or NeuronPolicyAdapter()
        self.provenance_recorder = provenance_recorder or NeuronProvenanceRecorder()
        self.verification_adapter = NeuronVerificationAdapter()

    def _torch_opt(self) -> Optional[Any]:
        if self.torch is not None:
            return self.torch
        try:
            import torch
            self.torch = torch
            return self.torch
        except ImportError:
            return None

    def _torch(self) -> Any:
        t = self._torch_opt()
        if t is None:
            raise NeuronUnavailable("PyTorch is not installed")
        return t

    def detect(self) -> Optional[str]:
        mode = self.config.mode
        if mode in ("auto", "native"):
            try:
                t = self._torch()
                if hasattr(t, "accelerator") and t.accelerator.is_available():
                    if "neuron" in str(t.accelerator.current_accelerator()).lower():
                        self.kind = "native"
                        return self.kind
                if hasattr(t, "device"):
                    try:
                        t.device("neuron")
                        if self.find("torch_neuronx") is not None:
                            self.kind = "native"
                            return self.kind
                    except (RuntimeError, ValueError, TypeError):
                        pass
            except NeuronUnavailable:
                if mode == "native":
                    raise
        if mode in ("auto", "xla") and self.find("torch_neuronx") and self.find("torch_xla"):
            self.kind = "xla"
            return self.kind
        if mode in ("auto", "legacy") and self.find("torch_neuron"):
            self.kind = "legacy"
            return self.kind
        return None

    def health(self) -> Dict[str, Any]:
        kind = self.detect()
        count = 0
        if kind == "native":
            try:
                count = int(self._torch().accelerator.device_count())
            except Exception:
                count = 1
        elif kind:
            count = 1

        hw_gen = {
            "native": "validate Trn2/Trn3 SKU and SDK",
            "xla": "Inf2/Trn1/Trn2; version-dependent",
            "legacy": "Inf1",
        }.get(kind, "unknown")

        return {
            "backend": self.name,
            "version": self.version,
            "available": bool(kind),
            "framework": kind,
            "device": "neuron" if kind == "native" else ("xla" if kind == "xla" else None),
            "device_count": count,
            "hardware_generation": hw_gen,
            "execution_enabled": kind in ("native", "xla"),
            "policy_enforced": self.config.enforce_policy,
            "provenance_chain_length": len(self.provenance_recorder.chain),
        }

    def load_model(self, model: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Load a model onto the detected Neuron accelerator.
        Returns loaded model (or (model, device) for XLA).
        Enforces OASA policy and records provenance if configured.
        """
        if self.config.enforce_policy:
            self.policy_adapter.authorize(
                operation="accelerator:neuron:load",
                identity_uri="system://sovereign-node",
                context=context or {},
            )

        kind = self.detect()
        model_digest = compute_object_digest(model)

        if kind == "native":
            try:
                loaded = model.to("neuron")
                if self.config.compile_model:
                    loaded = self._torch().compile(loaded)

                if self.config.record_provenance:
                    self.provenance_recorder.record_event(
                        event_type="accelerator.neuron.load",
                        operation="accelerator:neuron:load",
                        actor_id="system://sovereign-node",
                        facts={
                            "framework": "native",
                            "model_digest": model_digest,
                            "compiled": bool(self.config.compile_model),
                            "device": "neuron",
                        },
                    )
                return loaded
            except Exception as exc:
                raise NeuronUnavailable(f"Native Neuron model load failed: {exc}") from exc

        if kind == "xla":
            try:
                import sys
                xm = sys.modules.get("torch_xla.core.xla_model")
                if xm is None:
                    import torch_xla.core.xla_model as xm
                device = xm.xla_device()
                loaded = model.to(device)

                if self.config.record_provenance:
                    self.provenance_recorder.record_event(
                        event_type="accelerator.neuron.load",
                        operation="accelerator:neuron:load",
                        actor_id="system://sovereign-node",
                        facts={
                            "framework": "xla",
                            "model_digest": model_digest,
                            "device": str(device),
                        },
                    )
                return loaded, device
            except Exception as exc:
                raise NeuronUnavailable(f"Neuron XLA model load failed: {exc}") from exc

        if kind == "legacy":
            # For Inf1 torch-neuron, only precompiled TorchScript models can execute directly.
            # Generic uncompiled models cannot be moved without tracing.
            is_precompiled = (
                getattr(model, "is_compiled_neuron", False)
                or hasattr(model, "graph")
                or type(model).__name__ in ("ScriptModule", "RecursiveScriptModule")
            )
            if is_precompiled:
                if self.config.record_provenance:
                    self.provenance_recorder.record_event(
                        event_type="accelerator.neuron.load_legacy",
                        operation="accelerator:neuron:load",
                        actor_id="system://sovereign-node",
                        facts={
                            "framework": "legacy",
                            "model_digest": model_digest,
                            "hardware": "Inf1",
                        },
                    )
                return model
            raise NeuronUnavailable(
                "Inf1 torch-neuron is archived; use a dedicated pinned legacy artifact loader or trace_model()"
            )

        if self.config.allow_cpu_fallback:
            if self.config.record_provenance:
                self.provenance_recorder.record_event(
                    event_type="accelerator.neuron.cpu_fallback",
                    operation="accelerator:neuron:load",
                    actor_id="system://sovereign-node",
                    facts={"model_digest": model_digest, "fallback": "cpu"},
                )
            return model

        raise NeuronUnavailable("Neuron requested but no compatible Neuron runtime/device detected")

    def load_compiled_artifact(
        self,
        artifact_path_or_buffer: Any,
        expected_digest: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> NeuronModelWrapper:
        """
        Load a serialized TorchScript / NEFF model compiled for Neuron.
        Verifies SHA-256 digest before loading.
        """
        if self.config.enforce_policy:
            self.policy_adapter.authorize(
                operation="accelerator:neuron:load",
                identity_uri="system://sovereign-node",
                context=context or {},
            )

        t = self._torch()
        artifact_digest = None

        # Hash inspection if it's a file path or bytes
        if isinstance(artifact_path_or_buffer, str):
            import os
            if not os.path.exists(artifact_path_or_buffer):
                raise NeuronUnavailable(f"Artifact not found: {artifact_path_or_buffer}")
            with open(artifact_path_or_buffer, "rb") as f:
                content = f.read()
                artifact_digest = compute_object_digest(content)
        elif isinstance(artifact_path_or_buffer, (bytes, bytearray)):
            artifact_digest = compute_object_digest(artifact_path_or_buffer)

        if expected_digest and artifact_digest and expected_digest != artifact_digest:
            raise NeuronUnavailable(
                f"Artifact digest mismatch: expected {expected_digest}, computed {artifact_digest}"
            )

        try:
            loaded_jit = t.jit.load(artifact_path_or_buffer)
        except Exception as exc:
            raise NeuronUnavailable(f"Failed to load compiled Neuron artifact via torch.jit.load: {exc}") from exc

        kind = self.detect() or "legacy"
        target_device = "neuron" if kind == "native" else ("xla" if kind == "xla" else "cpu")

        if self.config.record_provenance:
            self.provenance_recorder.record_event(
                event_type="accelerator.neuron.load_artifact",
                operation="accelerator:neuron:load",
                actor_id="system://sovereign-node",
                facts={
                    "artifact_digest": artifact_digest or "unknown",
                    "framework": kind,
                    "target_device": target_device,
                },
            )

        return NeuronModelWrapper(
            model=loaded_jit,
            backend=self,
            framework=kind,
            device=target_device,
            artifact_digest=artifact_digest,
        )

    def trace_model(
        self,
        model: Any,
        example_inputs: Any,
        compiler_args: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> NeuronModelWrapper:
        """
        Compile an eager PyTorch model into a Neuron-optimized TorchScript module.
        Supports both torch_neuronx.trace() (Inf2/Trn1/Trn2) and torch.neuron.trace() (Inf1).
        """
        if self.config.enforce_policy:
            self.policy_adapter.authorize(
                operation="accelerator:neuron:trace",
                identity_uri="system://sovereign-node",
                context=context or {},
            )

        kind = self.detect()
        if not kind:
            raise NeuronUnavailable("Cannot trace model: no supported Neuron compiler detected")

        compiler_args = compiler_args or self.config.compiler_args or {}
        traced_model = None

        if kind in ("native", "xla"):
            try:
                import torch_neuronx
                traced_model = torch_neuronx.trace(model, example_inputs, **compiler_args)
            except Exception as exc:
                raise NeuronCompilationError(f"torch_neuronx.trace compilation failed: {exc}") from exc
        elif kind == "legacy":
            try:
                t = self._torch()
                if hasattr(t, "neuron") and hasattr(t.neuron, "trace"):
                    traced_model = t.neuron.trace(model, example_inputs, **compiler_args)
                else:
                    import torch_neuron
                    traced_model = torch_neuron.trace(model, example_inputs, **compiler_args)
            except Exception as exc:
                raise NeuronCompilationError(f"torch.neuron.trace compilation failed: {exc}") from exc

        artifact_digest = compute_object_digest(traced_model)

        if self.config.record_provenance:
            self.provenance_recorder.record_event(
                event_type="accelerator.neuron.trace",
                operation="accelerator:neuron:trace",
                actor_id="system://sovereign-node",
                facts={
                    "framework": kind,
                    "compiler_args": compiler_args,
                    "artifact_digest": artifact_digest,
                },
            )

        return NeuronModelWrapper(
            model=traced_model,
            backend=self,
            framework=kind,
            device="neuron" if kind == "native" else "cpu",
            artifact_digest=artifact_digest,
        )

    def infer(
        self,
        model_or_wrapper: Any,
        *inputs: Any,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute inference on Neuron accelerator with step synchronization and provenance.
        """
        if self.config.enforce_policy:
            self.policy_adapter.authorize(
                operation="accelerator:neuron:infer",
                identity_uri="system://sovereign-node",
                context=context or {},
            )

        req_id = request_id or f"inf-{uuid.uuid4().hex[:12]}"
        wrapper = (
            model_or_wrapper
            if isinstance(model_or_wrapper, NeuronModelWrapper)
            else NeuronModelWrapper(
                model=model_or_wrapper,
                backend=self,
                framework=self.detect() or "cpu",
                device="neuron" if self.detect() == "native" else "cpu",
            )
        )

        output = wrapper(*inputs, **kwargs)
        result_digest = compute_object_digest(output)

        if self.config.record_provenance:
            self.provenance_recorder.record_event(
                event_type="accelerator.neuron.infer",
                operation="accelerator:neuron:infer",
                actor_id="system://sovereign-node",
                request_id=req_id,
                facts={
                    "model_digest": wrapper.artifact_digest,
                    "result_digest": result_digest,
                    "framework": wrapper.framework,
                },
            )

        return output

    def generate_evidence(
        self,
        workload_uri: str = "model://sovereign-neuron-workload",
        operation: str = "accelerator:neuron:infer",
        authorization_decision: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an OASA L3 compliance evidence package for external audit.
        """
        auth = authorization_decision or {
            "decision": "allow",
            "policy_ref": "policy://accelerator/neuron/standard",
        }
        return self.verification_adapter.generate_evidence(
            workload_uri=workload_uri,
            operation=operation,
            authorization=auth,
            provenance_chain=self.provenance_recorder.chain,
            hardware_facts=self.health(),
        )
