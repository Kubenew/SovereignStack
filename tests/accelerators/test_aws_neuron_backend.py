from types import SimpleNamespace
import sys
import pytest
from integrations.accelerators.aws_neuron.backend import (
    NeuronBackend,
    NeuronConfig,
    NeuronUnavailable,
    NeuronCompilationError,
    NeuronModelWrapper,
)
from integrations.accelerators.aws_neuron.policy import (
    NeuronPolicyAdapter,
    NeuronAuthorizationError,
)
from integrations.accelerators.aws_neuron.provenance import (
    NeuronProvenanceRecorder,
    NeuronVerificationAdapter,
    compute_object_digest,
)
from integrations.accelerators.aws_neuron.hardware import NeuronHardwareDetector
from integrations.accelerators.aws_neuron.router import NeuronModelRouter


class FakeTorch:
    class accelerator:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def current_accelerator():
            return "neuron"

        @staticmethod
        def device_count():
            return 2

    class jit:
        @staticmethod
        def load(path_or_buf):
            class FakeJitModule:
                def __init__(self):
                    self.is_compiled_neuron = True
                    self.loaded_from = str(path_or_buf)

                def __call__(self, *args, **kwargs):
                    return "neuron_output"

            return FakeJitModule()

    @staticmethod
    def device(name):
        if name != "neuron":
            raise RuntimeError()
        return name

    @staticmethod
    def compile(model):
        model.compiled = True
        return model


# ============================================================================
# BASELINE TESTS (100% Backward Compatible)
# ============================================================================

def test_native_detection():
    b = NeuronBackend(NeuronConfig(mode="native"), FakeTorch, lambda n: object() if n == "torch_neuronx" else None)
    h = b.health()
    assert h["available"] and h["framework"] == "native" and h["device_count"] == 2


def test_native_model_load_and_optional_compile():
    class Model:
        def to(self, d):
            self.device = d
            return self

    b = NeuronBackend(NeuronConfig(mode="native", compile_model=True), FakeTorch, lambda n: object())
    m = b.load_model(Model())
    assert m.device == "neuron" and m.compiled


def test_unavailable_fails_closed():
    b = NeuronBackend(NeuronConfig(mode="xla"), SimpleNamespace(), lambda n: None)
    with pytest.raises(NeuronUnavailable):
        b.load_model(object())


def test_inf1_detection_does_not_claim_generic_execution():
    b = NeuronBackend(NeuronConfig(mode="legacy"), SimpleNamespace(), lambda n: object() if n == "torch_neuron" else None)
    assert b.health()["hardware_generation"] == "Inf1"
    with pytest.raises(NeuronUnavailable):
        b.load_model(object())


# ============================================================================
# EXPANDED TESTS: TORCH-NEURON (LEGACY INF1) & NEURONX COMPILATION / LOADING
# ============================================================================

def test_legacy_torch_neuron_trace_and_execution(monkeypatch):
    class FakeNeuronModule:
        @staticmethod
        def trace(model, example_inputs, **kwargs):
            class TracedScriptModule:
                def __init__(self):
                    self.is_compiled_neuron = True
                    self.compiler = "torch.neuron"

                def __call__(self, *args, **kwargs):
                    return "inf1_inferred_tensor"

            return TracedScriptModule()

    fake_torch = SimpleNamespace(
        neuron=FakeNeuronModule(),
        jit=FakeTorch.jit,
    )

    b = NeuronBackend(
        NeuronConfig(mode="legacy"),
        torch_module=fake_torch,
        module_finder=lambda n: object() if n == "torch_neuron" else None,
    )

    class DummyModel:
        def __call__(self, x):
            return x

    traced = b.trace_model(DummyModel(), example_inputs="test_input")
    assert isinstance(traced, NeuronModelWrapper)
    assert traced.framework == "legacy"
    assert traced("test_input") == "inf1_inferred_tensor"


def test_compiled_artifact_loading_with_digest_verification(tmp_path):
    artifact_file = tmp_path / "model_neuron.pt"
    artifact_file.write_bytes(b"FAKE_NEURON_NEFF_BYTECODE_CONTENT")

    expected_hash = compute_object_digest(b"FAKE_NEURON_NEFF_BYTECODE_CONTENT")

    b = NeuronBackend(
        NeuronConfig(mode="legacy"),
        torch_module=FakeTorch,
        module_finder=lambda n: object() if n == "torch_neuron" else None,
    )

    loaded = b.load_compiled_artifact(str(artifact_file), expected_digest=expected_hash)
    assert isinstance(loaded, NeuronModelWrapper)
    assert loaded("input") == "neuron_output"
    assert loaded.artifact_digest == expected_hash

    # Test tampering detection
    with pytest.raises(NeuronUnavailable, match="Artifact digest mismatch"):
        b.load_compiled_artifact(str(artifact_file), expected_digest="corrupted_hash_value_1234")


def test_xla_model_load_and_step_synchronization(monkeypatch):
    class FakeXLA:
        steps_marked = 0

        @classmethod
        def xla_device(cls):
            return "xla:0"

        @classmethod
        def mark_step(cls):
            cls.steps_marked += 1

    monkeypatch.setitem(sys.modules, "torch_xla", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "torch_xla.core", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "torch_xla.core.xla_model", FakeXLA)

    class Model:
        def to(self, d):
            self.device = d
            return self

        def __call__(self, x):
            return f"xla_output({x})"

    b = NeuronBackend(
        NeuronConfig(mode="xla"),
        torch_module=SimpleNamespace(),
        module_finder=lambda n: object() if n in ("torch_neuronx", "torch_xla") else None,
    )

    loaded_model, dev = b.load_model(Model())
    assert dev == "xla:0"
    assert loaded_model.device == "xla:0"

    # Test execution wrapper synchronization
    wrapper = NeuronModelWrapper(loaded_model, backend=b, framework="xla", device=dev)
    res = wrapper("input_token")
    assert res == "xla_output(input_token)"
    assert FakeXLA.steps_marked >= 1


