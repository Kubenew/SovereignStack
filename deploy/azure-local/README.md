# SovereignStack on Azure Local

Azure Local (formerly Azure Stack HCI) is a premier enterprise deployment target for SovereignStack. This profile provides a governance and intelligence layer that runs on top of Azure Local, keeping AI workloads strictly under organizational control.

## Layer Mapping

| Layer | Azure Local Provider | SovereignStack Provider |
|-------|----------------------|-------------------------|
| **Infrastructure** | Hardware, Hyper-V, Storage Spaces Direct | - |
| **Container Runtime** | Azure Kubernetes Service (AKS) on Azure Arc | `ss-runtime` via daemonsets |
| **Identity** | Microsoft Entra ID (Azure AD), Workload Identity | `ss-identity` (bridges Entra ID to `capability://`) |
| **Policy** | Azure Policy, Gatekeeper / OPA | `ss-policy` (`policy://`, `constitution://`) |
| **Storage** | Azure Blob Storage | `knowledge://`, `memory://`, `checkpoint://` |
| **Telemetry** | Azure Monitor, OpenTelemetry, Log Analytics | `ss-provenance` (`reason://`, `session://`) |
| **Disaster Recovery**| Azure Local Site Recovery | `ss-continuity` (`recovery://`, `playbook://`) |

## Deploying this Profile

This profile uses standard Kustomize to patch the base SovereignStack manifests with Azure Local specifics.

1. Ensure your AKS cluster on Azure Local is connected via Azure Arc.
2. Ensure you have the `az` CLI and `kubectl` configured.
3. Deploy the SovereignStack namespace:
   ```bash
   kubectl apply -k .
   ```

## Key Integrations

### Entra ID Integration
The `ss-identity` component bridges Entra ID groups and roles into SovereignStack `capability://` tokens. See `values-azure-local.yaml` for client ID mapping configuration.

### Storage & Vector Search
This profile configures `ss-memory` to use Azure Blob storage for checkpointing, and defaults to `pgvector` (which can be hosted via Azure Arc enabled PostgreSQL) for active vector memory.

### AI Fabric & GPU Scheduling
SovereignStack's `ss-scheduler` (AFS Protocol) takes precedence for cognitive workloads over the default Kubernetes scheduler, optimizing for GPU locality on the Azure Local cluster nodes.
