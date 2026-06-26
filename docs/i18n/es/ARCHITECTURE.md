# Arquitectura de SovereignStack

**Revisión:** 1.0 — Mayo 2026  
**Estado:** Documento vivo

---

## 1. Vista general del sistema

SovereignStack es una plataforma de infraestructura de IA soberana en capas. Cada capa tiene límites, APIs y contratos de seguridad bien definidos. Los datos fluyen estrictamente hacia arriba a través de pasarelas autenticadas y reguladas por políticas.

## 2. Subsistemas principales

### 2.1 Runtime Soberano
Capa de ejecución de IA. Responsable de la carga de modelos, inferencia, planificación y aislamiento de recursos.

### 2.2 Capa de Memoria y Coordinación
Almacenamiento persistente, cifrado y distribuido para vectores, cachés KV y sincronización de estado.

### 2.3 Capa de Identidad y Seguridad
Identidad de confianza cero para nodos, cargas de trabajo y usuarios.

### 2.4 Capa de Federación y Malla
Comunicación entre nodos, descubrimiento y sincronización para despliegues multinodo.

## 3. Perfiles de despliegue

| Perfil | Objetivo | Particularidad |
|--------|----------|---------------|
| Edge | Dispositivos ARM, IoT | Inferencia CPU, local, desconectado |
| Aislado | Redes sin conexión externa | GPU + CPU, AES-256 + TPM, sin WAN |
| Centro de datos | Clústeres GPU | Multi-GPU vLLM, BD distribuida |
| Personal | Portátil, homelab | CPU/GPU, FS local, VPN opcional |

---

*Vea la [versión inglesa canónica](/ARCHITECTURE.md) para la referencia.*
