# Arquitetura SovereignStack

**Revisão:** 1.0 — Maio 2026  
**Status:** Documento vivo

---

## 1. Visão geral do sistema

SovereignStack é uma plataforma de infraestrutura de IA soberana em camadas. Cada camada possui limites, APIs e contratos de segurança bem definidos. Os dados fluem estritamente para cima através de gateways autenticados e regulados por políticas.

## 2. Subsistemas principais

### 2.1 Runtime Soberano
Camada de execução de IA. Responsável pelo carregamento de modelos, inferência, agendamento e isolamento de recursos.

### 2.2 Camada de Memória e Coordenação
Armazenamento persistente, criptografado e distribuído para vetores, caches KV e sincronização de estado.

### 2.3 Camada de Identidade e Segurança
Identidade de confiança zero para nós, cargas de trabalho e usuários.

### 2.4 Camada de Federação e Malha
Comunicação entre nós, descoberta e sincronização para implantações multinó.

## 3. Perfis de implantação

| Perfil | Alvo | Particularidade |
|--------|------|---------------|
| Edge | Dispositivos ARM, IoT | Inferência CPU, local, desconectado |
| Isolado | Redes sem conexão externa | GPU + CPU, AES-256 + TPM, sem WAN |
| Datacenter | Clusters GPU | Multi-GPU vLLM, BD distribuída |
| Pessoal | Notebook, homelab | CPU/GPU, FS local, VPN opcional |

---

*Consulte a [versão canônica em inglês](/ARCHITECTURE.md) para referência.*
