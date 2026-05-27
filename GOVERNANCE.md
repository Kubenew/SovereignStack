# SovereignStack Governance

**Version:** 1.0 — May 2026

---

## 1. Project Structure

SovereignStack is organized as a layered governance model with clear roles, responsibilities, and decision-making processes.

```
           ┌─────────────────────────────────────┐
           │          CORE MAINTAINERS            │
           │  Strategic direction, releases,      │
           │  standards approval, architecture    │
           └──────────┬──────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
  ┌──────▼─────┐ ┌───▼────┐ ┌───▼──────┐
  │ SUBSYSTEM  │ │ WORKING│ │ RFC      │
  │ MAINTAINERS│ │ GROUPS │ │ REVIEWERS│
  │ Runtime    │ │ Runtime│ │ Spec     │
  │ Memory     │ │ Memory │ │ Security │
  │ Federation │ │ Fed.   │ │ Protocol │
  │ Security   │ │ Sec.   │ │          │
  └────────────┘ └────────┘ └──────────┘
```

---

## 2. Roles & Responsibilities

### 2.1 Core Maintainers

The Core Maintainers are responsible for the overall direction and health of the project.

**Responsibilities:**
- Define strategic roadmap
- Approve or reject RFCs
- Manage release process
- Resolve escalated disputes
- Maintain project standards

**Current Core Maintainers:**
- _TBD — See [MAINTAINERS.md](MAINTAINERS.md)_

**Becoming a Core Maintainer:**
- Demonstrated sustained contribution over 6+ months
- Deep understanding of multiple subsystems
- Approval from existing Core Maintainers

### 2.2 Subsystem Maintainers

Each major subsystem (Runtime, Memory, Federation, Security) has designated maintainers.

**Responsibilities:**
- Own subsystem code and documentation
- Review and merge subsystem PRs
- Participate in RFC reviews for their subsystem
- Coordinate with dependent subsystems

**Becoming a Subsystem Maintainer:**
- Consistent contributions to the subsystem (3+ months)
- Design and implementation track record
- Nomination by Core Maintainers

### 2.3 Working Groups

Working Groups (WGs) are temporary or permanent groups focused on specific areas.

**Active Working Groups:**

| WG | Focus | Status |
|---|---|---|
| Runtime WG | Inference engine, model routing, scheduling | Active |
| Memory WG | Vector store, KV cache, sync protocols | Active |
| Federation WG | Mesh networking, cross-node sync, discovery | Proposed |
| Security WG | Threat model, audit, supply chain | Active |
| Deployment WG | Profiles, installers, reference architectures | Active |

### 2.4 RFC Reviewers

RFC Reviewers are trusted community members with expertise in specific domains.

**Responsibilities:**
- Review RFCs for technical soundness
- Evaluate security and compatibility implications
- Provide structured feedback

---

## 3. Decision-Making Process

### 3.1 Lazy Consensus

The project defaults to **lazy consensus**. If no objections are raised within the review period, a proposal is considered accepted.

### 3.2 Explicit Approval

For significant decisions (new RFCs, breaking changes, new maintainers), explicit approval is required:

1. **Proposal** — Issue or RFC filed
2. **Discussion** — Minimum 7-day review period
3. **Approval** — Majority of Core Maintainers
4. **Implementation** — Merged after approval

### 3.3 Escalation

If consensus cannot be reached, the Core Maintainers make a final decision.

---

## 4. RFC Process

All significant changes follow the RFC process defined in [RFC 0000](rfcs/0000-rfc-process.md).

**RFC Lifecycle:**

```
Draft → Discussion → Accepted → Implemented → Stable → Deprecated
```

**Required for:**
- New subsystems or components
- API or protocol changes
- Security model changes
- Breaking configuration changes

---

## 5. Release Model

### 5.1 Versioning

The project uses **calendar versioning** (`YYYY.N`):
- `2026.1` — First release of 2026
- `2026.2` — Second release of 2026

### 5.2 Release Channels

| Channel | Quality | Frequency | Audience |
|---|---|---|---|
| **Stable** | Production-ready | Quarterly | Enterprise users |
| **Beta** | Feature-complete | Monthly | Early adopters |
| **Experimental** | Rapid iteration | Weekly | Developers |

### 5.3 Release Process

1. Feature freeze (2 weeks before release)
2. Testing and validation
3. Release candidate (1 week)
4. Final release
5. Post-release patch cycle (as needed)

---

## 6. Contribution Standards

All contributions must include:

- **Tests** — Unit and/or conformance
- **Documentation** — User-facing and developer-facing
- **Security Considerations** — Threat model impact
- **Backward Compatibility** — Migration path if breaking

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 7. Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 8. Licensing

All contributions are licensed under [Apache License 2.0](LICENSE).
