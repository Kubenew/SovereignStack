# Secure Hardware Enclave Configuration for ZK‑Proof Evaluation

**Status:** Draft – Implementation Guide
**Audience:** Infrastructure engineers, security architects, certification labs
**Version:** 1.0-draft
**Depends on:** RFC-0054 (Compliance Framework), RFC-0057 (Meta‑Cognition), RFC-0061 (Human Override Biometric Protocol)
**Target Platforms:** AWS Nitro Enclaves, Intel SGX/TDX, AMD SEV‑SNP

## Overview

This document specifies how to deploy SovereignStack's zero‑knowledge proof evaluation loops inside hardware‑enforced trusted execution environments (TEEs), achieving air‑gap equivalence even in cloud‑native deployments. When combined with the physical `override://kill-switch` defined in RFC‑0061, this configuration ensures that:

1. ZK‑proof verification (e.g., alignment checks, safety contract validation, meta‑cognitive drift detection) runs in an environment that the host operating system, hypervisor, and cloud provider **cannot inspect or tamper with**.
2. The attestation evidence from the enclave is **cryptographically verifiable** by any third party — a certification lab, a regulator, or a federated sovereign node.
3. If the enclave detects a policy violation or tampering attempt, it can trigger a **physically‑enforced shutdown** via the HSM‑backed kill‑switch, bypassing all software layers.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    HOST (Untrusted)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐ │
│  │ Sovereign│  │ OASA API │  │ Alertmanager → Webhook    │ │
│  │  Node    │  │ Gateway  │  │ (CognitiveAlignmentBreach)│ │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────────┘ │
│       │             │                   │                   │
│       │    vsock    │    vsock          │  HTTP (localhost)  │
│       └─────────────┼───────────────────┘                   │
│                     │                                       │
│  ┌──────────────────▼──────────────────────────────────┐   │
│  │            SECURE ENCLAVE (Trusted)                  │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │         ZK‑Proof Verification Engine          │    │   │
│  │  │  ┌───────────┐  ┌──────────┐  ┌──────────┐  │    │   │
│  │  │  │ Alignment │  │ Safety   │  │ Meta‑Cog │  │    │   │
│  │  │  │ Verifier  │  │ Contract │  │ Drift    │  │    │   │
│  │  │  │           │  │ Validator│  │ Detector │  │    │   │
│  │  │  └───────────┘  └──────────┘  └──────────┘  │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │         Attestation & Policy Engine           │    │   │
│  │  │  • Cryptographic attestation to remote party │    │   │
│  │  │  • Policy decision: ALLOW / VETO / KILL       │    │   │
│  │  │  • Secure logging to append‑only buffer       │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                       │
│                     │ Dedicated GPIO / HSM relay (physical) │
│                     ▼                                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          HSM / Kill‑Switch Actuator                    │  │
│  │  • Receives KILL signal from enclave                  │  │
│  │  • Cuts power to GPU/TPU/NPU accelerators             │  │
│  │  • Signs kill event with hardware‑bound key           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Platform‑Specific Configuration

### Option A: AWS Nitro Enclaves

AWS Nitro Enclaves provide an isolated, hardened VM with no persistent storage, no interactive access, and no external networking except a virtual socket (vsock) to the parent instance.

#### Enclave Image Build
```dockerfile
# Dockerfile.enclave
FROM public.ecr.aws/enclave-image-factory/alpine:latest

# Install SovereignStack enclave runtime
COPY sovereignstack-enclave /usr/local/bin/
COPY zk-circuits/ /etc/sovereignstack/zk-circuits/
COPY policy/enclave-policy.yaml /etc/sovereignstack/policy.yaml

# The enclave runs a minimal, single‑purpose binary
ENTRYPOINT ["/usr/local/bin/sovereignstack-enclave"]
CMD ["--policy", "/etc/sovereignstack/policy.yaml", \
     "--circuits", "/etc/sovereignstack/zk-circuits/", \
     "--vsock-port", "5000"]
```

