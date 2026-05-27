# RFC 0003: Node Identity Specification

| Field | Value |
|---|---|
| **Status** | Draft |
| **Author** | SovereignStack Core Team |
| **Created** | 2026-05-27 |
| **Category** | Standards Track |

---

## Summary

Define the node identity model for SovereignStack — how every node in the mesh is cryptographically identified, attested, and authorized. Node identity is the root of trust for the entire federation, enabling authenticated peer-to-peer communication, audit attribution, and jurisdictional policy enforcement.

---

## Motivation

Currently, nodes are identified by self-reported hostnames or IP addresses with no cryptographic binding. This creates several problems:

- **Spoofing**: Any node can claim any identity
- **No revocation**: Compromised nodes cannot be reliably excluded
- **No attestation**: No hardware-backed proof of identity (TPM)
- **Audit gaps**: Events cannot be cryptographically attributed to a specific node
- **Jurisdictional ambiguity**: No way to enforce data-residency per node identity

A standard node identity model is required before federation, SPIFFE/SPIRE integration, and compliance certification can proceed.

---

## Design

### Identity Model

Each node has a persistent identity consisting of three layers:

| Layer | Component | Purpose |
|---|---|---|
| **Identity Key** | Ed25519 key pair | Base cryptographic identity |
| **Attestation** | TPM 2.0 AIK (if available) | Hardware-backed proof |
| **Certificate** | X.509 cert signed by mesh CA | Trust chain membership |

### Identity Format

```yaml
node_identity:
  node_id: "eu-fr1-a7f3b2c1"
  public_key: "MCowBQYDK2VwAyEAFx..."
  attestation:
    provider: "tpm2"              # tpm2 | software | nil
    aik_pub: "..."                # TPM Attestation Identity Key (base64)
    cert_sha256: "a1b2c3..."     # Hardware cert hash (if Intel PTT/AMD fTPM)
  certificate:
    subject: "CN=eu-fr1,OU=sovereign-nodes,O=SovereignStack"
    issuer: "CN=SovereignStack Root CA"
    not_after: "2027-05-27T00:00:00Z"
    serial: "00a1b2c3d4e5"
```

### Identity Generation (Initialization)

```bash
# Step 1: Generate Ed25519 identity key
openssl genpkey -algorithm ed25519 -out /etc/sovereign/identity.key
openssl pkey -in /etc/sovereign/identity.key -pubout -out /etc/sovereign/identity.pub

# Step 2: Create CSR
openssl req -new -key /etc/sovereign/identity.key \
  -subj "/CN=$(hostname)/OU=sovereign-nodes/O=SovereignStack" \
  -out /etc/sovereign/node.csr

# Step 3: Submit CSR to mesh CA for signing
# (returns /etc/sovereign/node.crt signed by the root CA)
```

### Trust Chain

```
SovereignStack Root CA (offline root, HSM-protected)
├── Mesh CA (online, signs node certs)
│   ├── Node: eu-fr1
│   ├── Node: eu-de2
│   └── Node: us-ny3
├── Code Signing CA (signs container images)
└── Model Signing CA (signs model weight manifests)
```

### Validation

On connection, each peer validates:

1. **Certificate chain**: X.509 path to Root CA
2. **Key possession**: Proof-of-private-key via TLS or WireGuard handshake
3. **Attestation** (optional): TPM AIK signature over the identity key
4. **Revocation**: Check CRL or OCSP for serial number
5. **Jurisdiction**: Match `subject` OU against allowed jurisdictions

### Node Identity API

```
GET /identity              → Node identity document (signed)
GET /identity/certificate  → X.509 certificate (PEM)
GET /identity/attestation  → TPM attestation report (if available)
```

### Identity in Audit Log

Every audit event includes the node identity:

```json
{
  "event_id": "evt-9102",
  "timestamp": "2026-05-27T09:00:00Z",
  "node_id": "eu-fr1-a7f3b2c1",
  "node_cert_serial": "00a1b2c3d4e5",
  "action": "inference.completion",
  "actor": "user:analyst",
  "signature": "MEUCIQD..."
}
```

---

## Security Considerations

| Threat | Mitigation |
|---|---|
| Private key theft | TPM-wrapped key, HSM for root CA |
| Certificate forgery | Root CA offline, CRL distribution |
| Replay of identity doc | Timestamp + nonce in signed identity document |
| Sybil attack | TPM attestation binds identity to hardware |
| Jurisdiction bypass | Jurisdiction encoded in cert subject, validated by peers |

---

## Compatibility

- **Existing nodes**: Nodes without TPM use `software` attestation mode (same trust model, weaker hardware binding)
- **WireGuard integration**: Node public key = WireGuard public key
- **SPIFFE/SPIRE**: Node identity is SPIFFE-compatible (`spiffe://sovereign.stack/node/eu-fr1`); a future RFC will define full SPIFFE integration

---

## Deployment Strategy

| Phase | Scope |
|---|---|
| Phase 1 | Software key generation, certificate signing via mesh CA script |
| Phase 2 | TPM 2.0 attestation, automatic CSR on first boot |
| Phase 3 | CRL distribution, OCSP responder |
| Phase 4 | Full SPIFFE/SPIRE integration |

---

## Migration Path

Nodes with existing WireGuard key pairs can migrate by:

```bash
# Import existing WireGuard key as identity key
cp /etc/wireguard/private.key /etc/sovereign/identity.key
# Generate CSR from existing key
openssl req -new -key /etc/sovereign/identity.key -out /etc/sovereign/node.csr
# Submit CSR for CA signing
```

---

## Alternatives Considered

| Alternative | Reason Not Selected |
|---|---|
| Self-signed certificates only | No trust chain, no revocation |
| DIY PKI without TPM | Loses hardware-rooted trust |
| Third-party CA (Let's Encrypt) | Requires WAN egress, violates air-gapped profile |
| No node identity | Audit and federation impossible |

---

## References

- [TPM 2.0 Specification](https://trustedcomputinggroup.org/resource/tpm-library-specification/)
- [SPIFFE Standard](https://spiffe.io/)
- [WireGuard Key Management](https://www.wireguard.com/forward-secrecy/)