def test_cpu_fallback_when_explicitly_configured():
    class Model:
        def __call__(self, x):
            return f"cpu_eval({x})"

    # Without allow_cpu_fallback, fails closed
    b_strict = NeuronBackend(NeuronConfig(mode="auto", allow_cpu_fallback=False), SimpleNamespace(), lambda n: None)
    with pytest.raises(NeuronUnavailable):
        b_strict.load_model(Model())

    # With allow_cpu_fallback, returns original model
    b_fallback = NeuronBackend(NeuronConfig(mode="auto", allow_cpu_fallback=True), SimpleNamespace(), lambda n: None)
    m = b_fallback.load_model(Model())
    assert m("data") == "cpu_eval(data)"


# ============================================================================
# OASA GOVERNANCE, POLICY & ANTI-THEATER INVARIANT TESTS
# ============================================================================

def test_oasa_policy_authorization_and_anti_theater():
    policy = NeuronPolicyAdapter()
    prov = NeuronProvenanceRecorder()

    b = NeuronBackend(
        NeuronConfig(mode="native", enforce_policy=True),
        torch_module=FakeTorch,
        module_finder=lambda n: object(),
        policy_adapter=policy,
        provenance_recorder=prov,
    )

    class Model:
        called = False

        def to(self, d):
            self.called = True
            return self

    # 1. Allowed request succeeds
    m = Model()
    loaded = b.load_model(m, context={"security_tier": "air-gapped"})
    assert m.called is True

    # 2. Denied request halts BEFORE touching model/accelerator (Anti-Theater)
    m2 = Model()
    with pytest.raises(NeuronAuthorizationError, match="Explicit restriction"):
        b.load_model(m2, context={"restricted": True})

    # Crucial check: m2 was NEVER called!
    assert m2.called is False


def test_provenance_chain_integrity_and_tamper_evidence():
    prov = NeuronProvenanceRecorder()
    b = NeuronBackend(
        NeuronConfig(mode="native", record_provenance=True),
        torch_module=FakeTorch,
        module_finder=lambda n: object(),
        provenance_recorder=prov,
    )

    class Model:
        def to(self, d):
            return self

        def __call__(self, x):
            return {"token": "hello"}

    model = b.load_model(Model())
    b.infer(model, "prompt_1")
    b.infer(model, "prompt_2")

    assert len(prov.chain) == 3
    assert prov.verify_chain_integrity() is True

    # Tamper with chain
    prov.chain[1]["facts"]["tampered"] = True
    assert prov.verify_chain_integrity() is False


def test_oasa_independent_evidence_generation():
    b = NeuronBackend(
        NeuronConfig(mode="native", record_provenance=True),
        torch_module=FakeTorch,
        module_finder=lambda n: object(),
    )

    class Model:
        def to(self, d):
            return self

        def __call__(self, x):
            return "pred"

    m = b.load_model(Model())
    b.infer(m, "test")

    evidence = b.generate_evidence(workload_uri="model://llama3-neuron", operation="accelerator:neuron:infer")
    assert evidence["platform"] == "sovereignstack-aws-neuron"
    assert evidence["profile"] == "oasa-profile://accelerator-neuron/v0.1"
    assert evidence["evidence"]["integrity"] == "valid"
    assert evidence["conformance"]["accelerator-neuron-0.1"] == "PASS"
    assert evidence["provenance"]["entries"] >= 2


# ============================================================================
# HARDWARE SCANNER & MODEL ROUTER TESTS
# ============================================================================

def test_neuron_hardware_detector_with_mock_runner():
    mock_neuron_ls_json = """[
        {"neuron_device_id": 0, "neuron_core_count": 2, "memory_size": 34359738368, "pci_bdf": "0000:00:1f.0"},
        {"neuron_device_id": 1, "neuron_core_count": 2, "memory_size": 34359738368, "pci_bdf": "0000:00:20.0"}
    ]"""

    def mock_runner(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout=mock_neuron_ls_json)

    detector = NeuronHardwareDetector(command_runner=mock_runner)
    hw = detector.detect()

    assert hw["available"] is True
    assert hw["device_count"] == 2
    assert hw["total_cores"] == 4
    assert hw["total_memory_gb"] == 64.0
    assert hw["discovery_method"] == "neuron-ls"


def test_neuron_model_router():
    router = NeuronModelRouter()

    # Small model fits easily on single Inf2 device
    dec_small = router.route_workload("Llama-3.1-8B", precision="bfloat16")
    assert dec_small.allowed is True
    assert dec_small.backend == "aws-neuron"
    assert dec_small.recommended_sku == "inf2.xlarge"

    # Large model with limited device memory is rejected safely
    limited_hw = {"total_cores": 2, "total_memory_gb": 16.0, "generation": "NeuronCore-v2"}
    dec_large = router.route_workload("Llama-3.1-70B", precision="bfloat16", hardware_info=limited_hw)
    assert dec_large.allowed is False
    assert "Insufficient device memory" in dec_large.reason
