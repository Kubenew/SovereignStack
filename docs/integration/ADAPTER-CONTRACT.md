# SovereignStack Adapter Contract

This document defines the architectural boundary between an external infrastructure platform (such as HPE Morpheus) and the SovereignStack Core Contract.

## The Evidence Boundary

SovereignStack must strictly distinguish between **platform assertions** and **cryptographic proof**.

- **What the Platform Asserts:** Infrastructure facts (e.g., "VM created", "network attached", "storage provisioned").
- **What SovereignStack Proves:** Cryptographically verifiable governance evidence (e.g., "WHO requested it", "WHICH capability authorized it", "WHICH policy allowed it", "WHETHER the evidence was modified").

The platform API is the source of infrastructure facts. SovereignStack is the source of cryptographically verifiable governance evidence.

## The Central Rule

> A platform adapter translates platform-specific state and events into SovereignStack Core Contract objects. It **MUST NOT** redefine identity, authorization, provenance, evidence, or verification semantics.

## Responsibilities

| Adapter responsibility | Core responsibility |
|---|---|
| Discover VM | Identity |
| Map VM metadata | Object model |
| Translate operation | Policy |
| Collect platform event | Provenance |
| Supply platform evidence | Evidence |
| Report platform result | Verification |
| Handle API authentication | Security boundary |

By maintaining this separation, the adapter remains thin and replaceable, protecting SovereignStack's vendor neutrality.
