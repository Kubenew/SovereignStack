# SovereignStack-arkitektur

**Revision:** 1.0 — Maj 2026  
**Status:** Levande dokument

---

## 1. Systemöversikt

SovereignStack är en skiktad suverän AI-infrastrukturplattform. Varje skikt har väldefinierade gränser, API:er och säkerhetskontrakt. Data flödar strikt uppåt genom autentiserade och policy-styrda gateways.

## 2. Kärnsystem

### 2.1 Suverän körning
AI-exekveringsskikt. Ansvarar för modellinläsning, inferens, schemaläggning och resursisolering.

### 2.2 Minne och koordineringsskikt
Beständig, krypterad, distribuerad lagring för vektorer, KV-cachar och tillståndssynkronisering.

### 2.3 Identitets- och säkerhetsskikt
Noll-förtroende-identitet för noder, arbetsbelastningar och användare.

### 2.4 Federations- och mesh-skikt
Mellan-nod-kommunikation, upptäckt och synkronisering för multi-nod-distributioner.

## 3. Distributionsprofiler

| Profil | Mål | Egenskap |
|--------|-----|----------|
| Edge | ARM-enheter, IoT | CPU-inferens, lokalt, offline |
| Air-Gapped | Isolerade nätverk | GPU + CPU, AES-256 + TPM, inget WAN |
| Datacenter | GPU-kluster | Multi-GPU vLLM, distribuerad DB |
| Personlig | Laptop, hemmalabb | CPU/GPU, lokalt FS, valfritt VPN |

---

*Se den [engelska kanoniska versionen](/ARCHITECTURE.md) för referens.*
