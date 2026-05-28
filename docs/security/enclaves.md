# SovereignStack Hardware Enclaves & Confidential Computing

This guide outlines how to deploy SovereignStack using hardware enclaves for confidential computing. SovereignStack supports both **Intel SGX** (via Gramine) and **AMD SEV-SNP** (via Kata Containers).

## Architecture

Confidential computing ensures that memory pages are encrypted by the CPU hardware, protecting data-in-use from the host operating system, hypervisor, or malicious administrators.

- **Intel SGX (Software Guard Extensions)**: Operates at the application level. We use Gramine as a LibraryOS to run unmodified Linux binaries inside the SGX enclave.
- **AMD SEV-SNP (Secure Encrypted Virtualization)**: Operates at the VM level. We use Kata Containers to launch lightweight micro-VMs where the entire guest OS memory is encrypted.

## Attestation

Before a node can join the Sovereign Mesh, it must prove its hardware identity. The `enclave_attestation` service handles remote attestation, verifying SGX DCAP quotes and SEV-SNP reports, and issuing JWT tokens.

## Deploying on Intel SGX

To run the ingestion service inside SGX:

1. Ensure your hardware supports SGX and the EPC (Enclave Page Cache) size is sufficient.
2. The Helm chart deploys the Intel SGX Device Plugin (`feature.node.kubernetes.io/cpu-cpuid.SGX: "true"`).
3. The `ingest` service is deployed using the `deploy/enclave/gramine-ingest.manifest.template`.

## Deploying on AMD SEV-SNP

To run the vLLM inference engine inside an SEV-SNP VM:

1. Ensure the host kernel supports KVM with SEV-SNP enabled.
2. The Helm chart creates a RuntimeClass `kata-cc`.
3. The `vllm` deployment uses the `kata-cc` runtime and sets appropriate annotations for memory encryption.
4. An init container fetches an attestation quote and validates it with the attestation service before launching vLLM.

## Configuration

In `sovereign-stack.yaml`:

```yaml
node_infrastructure:
  sandboxing:
    confidential_compute:
      enabled: true
      mode: "sev-snp"
      attestation_endpoint: "http://attestation.local:8443"
      enforce_on: ["ingest", "vllm"]
```
