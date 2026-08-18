# OASA Foundation Charter
**Version:** 1.0 (Constitutional Draft)
**Status:** Core Governing Document
**Target Incorporation:** Geneva, Switzerland (Swiss Verein / Association)

## PREAMBLE: THE CONSTITUTIONAL PRINCIPLE
The Open Architecture Specification for Autonomous Systems (OASA) Foundation exists to enforce mathematical accountability within high-autonomy environments. As human systems transition from human-directed operation to algorithmic execution, the preservation of accountability requires an unalterable, non-repudiable infrastructure layer.

The Foundation does not build products; it maintains the protocol that makes the execution of unaccountable autonomy impossible. It is governed by a strict Mission Lock: every system action must flow down a deterministic pipeline:

`Identity → Capability → Policy → Action → Provenance → Evidence`

## ARTICLE I: LEGAL STRUCTURE, INTELLECTUAL PROPERTY, AND MISSION LOCK

### Section 1.01: Legal Form and Purpose
The Foundation shall be incorporated under Articles 60–79 of the Swiss Civil Code as a non-profit Swiss Association (Verein), headquartered in Geneva, Switzerland. The Foundation is permanently barred from engaging in commercial operations, software distribution monetization, or professional consulting services.

### Section 1.10: Intellectual Property Assignment
All software repositories, technical specifications, Request for Comments (RFCs), Uniform Resource Identifier (URI) schemes, and cryptographic verification blueprints bearing the name SovereignStack or OASA are hereby irrevocably assigned to the OASA Foundation.
- **Permissive Licensing**: All codebase assets must be distributed exclusively under the Apache License, Version 2.0.
- **Specification Licensing**: All written architectural specifications must be licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0) license.
- **Patent Non-Assertion**: The Foundation shall maintain a permanent patent non-assertion pledge. No member of the Foundation may assert patents against implementations conforming to the OASA specification.

### Section 1.20: Constitutional Mission Lock
The core architectural loop defined in the Preamble constitutes the Constitutional Mission of the Foundation.
- **The Non-Negotiable Halt State**: The right of a node running `ss-node-os` to drop execution to a definitive Halt State (Exit Code 2) upon cryptographic or capability verification failure is an absolute safety property.
- **Prohibition of Soft-Compliance**: No technical amendment, plug-in, or sub-routine may introduce a mechanism that bypasses, suppresses, or downgrades an active validation failure to a passive warning.

## ARTICLE II: BOARD COMPOSITION AND THE FOUR-QUADRANT GOVERNANCE MODEL

To prevent hostile takeover, vendor capture, or dilution by financial cartels, voting power is structurally locked into four distinct Stakeholder-Class Quadrants. Financial sponsorship carries zero voting weight.

