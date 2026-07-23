# Protocol Mappings

This directory contains integration guides mapping SovereignStack primitives to established industry standards and protocols.

Each mapping document explains how SovereignStack URI schemes, object models, and APIs correspond to specific external standards, enabling interoperability with existing enterprise infrastructure.

## Available Mappings

| Standard | Document | SovereignStack Integration |
|----------|----------|---------------------------|
| [ISO 20022](iso-20022.md) | Financial messaging | `ss-economy/payments`, `ss-economy/settlement` |
| [OpenID Connect](openid-connect.md) | Identity & authentication | `ss-identity`, `ss-economy/fin_identity` |
| [SPIFFE/SPIRE](spiffe-spire.md) | Workload identity | `ss-identity`, `ss-kernel`, `ss-federation` |
| [OpenTelemetry](opentelemetry.md) | Observability & tracing | `ss-eventbus`, `ss-provenance`, financial tx tracing |

## How to Use

These mappings serve as:
1. **Implementation guides** for teams integrating SovereignStack into existing infrastructure
2. **Compliance evidence** demonstrating standards alignment
3. **Interoperability blueprints** for connecting SovereignStack nodes to legacy systems
