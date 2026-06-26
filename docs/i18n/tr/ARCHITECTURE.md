# SovereignStack Mimarisi

**Revizyon:** 1.0 — Mayıs 2026  
**Durum:** Canlı belge

---

## 1. Sistem Genel Bakış

SovereignStack, katmanlı bir egemen AI altyapı platformudur. Her katmanın iyi tanımlanmış sınırları, API'leri ve güvenlik sözleşmeleri vardır. Veriler, kimliği doğrulanmış ve politikalarla yönetilen ağ geçitleri aracılığıyla kesinlikle yukarı doğru akar.

## 2. Temel Alt Sistemler

### 2.1 Egemen Çalışma Zamanı
AI yürütme katmanı. Model yükleme, çıkarım, zamanlama ve kaynak yalıtımından sorumludur.

### 2.2 Bellek ve Koordinasyon Katmanı
Vektörler, KV önbellekleri ve durum senkronizasyonu için kalıcı, şifrelenmiş, dağıtık depolama.

### 2.3 Kimlik ve Güvenlik Katmanı
Düğümler, iş yükleri ve kullanıcılar için sıfır güven kimliği.

### 2.4 Federasyon ve Mesh Katmanı
Çok düğümlü dağıtımlar için düğümler arası iletişim, keşif ve senkronizasyon.

## 3. Dağıtım Profilleri

| Profil | Hedef | Özellik |
|--------|-------|---------|
| Edge | ARM cihazlar, IoT | CPU çıkarımı, yerel, çevrimdışı |
| Air-Gapped | İzole ağlar | GPU + CPU, AES-256 + TPM, WAN yok |
| Veri Merkezi | GPU kümeleri | Çoklu GPU vLLM, dağıtık veritabanı |
| Kişisel | Dizüstü bilgisayar, ev laboratuvarı | CPU/GPU, yerel FS, isteğe bağlı VPN |

---

*Referans için [İngilizce kanonik sürüme](/ARCHITECTURE.md) bakın.*