```text
┌─────────────────────────────────────────┐
│          OASA General Assembly          │
│   (12 Total Seats - Rotating 3-Year)    │
└────────────────────┬────────────────────┘
                     │
 ┌─────────────────────────────┼─────────────────────────────┐
 ▼                             ▼                             ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ 1. Tech Maintain │  │ 2. Academic Core │  │ 3. Contester/Ins │
│    (3 Seats)     │  │    (3 Seats)     │  │    (3 Seats)     │
│ Vote: Committers │  │ Vote: Labs/Univ  │  │  Vote: Auditors  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

> [!NOTE]
> The 4th Quadrant, Enterprise Operators (3 seats), acts as an advisory and consumer layer but is barred from holding structural voting blocks on standard specification strictness.

### Section 2.10: Seat Allocation and Electorates
The Governing Board shall consist of twelve (12) voting seats, distributed equally across three core voting blocks, with a fourth non-voting advisory block:
1. **The Technical Maintainer Quadrant (3 Seats)**: Elected exclusively by active open-source code contributors who have maintained an active commit profile over the preceding twelve (12) calendar months.
2. **The Academic & Research Quadrant (3 Seats)**: Elected by accredited global university laboratories, institutes, and research bodies hosting dedicated "Accountable Autonomy" testbeds.
3. **The Contester & Auditor Quadrant (3 Seats)**: Elected by verified independent security auditing firms, cyber-insurance underwriting institutions, and civil society legal defense funds.
4. **The Enterprise Operator Quadrant (3 Seats - Non-Voting Advisory Status)**: Composed of representatives from corporations deploying OASA-conformant clusters in production environments.

### Section 2.20: Anti-Capture Safeguards
- **The Single-Affiliation Rule**: No single corporate entity, subsidiary, state enterprise, or group of companies sharing ultimate beneficial ownership may hold more than one (1) voting seat across the entire Board concurrently.
- **Separation of Affiliation**: If a Technical Maintainer gains employment at an enterprise represented in the Operator quadrant, their seat is automatically vacated and a special election is triggered.

## ARTICLE III: VOTING ASYMMETRY AND SPECIFICATION PROTECTION

### Section 3.10: Jurisdictional and Geographic Quotas
Board seats must be strictly bound to the geographic locus of the underlying operational work, not the personal residency or nationality of the individual holding the seat.

**Calculation Metric**: Geographic contribution metrics are determined programmatically:
- **Code Commits**: Geographic origin is the IP address of the commit signing event, with a fallback to the declared primary work location of the contributor if the signing IP is anonymized.
- **Academic Work**: Geographic origin is the physical address of the laboratory facility where the research was conducted.
- **Contester Work**: Geographic origin is the jurisdiction where the audit verification was legally filed.

**The 25% Structural Cap**: No single geographic region (North America, European Union, Asia-Pacific, or Rest of World) may command more than 25% of the total voting power at any General Assembly vote.

### Section 3.20: Asymmetric Veto Operations
Standard operational procedures require a simple majority (>50%). However, any resolution that proposes to amend conformance parameters, lower verification thresholds, or alter the `ss-test --verify` matrix requires a Double Protection Loop:
1. **Supermajority Mandate**: Must achieve a Three-Fourths (75%) Supermajority of the total Board.
2. **The Contester Class Veto**: Regardless of the macro vote score, if all three (3) members of the Contester & Auditor Quadrant vote collectively to reject an amendment that reduces verification strictness, the resolution is permanently defeated.

> [!IMPORTANT]
> **Quorum Floor for Contesters**: At least 2 of 3 Contester seats must be filled for any vote on verification strictness to proceed. If vacant, votes are suspended. If vacant for >90 days, the remaining Contester may appoint temporary representatives. If all are vacant, the Academic Quadrant assumes temporary veto power.

## ARTICLE IV: CRYPTOGRAPHIC KEY MANAGEMENT AND RELEASE SIGNING CEREMONIES

### Section 4.10: The 5-of-9 Distributed Release Key Topology
The master cryptographic private key used to sign official releases of the `ss-node-os` base image and publish the `oasa-manifest.sig` file is split into nine (9) distinct cryptographic shards utilizing an un-backed, threshold-based multi-signature scheme.

- **Key Shard Allocation**: Shards are distributed exclusively to independent academic institutions and core technical maintainers across distinct legal jurisdictions.
- **Sign-off Condition**: To sign an official reference release, five (5) of the nine (9) independent key holders must cryptographically sign the release manifest.

### Section 4.20: Mandatory Key Rotation Protocol
- **The 24-Month Key Ceremony**: Every twenty-four (24) months, the multi-signature key topology must be completely regenerated during a publicly streamable, cryptographically recorded key generation ceremony.
- **Air-Gapped Generation**: Keys must be generated on single-use, bare-metal hardware endpoints lacking network interface controllers (NICs).

### Section 4.30: Emergency Key Compromise Procedure
If an active cryptographic key holder reports a compromised storage device or physical duress:
1. An emergency session of the Board is automatically triggered via an encrypted messaging fallback layer.
2. Upon verification of compromise, a supermajority vote authorizes the execution of a pre-compiled Key Revocation Transaction to old nodes.
3. The remaining clean shards compile an emergency recovery manifest using backup shards held in cold isolation by independent Swiss fiduciary trustees.

## ARTICLE V: UNAMENDABLE CORE PROVISIONS AND DISSOLUTION

### Section 5.10: Unamendable Core
Sections 1.01 (Purpose), 1.20 (Mission Lock), 2.20 (Anti-Capture), 3.20 (Asymmetric Veto), and 4.10 (Distributed Release Key Topology) are explicitly defined as Immutable Clauses. They cannot be modified, deleted, suspended, or overridden by any vote, assembly, or emergency decree.

### Section 5.20: Perpetual Anti-Commercialization Dissolution Trigger
If the Foundation faces bankruptcy, legal attack, or hostile jurisdictional expropriation, the Board shall invoke a structured Dissolution Procedure:
1. All core IP, codebases, and cryptographic verification suites are mirrored globally across decentralized peer networks and released unconditionally into the public domain under a **CC0 license**.
2. Remaining financial cash reserves are transferred automatically to a recognized open-source software foundation or a Swiss academic trust dedicated to open infrastructure research.