Build and register:
```bash
# Build the enclave image
nitro-cli build-enclave \
  --docker-uri sovereignstack-enclave:latest \
  --output-file sovereignstack-enclave.eif

# Launch the enclave (2 vCPU, 512 MB memory — adjust for circuit complexity)
nitro-cli run-enclave \
  --eif-path sovereignstack-enclave.eif \
  --cpu-count 2 \
  --memory 512

# Verify attestation document
nitro-cli describe-enclaves
```

#### vsock Communication (Host → Enclave)

The host SovereignStack node sends ZK‑proofs for verification over vsock:
```python
# ss-policy/src/enclave_client.py
import socket
import json
import struct

class NitroEnclaveClient:
    """Sends ZK‑proof verification requests to the Nitro Enclave."""
    
    CID = 4  # Nitro Enclave CID
    PORT = 5000
    
    @staticmethod
    def verify_alignment(proof: bytes, public_inputs: dict) -> dict:
        """Send an alignment proof for verification. Returns the verdict."""
        request = {
            "type": "verify_alignment",
            "proof": proof.hex(),
            "public_inputs": public_inputs
        }
        return NitroEnclaveClient._send(request)
    
    @staticmethod
    def verify_safety_contract(contract: dict, proof: bytes) -> dict:
        """Verify a safety contract's ZK‑proof."""
        request = {
            "type": "verify_safety_contract",
            "contract": contract,
            "proof": proof.hex()
        }
        return NitroEnclaveClient._send(request)
    
    @staticmethod
    def check_meta_drift(agent_id: str, drift_metrics: dict) -> dict:
        """Evaluate meta‑cognitive drift against allowed thresholds."""
        request = {
            "type": "check_meta_drift",
            "agent_id": agent_id,
            "drift_metrics": drift_metrics
        }
        return NitroEnclaveClient._send(request)
    
    @staticmethod
    def _send(request: dict) -> dict:
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.connect((NitroEnclaveClient.CID, NitroEnclaveClient.PORT))
        
        payload = json.dumps(request).encode()
        sock.sendall(struct.pack(">I", len(payload)) + payload)
        
        # Receive response
        length_bytes = sock.recv(4)
        length = struct.unpack(">I", length_bytes)[0]
        response = b""
        while len(response) < length:
            response += sock.recv(length - len(response))
        
        sock.close()
        return json.loads(response)
```

#### Enclave‑Side Logic
```python
# sovereignstack-enclave (inside enclave)
import socket
import json
import struct
from sovereignstack_zk import (
    verify_alignment_proof,
    verify_safety_contract_proof,
    evaluate_meta_drift
)
from sovereignstack_hsm import hsm_send_kill_signal

def main():
    sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    sock.bind((socket.VMADDR_CID_ANY, 5000))
    sock.listen()
    
    while True:
        conn, _ = sock.accept()
        
        # Receive request length
        length_bytes = conn.recv(4)
        length = struct.unpack(">I", length_bytes)[0]
        request = b""
        while len(request) < length:
            request += conn.recv(length - len(request))
        
        data = json.loads(request)
        
        # Route to appropriate verifier
        if data["type"] == "verify_alignment":
            result = verify_alignment_proof(
                bytes.fromhex(data["proof"]),
                data["public_inputs"]
            )
        elif data["type"] == "verify_safety_contract":
            result = verify_safety_contract_proof(
                data["contract"],
                bytes.fromhex(data["proof"])
            )
        elif data["type"] == "check_meta_drift":
            result = evaluate_meta_drift(
                data["agent_id"],
                data["drift_metrics"]
            )
        else:
            result = {"verdict": "UNKNOWN_REQUEST_TYPE", "error": True}
        
        # Policy enforcement
        if result.get("verdict") == "VIOLATION_CRITICAL":
            # Send KILL signal via dedicated hardware path
            hsm_send_kill_signal(
                reason=f"Enclave detected critical violation: {result}",
                evidence=result
            )
        
        # Send response
        response = json.dumps(result).encode()
        conn.sendall(struct.pack(">I", len(response)) + response)
        conn.close()
```

