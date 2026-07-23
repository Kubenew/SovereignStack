# OpenTelemetry Protocol Mapping

**Version:** 1.0  
**Status:** Draft  
**Related:** [ss-eventbus](../../ss-eventbus/) · [ss-provenance](../../ss-provenance/) · [ss-economy](../../ss-economy/)

---

## Overview

[OpenTelemetry (OTel)](https://opentelemetry.io/) is the vendor-neutral observability framework for traces, metrics, and logs. SovereignStack uses OTel as its primary observability substrate, extending it with domain-specific semantic conventions for financial transaction tracing.

---

## Integration Points

### 1. Traces

| SovereignStack Operation | OTel Span | Attributes |
|---|---|---|
| Payment initiation | `ss.payment.initiate` | `ss.payment.uri`, `ss.payment.amount`, `ss.payment.currency` |
| Settlement execution | `ss.settlement.execute` | `ss.settlement.uri`, `ss.settlement.mechanism` |
| KYC verification | `ss.kyc.verify` | `ss.kyc.entity_uri`, `ss.kyc.status` |
| Risk calculation | `ss.risk.calculate` | `ss.risk.entity_uri`, `ss.risk.category`, `ss.risk.score` |
| Agent reasoning | `ss.agent.reason` | `ss.agent.uri`, `ss.reason.uri` |
| Federation relay | `ss.federation.relay` | `ss.gateway.uri`, `ss.federation.peer` |
| Policy evaluation | `ss.policy.evaluate` | `ss.policy.uri`, `ss.policy.result` |

### 2. Metrics

| Metric Name | Type | Description |
|---|---|---|
| `ss.payments.total` | Counter | Total payments processed |
| `ss.payments.amount` | Histogram | Payment amount distribution |
| `ss.payments.latency_ms` | Histogram | End-to-end payment latency |
| `ss.settlement.total` | Counter | Settlements executed |
| `ss.settlement.netting_ratio` | Gauge | Gross-to-net netting efficiency |
| `ss.risk.var_amount` | Gauge | Current VaR exposure |
| `ss.kyc.checks_total` | Counter | KYC verifications performed |
| `ss.compliance.violations` | Counter | Compliance violations detected |
| `ss.agents.active` | Gauge | Active agent sessions |
| `ss.federation.peers` | Gauge | Connected federation peers |

### 3. Logs

All SovereignStack components emit structured logs in OTel-compatible format:

```json
{
  "timestamp": "2026-07-23T12:00:00Z",
  "severity": "INFO",
  "body": "Payment settled",
  "attributes": {
    "ss.payment.uri": "payment://swift/pacs008-001",
    "ss.payment.status": "Settled",
    "ss.settlement.uri": "settlement://dvp/trade-88421"
  },
  "resource": {
    "service.name": "ss-economy",
    "service.version": "0.1.0",
    "ss.node.uri": "node://eu-prod-01"
  }
}
```

---

## Semantic Conventions

SovereignStack defines a `ss.*` attribute namespace:

| Attribute | Type | Description |
|---|---|---|
| `ss.node.uri` | string | Node URI |
| `ss.agent.uri` | string | Agent URI |
| `ss.twin.uri` | string | Digital twin URI |
| `ss.payment.uri` | string | Payment URI |
| `ss.payment.amount` | int | Amount in smallest unit |
| `ss.payment.currency` | string | ISO 4217 currency |
| `ss.payment.status` | string | Payment status |
| `ss.settlement.uri` | string | Settlement URI |
| `ss.settlement.mechanism` | string | DvP, FoP, PvP, Netting |
| `ss.risk.category` | string | Risk category |
| `ss.risk.score` | double | Risk score (0.0–1.0) |
| `ss.compliance.framework` | string | Regulatory framework |
| `ss.compliance.result` | string | Compliant / NonCompliant |

---

## Financial Transaction Tracing

For financial workflows, OTel traces span the entire lifecycle:

```
                     Cross-Border Payment Trace
┌─────────────────────────────────────────────────────────┐
│ ss.payment.initiate (root span)                          │
│  ├── ss.kyc.verify                                       │
│  ├── ss.compliance.check (PSD2)                          │
│  ├── ss.policy.evaluate (transaction limits)             │
│  ├── ss.treasury.debit                                   │
│  ├── ss.federation.relay (cross-border)                  │
│  ├── ss.treasury.credit                                  │
│  ├── ss.settlement.execute                               │
│  ├── ss.accounting.post (journal entry)                  │
│  └── ss.tax.calculate (withholding tax)                  │
└─────────────────────────────────────────────────────────┘
```

---

## Collector Configuration

```yaml
# OTel Collector config for SovereignStack
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"

processors:
  batch:
    timeout: 5s

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  jaeger:
    endpoint: "jaeger:14250"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

---

## Implementation Notes

1. **Provenance linking**: OTel trace IDs are stored alongside provenance entries for correlation.
2. **Audit bridge**: Financial transaction traces are automatically linked to the Merkle audit log.
3. **Alerting**: Prometheus alerting rules (21 alerts from 2027.1) extended with financial metrics.
