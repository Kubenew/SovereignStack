# SovereignStack Proje Anayasası

**Sürüm:** 1.0 — Haziran 2026  
**Durum:** Onaylanmış  
**Kanonik dil:** İngilizce

> Egemen zeka, tek bir dile, yargı yetkisine, bulut sağlayıcısına veya uygulamaya bağımlı olmamalıdır.

---

## Giriş

Biz, SovereignStack katkıcıları, Egemen Zeka Ağı'nın gelişimini, yönetişimini ve evrimini düzenlemek için bu Anayasa'yı oluşturuyoruz. Bu belge, projenin en üst düzey yönetim belgesidir. Tüm RFC'ler, standartlar ve proje politikaları yetkilerini bu Anayasa'dan alır.

SovereignStack, yapay ve insan zekasının egemen sınırlar ötesinde özgürce çalışabildiği, hiçbir katılımcının özerkliğini, gizliliğini veya güvenliğini tehlikeye atmadığı bir dünyayı gerçekleştirmek için vardır.

---

## Bölüm I — Temel İlkeler

### §1.1 Egemenlik
Egemen Zeka Ağı'ndaki her katılımcı, kendi verileri, modelleri, hesaplama kaynakları ve kararları üzerinde tam egemenliğe sahiptir. Hiçbir katılımcı, bir başkasını egemen iradesi dışında hareket etmeye zorlayamaz.

### §1.2 Birlikte Çalışabilirlik
Tüm protokoller ve standartlar, uygulamalar, yargı bölgeleri ve donanım platformları arasında maksimum birlikte çalışabilirlik için tasarlanmalıdır.

### §1.3 Doğrulanabilirlik
Ağdaki her işlem kriptografik olarak doğrulanabilir olmalıdır. Güven varsayılmaz — imzalar, Merkle denetimleri ve kaynak grafikleriyle kanıtlanır.

### §1.4 Taşınabilirlik
Ajanlar, oturumlar, yetenekler ve zeka varlıkları, satıcı kilidi olmadan düğümler, bulutlar ve yargı bölgeleri arasında taşınabilir olmalıdır.

### §1.5 Şeffaflık
SovereignStack'in yönetişimi, kodu, standartları ve karar alma süreçleri açık, şeffaf ve tüm katılımcılar için erişilebilir kalmalıdır.

---

## Bölüm II — Yönetişim Yapısı

### §2.1 Teknik Yönlendirme Komitesi (TSC)
TSC, projenin en yüksek yönetim organıdır. Aşağıdakilerden sorumludur:

- Bu Anayasa'ya yapılan değişiklikleri onaylamak
- RFC'leri onaylamak veya reddetmek
- Çekirdek Bakıcıları atamak ve görevden almak
- Anlaşmazlıkları çözmek
- Stratejik yol haritasını tanımlamak

**Kompozisyon:** 5–9 üye, kademeli 12 aylık dönemlerle.

---

## Bölüm III — Standart Süreci

### §3.1 RFC Yaşam Döngüsü
```
Taslak → Tartışma → Kabul Edildi → Uygulandı → Kararlı → Kullanımdan Kaldırıldı
```

### §3.2 Onay
Bir RFC şu durumda onaylanır:
1. En az 14 günlük inceleme süresi geçmişse
2. TSC çoğunlukla lehte oy kullanmışsa
3. Ele alınmamış güvenlik endişesi yoksa

---

## Bölüm IV — Katılımcı Hakları

### §4.1 Fork Hakkı
Her katılımcı, lisans uyarınca projeyi istediği zaman fork edebilir.

### §4.2 Denetim Hakkı
Tüm katılımcılar, referans uygulamanın tam denetim izini inceleme hakkına sahiptir.

### §4.3 Çıkış Hakkı
Katılımcılar ağdan istedikleri zaman ayrılabilir ve verilerinin, modellerinin ve oturumlarının tam mülkiyetini korur.

### §4.4 Katılım Hakkı
Tüm katılımcılar, ayrımcılığa uğramadan katkıda bulunma, RFC önerme ve yönetişim tartışmalarına katılma hakkına sahiptir.

---

## Bölüm V — Uyumluluk ve Sertifikasyon

### §5.1 OASA Çerçevesi
| Seviye | Ad | Gereksinimler |
|--------|-----|--------------|
| L1 | Sovereign-Ready | Temel nesne modeli, URI standardı ve denetim ile uyumluluk |
| L2 | Secure-Runtime | L1 + durağan şifreleme, politika uygulama, kimlik doğrulama |
| L3 | Strict-Sovereign | L2 + donanım onayı, çevrimdışı yetenek, harici bağımlılık yok |

---

## Bölüm VI — Değişiklik Süreci

Değişiklikler 30 günlük kamu yorumu süresi ve TSC'nin 2/3 çoğunluğunu gerektirir.

---

## Bölüm VII — Fesih

Projenin feshi durumunda, tüm varlıklar projenin açık kaynak lisansı altında kullanılabilir durumda kalır.

---

*Bu Anayasa, SovereignStack katkıcılarının mutabakatı ile onaylanmıştır.*

**Ek A:** [GOVERNANCE.md](/GOVERNANCE.md) — Ayrıntılı yönetişim prosedürleri  
**Ek B:** [CONTRIBUTING.md](/CONTRIBUTING.md) — Katkıda bulunma yönergeleri  
**Ek C:** [CODE_OF_CONDUCT.md](/CODE_OF_CONDUCT.md) — Davranış kuralları