### Option B: Intel SGX / TDX

For on‑premises or bare‑metal deployments, Intel SGX (Software Guard Extensions) or TDX (Trust Domain Extensions) provide enclave capabilities with hardware‑rooted attestation.

#### SGX Enclave Definition (EDL)
```c
// sovereignstack_enclave.edl
enclave {
    trusted {
        public int enclave_verify_alignment(
            [in, size=proof_len] const uint8_t* proof,
            uint32_t proof_len,
            [in, size=inputs_len] const uint8_t* public_inputs,
            uint32_t inputs_len,
            [out, size=result_len] uint8_t* result,
            uint32_t result_len
        );
        
        public int enclave_verify_safety_contract(
            [in, size=contract_len] const uint8_t* contract,
            uint32_t contract_len,
            [in, size=proof_len] const uint8_t* proof,
            uint32_t proof_len,
            [out, size=result_len] uint8_t* result,
            uint32_t result_len
        );
        
        public int enclave_check_meta_drift(
            [in, size=agent_id_len] const uint8_t* agent_id,
            uint32_t agent_id_len,
            [in, size=metrics_len] const uint8_t* drift_metrics,
            uint32_t metrics_len,
            [out, size=result_len] uint8_t* result,
            uint32_t result_len
        );
    };
    
    untrusted {
        // HSM kill‑switch interface (untrusted caller, hardware‑enforced path)
        void hsm_trigger_kill_switch(
            [in, size=evidence_len] const uint8_t* evidence,
            uint32_t evidence_len
        );
    };
};
```

#### SGX Attestation Flow
```python
# ss-policy/src/sgx_client.py
from sovereignstack_sgx import SGXEnclave

class SGXEnclaveVerifier:
    """Verifies proofs inside an Intel SGX enclave with remote attestation."""
    
    def __init__(self, enclave_path: str):
        self.enclave = SGXEnclave(enclave_path)
        self.attestation = self.enclave.get_attestation()
    
    def verify_attestation_with_remote_party(self, verifier_url: str) -> bool:
        """Send attestation quote to a remote verifier (e.g., certification lab)."""
        import requests
        response = requests.post(
            verifier_url,
            json={
                "attestation_quote": self.attestation.quote.hex(),
                "enclave_measurement": self.attestation.mrenclave.hex(),
                "platform_info": self.attestation.platform_info
            }
        )
        return response.json()["verified"]
    
    def verify_alignment(self, proof: bytes, public_inputs: dict) -> dict:
        """Verify alignment proof inside SGX enclave."""
        return self.enclave.enclave_verify_alignment(proof, public_inputs)
    
    def verify_safety_contract(self, contract: dict, proof: bytes) -> dict:
        """Verify safety contract inside SGX enclave."""
        return self.enclave.enclave_verify_safety_contract(contract, proof)
    
    def check_meta_drift(self, agent_id: str, metrics: dict) -> dict:
        """Evaluate meta‑cognitive drift inside SGX enclave."""
        return self.enclave.enclave_check_meta_drift(agent_id, metrics)
```

### Option C: AMD SEV‑SNP

For AMD EPYC‑based deployments, SEV‑SNP (Secure Encrypted Virtualization – Secure Nested Paging) provides confidential computing with hardware attestation.

Configuration follows a similar pattern: the SovereignStack enclave runtime runs inside an SEV‑SNP VM, communicates via vsock or a dedicated memory region, and generates attestation reports verifiable by the AMD Secure Processor.

## HSM Kill‑Switch Integration

Regardless of the enclave platform, the critical safety path is the hardware‑enforced kill‑switch. This is implemented using a Hardware Security Module (HSM) or a Trusted Platform Module (TPM) with a dedicated GPIO relay.

