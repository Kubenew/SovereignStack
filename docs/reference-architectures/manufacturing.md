# Reference Architecture: Manufacturing

**Version:** 1.0  
**Status:** Draft  
**Profile:** [Sovereign Manufacturing Profile](../../profiles/manufacturing/profile.yaml)

---

## Overview

This reference architecture describes how SovereignStack deploys in manufacturing, covering digital twin factories, predictive maintenance, supply chain traceability, and quality management.

---

## Architecture Diagram

```mermaid
graph TB
    subgraph "Shop Floor"
        PLC[PLCs / SCADA]
        SEN[IoT Sensors]
        ROB[Robot Arms]
    end

    subgraph "SovereignStack — Factory Node"
        GW["gateway://factory-edge"]
        
        subgraph "Agent Layer"
            SCO["agent://supply-chain-optimizer"]
            QI["agent://quality-inspector"]
            MS["agent://maintenance-scheduler"]
            PP["agent://production-planner"]
        end
        
        subgraph "Bridging Layer"
            TW["ss-twin (RealityInterface)"]
            DEV["ss-device"]
        end
        
        subgraph "Economy Layer"
            AST[assets]
            ACC[accounting]
        end
        
        subgraph "Digital Twins"
            FAC["factory://munich-plant-7"]
            MCH["machine://press-line-01"]
            VEH["vehicle://agv-fleet"]
            PRD["product://widget-a"]
        end
    end

    subgraph "Supply Chain Federation"
        SUP["gateway://supplier-mesh"]
        S1["company://supplier-a"]
        S2["company://supplier-b"]
    end

    subgraph "HQ"
        HQ["gateway://hq-cloud"]
        ERP[ERP System]
    end

    PLC --> TW
    SEN --> TW
    ROB --> TW
    TW --> MCH
    TW --> FAC
    GW --> SCO
    GW --> QI
    GW --> MS
    GW --> PP
    SCO --> SUP
    SUP --> S1
    SUP --> S2
    GW --> HQ
    HQ --> ERP
```

---

## Component Mapping

| Manufacturing Domain | SovereignStack Component | URI Scheme |
|---|---|---|
| Machine telemetry | `ss-twin` (RealityInterface) | `robot://`, `machine://` |
| Factory digital twin | Digital twin framework | `factory://` |
| Product tracking | `ss-provenance` + `ss-cas` | `product://`, `lot://` |
| Quality inspection | `agent://quality-inspector` | `inspection://` records |
| Predictive maintenance | `agent://maintenance-scheduler` | Event patterns on `machine://` |
| Supply chain | `ss-federation` | `company://` twins via `gateway://` |
| Inventory accounting | `ss-economy/accounting` | `account://` |
| Asset management | `ss-economy/assets` | `asset://` |
| Fleet management | `ss-twin` + `ss-swarm` | `vehicle://` |

---

## Edge Deployment

Manufacturing requires edge-first deployment:

```
Factory Floor (Edge Node)
  ├── ss-twin: Real-time sensor polling (5s intervals)
  ├── ss-eventbus: Local event processing
  ├── ss-kernel: Offline-capable identity + policy
  └── Selective federation → HQ cloud node
```

---

## Key Workflows

1. **Predictive maintenance**: `machine://` twin detects anomaly → `agent://maintenance-scheduler` plans intervention
2. **Supply chain traceability**: Full `lineage://` chain from `product://` back through `lot://` to `company://supplier-*`
3. **Quality gate**: `agent://quality-inspector` signs `inspection://` record → attached to `product://` provenance
4. **Production planning**: `agent://production-planner` optimizes line scheduling based on `factory://` twin state

---

## Compliance

| Framework | Coverage |
|---|---|
| ISO 9001 | Quality management via signed inspection records |
| Supply Chain Act | Full traceability via provenance graph |
| ISO 27001 | Information security via OASA controls |
| Industry 4.0 / RAMI 4.0 | Digital twin alignment with administration shell |
