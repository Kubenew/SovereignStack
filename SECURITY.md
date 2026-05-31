# Security Policy & Threat Model

## Reporting Vulnerabilities

Contact: security@sovereignstack.ai
PGP Key: Available at keys.sovereignstack.ai

## Supported Subsystems

| Subsystem | Supported |
|---|---|
| ss-core | ✓ |
| ss-identity | ✓ |
| ss-sessiond | ✓ |
| ss-bus | ✓ |
| ss-cas | ✓ |
| ss-federation | ✓ |
| ss-trust | ✓ |
| ss-kas | ✓ |
| ss-reason | ✓ |
| ss-lineage | ✓ |
| ss-capability | ✓ |
| ss-swarm | ✓ |
| ss-scheduler | ✓ |

## Threat Model

1. Agent Impersonation — Mitigated by cryptographic identity
2. Capability Escalation — Mitigated by strict capability boundaries
3. Data Tampering — Mitigated by Merkle provenance chains
4. Sybil Attacks — Mitigated by reputation + stake mechanisms
5. Eclipse Attacks — Mitigated by diverse peer discovery
6. Supply Chain — Mitigated by signed releases and reproducible builds
7. Replay Attacks — Mitigated by nonce/timestamp checks
8. Side Channel — Mitigated by constant-time crypto primitives

## Secure Development Lifecycle

- All code reviewed
- All commits signed
- Dependencies scanned automatically
- Fuzzing on critical parsers
- Regular third-party audits
- Bug bounty program

## Incident Response

1. Triage (within 1 hour)
2. Containment
3. Root Cause Analysis
4. Patch & Release
5. Post-Mortem (published publicly)