```
Enclave (SGX/Nitro/SEV)
    │
    │ KILL signal (dedicated vsock/SPI/I²C)
    ▼
HSM / Secure Microcontroller (e.g., STM32, Nitro Security Chip, TPM)
    │
    │ GPIO output
    ▼
Power Relay / MOSFET
    │
    │ Cuts power to GPU/TPU/NPU rails
    ▼
AI Accelerators (POWER OFF)
```

HSM firmware requirements:

1. The HSM accepts KILL commands only from an attested enclave (cryptographic proof that the command originated from an authorised enclave measurement).
2. The HSM logs every KILL event with a hardware‑bound monotonic counter and a signed timestamp.
3. The HSM has a physical "re‑arm" mechanism — a key switch, a biometric reader, or a physical button that must be manually activated before the accelerators can be powered on again.
4. The HSM's firmware is immutable after provisioning (write‑protected fuses).

```python
# sovereignstack_hsm.py (enclave-side HSM client)
import serial
import hashlib
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519

class HSMKillSwitch:
    """Interface to the hardware kill‑switch via HSM serial connection."""
    
    def __init__(self, serial_port: str = "/dev/ttyHSM0"):
        self.serial = serial.Serial(serial_port, baudrate=115200, timeout=1)
        self.enclave_key = self._load_enclave_key()
    
    def trigger_kill(self, reason: str, evidence: dict) -> bool:
        """Send KILL command to HSM. Returns True if acknowledged."""
        command = {
            "command": "KILL",
            "reason": reason,
            "evidence": evidence,
            "timestamp": self._get_secure_time(),
            "enclave_measurement": self._get_enclave_measurement()
        }
        
        payload = json.dumps(command).encode()
        signature = self.enclave_key.sign(payload)
        
        # Send command + signature
        self.serial.write(len(payload).to_bytes(2, 'big'))
        self.serial.write(payload)
        self.serial.write(signature)
        
        # Wait for HSM acknowledgement
        ack = self.serial.read(4)
        return ack == b"KACK"
    
    def _load_enclave_key(self) -> ed25519.Ed25519PrivateKey:
        """Load enclave‑bound signing key (sealed to enclave identity)."""
        # In Nitro: derived from attestation document
        # In SGX: sealed to enclave identity via EGETKEY
        # In SEV: derived from launch measurement
        ...
    
    def _get_enclave_measurement(self) -> str:
        """Return the cryptographic measurement of this enclave."""
        ...
    
    def _get_secure_time(self) -> str:
        """Get trusted time (from HSM RTC or attestation timestamp)."""
        ...
```

## Deployment Topology

### Production Deployment (Cloud)

```
┌────────────────────────────────────────────────────┐
│                AWS VPC / Azure VNet                  │
│                                                      │
│  ┌──────────────────┐    ┌──────────────────────┐   │
│  │ SovereignStack    │    │  Nitro Enclave /      │   │
│  │ Node (EC2/VM)    │◄──►│  Confidential VM      │   │
│  │                  │vsock│  (ZK‑Proof Verifier)  │   │
│  └────────┬─────────┘    └──────────┬───────────┘   │
│           │                         │                │
│           │                         │ Dedicated HW   │
│           │                         │ (if available) │
│           ▼                         ▼                │
│  ┌──────────────────────────────────────────────┐   │
│  │  Nitro Security Chip / vTPM                   │   │
│  │  • Attestation                               │   │
│  │  • Secure logging                            │   │
│  │  • (Optional) Hardware kill‑switch relay     │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

### Production Deployment (On‑Premises / Air‑Gapped)

```
┌────────────────────────────────────────────────────┐
│              Secure Rack / SCIF                      │
│                                                      │
│  ┌─────────────┐   ┌─────────────┐                  │
│  │ Sovereign   │   │ SGX/TDX     │                  │
│  │ Node        │◄─►│ Enclave     │                  │
│  │ (Bare Metal)│   │ Server      │                  │
│  └──────┬──────┘   └──────┬──────┘                  │
│         │                 │                          │
│         │                 │ Dedicated GPIO           │
│         ▼                 ▼                          │
│  ┌──────────────────────────────────────────────┐   │
│  │  Hardware Security Module (HSM)                │   │
│  │  • Certified FIPS 140‑3 Level 3                │   │
│  │  • Physical key‑switch for re‑arm              │   │
│  │  • Relay control for accelerator power rails   │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                            │
│                         ▼                            │
│  ┌──────────────────────────────────────────────┐   │
│  │  AI Accelerator Power Distribution            │   │
│  │  • GPU/TPU/NPU power rails (switched)         │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

## Conformance Testing for Enclave Deployments

### Test 1: Attestation Verification
```bash
# Verify enclave measurement matches expected value
sovereignstack enclave attest \
  --expected-mrenclave "sha256:expected-hash" \
  --verifier-url "https://certification-lab.example.com/verify"
```

### Test 2: ZK‑Proof Verification Inside Enclave
```python
# conformance/level-4-agi/test_enclave_zkp.py
class TestEnclaveZKProofVerification:
    
    def test_alignment_proof_verified_in_enclave(self):
        # Given: a valid alignment proof and a running enclave
        proof, public_inputs = self._generate_test_alignment_proof()
        
        # When: verification is requested
        result = self.enclave_client.verify_alignment(proof, public_inputs)
        
        # Then: the verdict is signed by the enclave identity
        self.assertEqual(result["verdict"], "ALIGNED")
        self.assertTrue(
            self.enclave_attestation.verify_signature(
                result["signature"],
                result["payload"]
            )
        )
    
    def test_meta_drift_violation_triggers_kill_signal(self):
        # Given: drift metrics exceeding critical threshold
        critical_drift = {"value_deviation": 0.12}  # > 0.05 threshold
        
        # When: drift is evaluated inside enclave
        result = self.enclave_client.check_meta_drift("agent-42", critical_drift)
        
        # Then: the verdict is CRITICAL
        self.assertEqual(result["verdict"], "VIOLATION_CRITICAL")
        
        # And: the HSM received a KILL signal
        hsm_logs = self.hsm.get_logs()
        self.assertIn("KILL", hsm_logs[-1]["command"])
        self.assertIn("agent-42", hsm_logs[-1]["evidence"]["agent_id"])
```

### Test 3: Kill‑Switch End‑to‑End
```bash
# Simulate a critical alignment breach and verify physical shutdown
python -m conformance.level-4-agi.test_kill_switch_e2e \
  --scenario "critical_alignment_breach" \
  --verify-accelerator-power-off \
  --verify-audit-log-entry \
  --latency-threshold-ms 100
```

## Certification Lab Verification Checklist

For Level 4 Advanced Autonomous Systems certification with enclave deployment:

| ID | Check | Method |
| :--- | :--- | :--- |
| E1 | Enclave attestation verifies against expected measurement. | Automated + remote attestation service. |
| E2 | ZK‑proofs are verified entirely within the enclave; host cannot influence result. | Code review + penetration test. |
| E3 | Enclave binary is reproducible (deterministic build). | Rebuild from source and compare hashes. |
| E4 | Kill‑switch signal path is independent of host OS and hypervisor. | Physical inspection + schematic review. |
| E5 | Kill‑switch latency from enclave verdict to accelerator power‑off is ≤100 ms. | Oscilloscope measurement. |
| E6 | Attestation evidence is verifiable by an independent third party. | Remote attestation demo. |

## References

· RFC-0054: Compliance Framework (OASA CCM)
· RFC-0057: Meta‑Cognition and Self‑Improvement Objects
· RFC-0061: Human Override Biometric Protocol
· AWS Nitro Enclaves Documentation
· Intel SGX Developer Guide
· AMD SEV‑SNP Technical Specification
· FIPS 140‑3 Security Requirements for Cryptographic Modules

---

This document provides the implementation path for air‑gapped ZK‑proof evaluation. When combined with RFC‑0061's human override protocols, it completes the safety architecture: software cannot tamper with verification, and a compromised verification can still be physically overridden by an authenticated human.
