# E-Menum Persona & User Flows

> **Auto-Claude Persona Document**  
> RBAC rolleri persona olarak, sektör personaları, kullanıcı akışları, UI/UX yaklaşımları.  
> Son Güncelleme: 2026-01-31

---

## 1. PERSONA FELSEFESİ

### 1.1 Persona Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERSONA-DRIVEN DESIGN                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRENSİP:                                                                   │
│  Her RBAC rolü bir persona'dır.                                            │
│  Her persona'nın farklı ihtiyaçları, beklentileri ve zorlukları vardır.   │
│  UI/UX bu farklılıklara göre şekillenir.                                   │
│                                                                             │
│  PERSONA KATMANLARI:                                                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  KATMAN 1: ROL PERSONA                                               │ │
│  │  Sistemdeki rolü nedir? (owner, manager, staff, customer...)         │ │
│  │                                                                       │ │
│  │  KATMAN 2: SEKTÖR PERSONA                                            │ │
│  │  Hangi tür işletme? (fine dining, fast food, cafe...)                │ │
│  │                                                                       │ │
│  │  KATMAN 3: DEMOGRAFİK PERSONA                                        │ │
│  │  Kim? (yaş, teknoloji yetkinliği, erişilebilirlik ihtiyacı...)      │ │
│  │                                                                       │ │
│  │  KATMAN 4: BAĞLAM PERSONA                                            │ │
│  │  Ne zaman, nerede? (yoğun servis, mobil, gürültülü ortam...)        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Her UI kararında bu 4 katmanı düşün.                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. PLATFORM ROL PERSONALARI

### 2.1 Super Admin Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUPER ADMIN PERSONA                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── E-Menum çekirdek ekip üyesi                                           │
│  ├── Teknik veya operasyon yöneticisi                                      │
│  ├── Sistem genelinde yetkili                                              │
│  └── Az sayıda (1-3 kişi)                                                  │
│                                                                             │
│  TEKNOLOJİ YETKİNLİĞİ: Yüksek                                              │
│  KULLANIM SIKLIĞI: Günlük (iş saatleri)                                    │
│  CİHAZ: Desktop ağırlıklı                                                  │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Organizasyon yönetimi (oluşturma, düzenleme, silme)                  │
│  ├── Plan ve fiyatlandırma yönetimi                                        │
│  ├── Feature flag yönetimi                                                 │
│  ├── Kullanıcı impersonation (destek amaçlı)                              │
│  ├── Sistem ayarları                                                       │
│  ├── Audit log inceleme                                                    │
│  └── Kritik operasyonlar                                                   │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Bilgi yoğunluğu: YÜKSEK (tek bakışta çok veri)                 │ │
│  │  ├── Data table ağırlıklı                                           │ │
│  │  ├── Filtreleme ve arama güçlü                                      │ │
│  │  ├── Batch işlemler desteklenir                                     │ │
│  │  ├── Keyboard shortcuts (power user)                                │ │
│  │  └── Command palette (Ctrl+K) erişimi                               │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Compact spacing tercih                                         │ │
│  │  ├── Monospace font data için                                       │ │
│  │  ├── Renk: Güç ve kontrol hissi (koyu tonlar)                      │ │
│  │  └── Status badge'ler belirgin                                      │ │
│  │                                                                       │ │
│  │  GÜVENLİK:                                                           │ │
│  │  ├── Tehlikeli işlemler için çift onay                              │ │
│  │  ├── Impersonation banner belirgin                                  │ │
│  │  └── Audit trail her yerde görünür                                  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Admin Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ADMIN PERSONA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── E-Menum operasyon ekibi                                               │
│  ├── Müşteri hesap yöneticisi                                              │
│  ├── Teknik destek seviye 2                                                │
│  └── Orta sayıda (3-10 kişi)                                               │
│                                                                             │
│  TEKNOLOJİ YETKİNLİĞİ: Orta-Yüksek                                         │
│  KULLANIM SIKLIĞI: Günlük                                                  │
│  CİHAZ: Desktop ağırlıklı, bazen tablet                                    │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Organizasyon onboarding                                               │
│  ├── Hesap sorunları çözme                                                 │
│  ├── Plan değişikliği işlemleri                                            │
│  ├── Raporlama ve analiz                                                   │
│  └── Kullanıcı desteği (impersonation)                                     │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Bilgi yoğunluğu: ORTA-YÜKSEK                                   │ │
│  │  ├── Dashboard özet kartları                                        │ │
│  │  ├── Quick action butonları                                         │ │
│  │  ├── Son aktiviteler listesi                                        │ │
│  │  └── Arama: Organizasyon hızlı erişim                               │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Normal spacing                                                 │ │
│  │  ├── Profosyonel, kurumsal his                                      │ │
│  │  └── Organizasyon bilgisi vurgulu                                   │ │
│  │                                                                       │ │
│  │  WORKFLOW:                                                           │ │
│  │  ├── Sık yapılan işlemler için wizard/form                         │ │
│  │  ├── Onboarding checklist görünümü                                 │ │
│  │  └── Ticket/destek entegrasyonu                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Sales Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SALES PERSONA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── Saha satış temsilcisi                                                 │
│  ├── Telesatış ekibi                                                       │
│  ├── Genellikle genç (25-35 yaş)                                          │
│  └── Dinamik, hedef odaklı                                                 │
│                                                                             │
│  TEKNOLOJİ YETKİNLİĞİ: Orta                                                │
│  KULLANIM SIKLIĞI: Sürekli (iş saatleri)                                   │
│  CİHAZ: MOBİL AĞIRLIKLI (sahada), tablet                                   │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Potansiyel müşteri yönetimi (lead tracking)                          │
│  ├── Demo gösterimi                                                        │
│  ├── Yeni kayıt oluşturma                                                  │
│  ├── Pipeline takibi                                                       │
│  └── Performans raporları                                                  │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ (MOBİL ÖNCELİKLİ):                                          │ │
│  │  ├── Büyük touch target'lar (sahada tek elle kullanım)              │ │
│  │  ├── Hızlı işlem: Minimum tıklama                                   │ │
│  │  ├── Offline destek (bağlantı sorunu)                               │ │
│  │  ├── Voice notes / hızlı not alma                                   │ │
│  │  └── One-tap arama (müşteriyi ara)                                  │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Enerjik, motivasyonel renk şeması                              │ │
│  │  ├── Başarı göstergeleri belirgin (günlük hedef)                   │ │
│  │  ├── Gamification elementleri (opsiyonel)                           │ │
│  │  └── Lead durumu renk kodlu                                         │ │
│  │                                                                       │ │
│  │  DEMO MODU:                                                          │ │
│  │  ├── Örnek menü ile hızlı demo gösterimi                           │ │
│  │  ├── "Canlı önizleme" özelliği                                     │ │
│  │  └── Müşteri adına hızlı kayıt                                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Support Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORT PERSONA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── Müşteri destek temsilcisi                                             │
│  ├── Farklı deneyim seviyeleri (junior-senior)                            │
│  ├── Empati odaklı, problem çözücü                                        │
│  └── Çoklu ticket yönetimi                                                 │
│                                                                             │
│  TEKNOLOJİ YETKİNLİĞİ: Orta                                                │
│  KULLANIM SIKLIĞI: Sürekli (vardiyalı)                                     │
│  CİHAZ: Desktop (kulaklık ile)                                             │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Kullanıcı sorularını yanıtlama                                       │
│  ├── Hesap sorunları araştırma                                             │
│  ├── Temel işlem desteği                                                   │
│  ├── Escalation (üst seviyeye aktarma)                                    │
│  └── Bilgi bankası kullanımı                                               │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Split view: Sol ticket listesi, sağ detay                      │ │
│  │  ├── Organizasyon bilgisi hızlı erişim (context)                    │ │
│  │  ├── Canned response (hazır yanıtlar)                               │ │
│  │  ├── Knowledge base sidebar entegrasyonu                            │ │
│  │  └── Hızlı impersonation linki                                      │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Sakin, stressiz renk paleti                                   │ │
│  │  ├── Ticket önceliği renk kodlu                                    │ │
│  │  ├── SLA timer görünür                                             │ │
│  │  └── Müşteri ruh hali göstergesi (opsiyonel)                       │ │
│  │                                                                       │ │
│  │  WORKFLOW:                                                           │ │
│  │  ├── Step-by-step troubleshooting wizard                           │ │
│  │  ├── Quick action: Şifre sıfırla, hesap durumu değiştir           │ │
│  │  └── Template response önerileri (AI destekli)                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. ORGANİZASYON ROL PERSONALARI

### 3.1 Owner Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OWNER PERSONA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── İşletme sahibi / Ortak                                                │
│  ├── Karar verici                                                          │
│  ├── Yaş: 30-60 (geniş aralık)                                            │
│  ├── Teknoloji yetkinliği: DEĞİŞKEN (düşük-orta)                          │
│  └── Zaman: KISITLI (işletme yönetimi meşgul)                             │
│                                                                             │
│  KULLANIM SIKLIĞI: Aralıklı (haftalık kontrol, aylık analiz)               │
│  CİHAZ: Mobil ağırlıklı (hareket halinde)                                  │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Genel performans takibi                                               │
│  ├── Finansal raporlar inceleme                                            │
│  ├── Abonelik / fatura yönetimi                                            │
│  ├── Ekip yetkilendirme                                                    │
│  ├── Stratejik kararlar                                                    │
│  └── Nadiren: Detaylı ayar değişikliği                                     │
│                                                                             │
│  MOTİVASYON:                                                                │
│  ├── İşletme büyütme                                                       │
│  ├── Rekabet avantajı                                                      │
│  ├── Operasyonel verimlilik                                                │
│  └── Müşteri memnuniyeti                                                   │
│                                                                             │
│  ZORLUKLAR:                                                                 │
│  ├── Zamanı kısıtlı                                                        │
│  ├── Teknoloji adaptasyonu zorlanabilir                                    │
│  ├── Birçok sorumluluğu var                                                │
│  └── Hızlı sonuç bekler                                                    │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Dashboard odaklı: Önemli metrikler tek bakışta                 │ │
│  │  ├── Executive summary: Grafik ve rakamlar                          │ │
│  │  ├── Minimal navigasyon derinliği (max 2 tık)                       │ │
│  │  ├── Bildirimler: Sadece kritik olanlar                            │ │
│  │  └── "Hızlı Eylemler" kısayolları                                   │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Profesyonel, güven veren                                       │ │
│  │  ├── Büyük rakamlar, net grafikler                                 │ │
│  │  ├── Yeşil/kırmızı trend göstergeleri                              │ │
│  │  └── Sade, dağınıklık yok                                          │ │
│  │                                                                       │ │
│  │  MOBİL:                                                              │ │
│  │  ├── Dashboard widget'ları                                          │ │
│  │  ├── Pull-to-refresh                                                │ │
│  │  ├── Push notification (kritik uyarılar)                           │ │
│  │  └── Hızlı rapor paylaşımı                                         │ │
│  │                                                                       │ │
│  │  DİL:                                                                │ │
│  │  ├── İş terimleri (ciro, kâr, büyüme)                              │ │
│  │  ├── Teknik jargon KAÇIN                                            │ │
│  │  └── Aksiyon odaklı ("Satışları artırmak için...")                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Manager Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MANAGER PERSONA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── İşletme müdürü / Operasyon şefi                                       │
│  ├── Günlük operasyondan sorumlu                                           │
│  ├── Yaş: 25-50                                                            │
│  ├── Teknoloji yetkinliği: Orta                                            │
│  └── Zaman: Yoğun ama esnek                                                │
│                                                                             │
│  KULLANIM SIKLIĞI: Günlük (vardiya başı/sonu)                              │
│  CİHAZ: Tablet + Mobil (işletme içinde hareket)                            │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Günlük operasyon yönetimi                                             │
│  ├── Menü güncelleme (fiyat, stok)                                        │
│  ├── Personel koordinasyonu                                                │
│  ├── Sipariş akışı takibi                                                  │
│  ├── Müşteri şikayeti çözme                                                │
│  ├── Günlük/haftalık raporlama                                             │
│  └── Kampanya yönetimi                                                     │
│                                                                             │
│  MOTİVASYON:                                                                │
│  ├── Sorunsuz operasyon                                                    │
│  ├── Ekip verimliliği                                                      │
│  ├── Müşteri memnuniyeti                                                   │
│  └── Hedeflere ulaşma                                                      │
│                                                                             │
│  ZORLUKLAR:                                                                 │
│  ├── Çoklu görev (multitasking)                                           │
│  ├── Kesintiler (sürekli sorular)                                         │
│  ├── Zaman baskısı (yoğun saatler)                                        │
│  └── Ekip yönetimi stresi                                                  │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Operasyon odaklı dashboard                                     │ │
│  │  ├── Canlı sipariş akışı görünümü                                  │ │
│  │  ├── Hızlı stok güncelleme (bir tık "Tükendi")                     │ │
│  │  ├── Personel durumu (kim nerede)                                   │ │
│  │  ├── Alert sistemi (bekleyen sipariş, düşük stok)                  │ │
│  │  └── Shift handoff notu                                            │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Status-driven renklendirme                                     │ │
│  │  ├── Kompakt ama okunabilir                                        │ │
│  │  ├── Kritik bilgi vurgulu                                          │ │
│  │  └── Timeline/gantt görünümü (sipariş akışı)                       │ │
│  │                                                                       │ │
│  │  TABLET OPTİMİZASYONU:                                              │ │
│  │  ├── Split view desteği                                            │ │
│  │  ├── Drag & drop işlemler                                          │ │
│  │  └── Landscape orientation uyumlu                                  │ │
│  │                                                                       │ │
│  │  HIZLI EYLEMLER:                                                    │ │
│  │  ├── "86" (ürün tükendi) tek buton                                 │ │
│  │  ├── "Garson çağır" yanıtla                                        │ │
│  │  ├── "Fiyat güncelle" inline                                       │ │
│  │  └── "Kampanya başlat/bitir" toggle                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Staff Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STAFF PERSONA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── Garson / Servis personeli                                             │
│  ├── Mutfak personeli (bazen)                                              │
│  ├── Yaş: 18-40 (genç ağırlıklı)                                          │
│  ├── Teknoloji yetkinliği: Orta (sosyal medya kullanıcısı)                │
│  └── Eğitim: Değişken                                                      │
│                                                                             │
│  KULLANIM SIKLIĞI: Sürekli (vardiya boyunca)                               │
│  CİHAZ: MOBİL (işletme telefonu veya kendi)                                │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Sipariş alma/iletme                                                   │
│  ├── Servis talepleri yanıtlama                                            │
│  ├── Masa durumu güncelleme                                                │
│  ├── Menü soruları yanıtlama (müşteriye)                                  │
│  └── Basit menü düzenleme (stok durumu)                                   │
│                                                                             │
│  MOTİVASYON:                                                                │
│  ├── Hızlı iş tamamlama                                                    │
│  ├── Hata yapmama                                                          │
│  ├── Müşteri memnuniyeti (bahşiş)                                         │
│  └── Kolay kullanım                                                        │
│                                                                             │
│  ZORLUKLAR:                                                                 │
│  ├── Yoğun saatlerde stres                                                 │
│  ├── Aynı anda birden fazla masa                                           │ 
│  ├── Gürültülü ortam                                                       │
│  ├── Elleri dolu olabilir                                                  │
│  └── Sınırlı eğitim süresi                                                 │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ (MOBİL FIRST):                                              │ │
│  │  ├── BÜYÜK BUTONLAR (56px+ yükseklik)                               │ │
│  │  ├── Minimal metin, ikon ağırlıklı                                  │ │
│  │  ├── Tek elle kullanım optimize                                     │ │
│  │  ├── Hızlı geçiş (swipe gestures)                                   │ │
│  │  ├── Sesli bildirim (vibrasyon + ses)                               │ │
│  │  └── Karanlık mod (gece çalışma)                                    │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Yüksek kontrast (loş ortamda okunabilir)                      │ │
│  │  ├── Renk kodlu masalar (boş/dolu/bekleyen)                        │ │
│  │  ├── Büyük sayılar (masa no, sipariş no)                           │ │
│  │  └── Animasyon az (dikkat dağıtmaz)                                │ │
│  │                                                                       │ │
│  │  WORKFLOW:                                                           │ │
│  │  ├── Max 3 adımda görev tamamlama                                  │ │
│  │  ├── Geri al desteği (yanlış tıklama)                              │ │
│  │  ├── Onay modalları minimal (sadece kritik)                        │ │
│  │  └── Offline tolerans (kısa bağlantı kopması)                      │ │
│  │                                                                       │ │
│  │  EĞİTİM:                                                            │ │
│  │  ├── Tooltip/coach mark ilk kullanımda                             │ │
│  │  ├── Video tutorial erişimi                                        │ │
│  │  └── Yaparak öğren (sandbox mod)                                   │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Cashier Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CASHIER PERSONA                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── Kasa personeli                                                        │
│  ├── Yaş: 20-50                                                            │
│  ├── Teknoloji yetkinliği: Düşük-Orta                                     │
│  └── Sabit pozisyon (kasa arkası)                                          │
│                                                                             │
│  KULLANIM SIKLIĞI: Sürekli (vardiya boyunca)                               │
│  CİHAZ: TABLET veya DESKTOP (kasa yanında)                                 │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Ödeme alma                                                            │
│  ├── Sipariş onaylama                                                      │
│  ├── Fatura/fiş kesme                                                      │
│  ├── Günlük kasa kapama                                                    │
│  └── Sipariş görüntüleme                                                   │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ (PoS ODAKLI):                                               │ │
│  │  ├── Numpad büyük ve erişilebilir                                   │ │
│  │  ├── Sipariş özeti net görünür                                     │ │
│  │  ├── Ödeme butonları belirgin (Nakit/Kart/Diğer)                   │ │
│  │  ├── Hızlı ürün ekleme (sık satılanlar)                            │ │
│  │  └── Günlük toplam her zaman görünür                               │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Para birimi ve rakamlar BÜYÜK                                 │ │
│  │  ├── Ödeme durumu renk kodlu                                       │ │
│  │  ├── Kontrastlı (ekrana uzaktan bakılabilir)                       │ │
│  │  └── Sade, dağınıklık yok                                          │ │
│  │                                                                       │ │
│  │  GÜVENLIK:                                                          │ │
│  │  ├── İptal işlemi için yönetici onayı                              │ │
│  │  ├── Kasa açma logu                                                │ │
│  │  └── Tutarsızlık uyarısı                                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Viewer Persona

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VIEWER PERSONA                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KİM:                                                                       │
│  ├── Dış danışman / Muhasebeci                                             │
│  ├── Yatırımcı / Ortak (operasyonda değil)                                │
│  ├── Franchiser (merkez)                                                   │
│  └── Sadece görüntüleme yetkisi                                            │
│                                                                             │
│  KULLANIM SIKLIĞI: Aralıklı (haftalık/aylık)                               │
│  CİHAZ: Desktop ağırlıklı                                                  │
│                                                                             │
│  GÖREVLER:                                                                  │
│  ├── Rapor inceleme                                                        │
│  ├── Performans takibi                                                     │
│  └── Veri dışa aktarma                                                     │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  ARAYÜZ:                                                             │ │
│  │  ├── Sadece okuma arayüzü (edit butonları yok)                     │ │
│  │  ├── Rapor ve analiz odaklı                                        │ │
│  │  ├── Export seçenekleri belirgin                                   │ │
│  │  └── Filtre ve tarih aralığı seçimi                                │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Profesyonel, kurumsal                                         │ │
│  │  ├── Grafik ve tablo ağırlıklı                                     │ │
│  │  └── Print-friendly tasarım                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. PUBLİK PERSONALAR (MÜŞTERİ)

### 4.1 Customer Persona Spektrumu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MÜŞTERİ PERSONA SPEKTRUMU                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  GENÇ MÜŞTERİ (18-30):                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Profil:                                                             │ │
│  │  ├── Teknolojiye aşina                                              │ │
│  │  ├── Hızlı karar verici                                             │ │
│  │  ├── Görsel odaklı (fotoğraf önemli)                               │ │
│  │  ├── Sosyal paylaşım eğilimi                                       │ │
│  │  └── Fiyat-duyarlı olabilir                                        │ │
│  │                                                                       │ │
│  │  Beklentiler:                                                        │ │
│  │  ├── Hızlı yükleme                                                  │ │
│  │  ├── Modern tasarım                                                 │ │
│  │  ├── Instagram'da paylaşılabilir fotoğraflar                       │ │
│  │  ├── Detaylı filtreleme (vegan, glutensiz vb.)                     │ │
│  │  └── Kolay sepet yönetimi                                          │ │
│  │                                                                       │ │
│  │  UI Yaklaşımı:                                                       │ │
│  │  ├── Trend tasarım elementleri                                      │ │
│  │  ├── Smooth animasyonlar                                            │ │
│  │  ├── Yatay swipe navigasyon                                        │ │
│  │  └── Social sharing butonları                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ORTA YAŞ MÜŞTERİ (30-55):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Profil:                                                             │ │
│  │  ├── Teknoloji ile barışık                                          │ │
│  │  ├── Verimlilik odaklı                                              │ │
│  │  ├── Kalite beklentisi yüksek                                       │ │
│  │  ├── Alerjen/besin bilgisi önemli                                  │ │
│  │  └── Aile ile gelebilir (çocuk menüsü)                             │ │
│  │                                                                       │ │
│  │  Beklentiler:                                                        │ │
│  │  ├── Net fiyatlandırma                                              │ │
│  │  ├── Detaylı ürün bilgisi                                          │ │
│  │  ├── Kolay navigasyon                                               │ │
│  │  ├── Güvenilir görünüm                                             │ │
│  │  └── Hızlı sipariş süreci                                          │ │
│  │                                                                       │ │
│  │  UI Yaklaşımı:                                                       │ │
│  │  ├── Klasik, anlaşılır layout                                      │ │
│  │  ├── Metin okunabilirliği yüksek                                   │ │
│  │  ├── Kategoriler net ayrılmış                                      │ │
│  │  └── Alerjen ikonları belirgin                                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  YAŞLI MÜŞTERİ (55+):                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Profil:                                                             │ │
│  │  ├── Teknoloji ile zorlanabilir                                     │ │
│  │  ├── Görme sorunları olabilir                                       │ │
│  │  ├── Daha yavaş karar verir                                        │ │
│  │  ├── Geleneksel menü deneyimine alışık                             │ │
│  │  └── Yardım isteme çekingenliği                                    │ │
│  │                                                                       │ │
│  │  Beklentiler:                                                        │ │
│  │  ├── Büyük, okunabilir yazılar                                     │ │
│  │  ├── Basit, kafa karıştırmayan                                     │ │
│  │  ├── Az seçenek (karar yorgunluğu yok)                             │ │
│  │  ├── Garson çağırma seçeneği                                       │ │
│  │  └── Fiyat net görünür                                             │ │
│  │                                                                       │ │
│  │  UI Yaklaşımı:                                                       │ │
│  │  ├── BÜYÜK font (20px+ base)                                       │ │
│  │  ├── Yüksek kontrast                                               │ │
│  │  ├── Geniş touch alanları                                          │ │
│  │  ├── Minimal hiyerarşi (düz liste tercih)                          │ │
│  │  ├── "Yardım" butonu belirgin                                      │ │
│  │  └── Accessibility mode otomatik algılama                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TURİST MÜŞTERİ:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Profil:                                                             │ │
│  │  ├── Dil bariyeri olabilir                                          │ │
│  │  ├── Yerel mutfağı keşfetmek istiyor                               │ │
│  │  ├── Fotoğraf çok önemli (ne sipariş ettiğini bilmeli)             │ │
│  │  └── Dietary restriction'lar (helal, koşer, vegan)                 │ │
│  │                                                                       │ │
│  │  Beklentiler:                                                        │ │
│  │  ├── Çoklu dil desteği                                             │ │
│  │  ├── Fotoğraflı menü                                               │ │
│  │  ├── İngilizcesi kesinlikle olmalı                                 │ │
│  │  ├── Alerjen/içerik bilgisi                                        │ │
│  │  └── Fiyatın para birimi net                                       │ │
│  │                                                                       │ │
│  │  UI Yaklaşımı:                                                       │ │
│  │  ├── Dil seçici hemen görünür                                      │ │
│  │  ├── Görsel ağırlıklı                                              │ │
│  │  ├── Universal ikonlar                                             │ │
│  │  └── Çeviri kalitesi yüksek                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. SEKTÖR BAZLI PERSONALAR

### 5.1 Fine Dining Personası

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FİNE DİNİNG İŞLETME PERSONASI                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İŞLETME PROFİLİ:                                                          │
│  ├── Yüksek fiyat segmenti                                                 │
│  ├── Detaylı yemek açıklamaları                                            │
│  ├── Şarap/içki menüsü ayrı ve önemli                                     │
│  ├── Deneyim odaklı (yemek + ambiyans)                                    │
│  ├── Rezervasyon sistemi kullanır                                          │
│  └── Az ürün, yüksek kalite                                                │
│                                                                             │
│  OWNER/MANAGER BEKLENTİSİ:                                                 │
│  ├── Menü "lüks" görünmeli                                                 │
│  ├── Marka imajını yansıtmalı                                              │
│  ├── QR kod "ucuz" hissettirmemeli                                        │
│  └── Dijital deneyim fiziksel kadar şık                                   │
│                                                                             │
│  MÜŞTERİ BEKLENTİSİ:                                                       │
│  ├── Şık, premium his                                                      │
│  ├── Detaylı yemek hikayesi                                                │
│  ├── Şef önerileri                                                         │
│  ├── Wine pairing önerileri                                                │
│  └── Alerjen/diyet bilgisi detaylı                                        │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TEMA ÖNERİSİ: Dark Luxe / Classic Elegant                          │ │
│  │                                                                       │ │
│  │  GÖRSEL DİL:                                                         │ │
│  │  ├── Koyu arka plan tercih                                          │ │
│  │  ├── Gold/champagne aksan renkleri                                  │ │
│  │  ├── Serif font (Playfair Display başlıklar)                       │ │
│  │  ├── Bol white space                                                │ │
│  │  ├── Subtle animasyonlar (fade-in)                                 │ │
│  │  └── Yüksek kalite fotoğraf zorunlu                                │ │
│  │                                                                       │ │
│  │  İÇERİK YAKLAŞIMI:                                                  │ │
│  │  ├── Uzun, hikaye odaklı açıklamalar                               │ │
│  │  ├── Malzeme kaynağı bilgisi                                       │ │
│  │  ├── Şef notu/tavsiyesi                                            │ │
│  │  ├── Şarap eşleştirme önerileri                                    │ │
│  │  └── Mevsimsel menü vurgusu                                        │ │
│  │                                                                       │ │
│  │  FONKSİYONELLİK:                                                    │ │
│  │  ├── Sipariş sistemi opsiyonel (sadece menü gösterimi)             │ │
│  │  ├── Tasting menu detaylı sunumu                                   │ │
│  │  ├── Wine list ayrı, filtrelenebilir                               │ │
│  │  └── Rezervasyon entegrasyonu                                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Fast Food / Döner / Pide Personası

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  FAST FOOD / DÖNER / PİDE PERSONASI                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İŞLETME PROFİLİ:                                                          │
│  ├── Hızlı servis                                                          │
│  ├── Yüksek müşteri devir hızı                                            │
│  ├── Fiyat odaklı müşteri                                                  │
│  ├── Paket servis önemli                                                   │
│  ├── Çok sayıda ürün (kombinasyonlar)                                     │
│  └── Yoğun saatler belirgin (öğle, akşam)                                 │
│                                                                             │
│  OWNER/MANAGER BEKLENTİSİ:                                                 │
│  ├── Hızlı sipariş akışı                                                   │
│  ├── Stok yönetimi kolay                                                   │
│  ├── Combo/menü oluşturma                                                  │
│  ├── Kampanya yönetimi                                                     │
│  └── Paket servis optimize                                                 │
│                                                                             │
│  MÜŞTERİ BEKLENTİSİ:                                                       │
│  ├── Hızlı karar, hızlı sipariş                                           │
│  ├── Fiyat net görünür                                                     │
│  ├── Combo seçenekleri belirgin                                           │
│  ├── Porsiyon bilgisi                                                      │
│  └── "Acılı mı?" gibi önemli bilgiler                                     │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TEMA ÖNERİSİ: Bold Contemporary / Street Food                      │ │
│  │                                                                       │ │
│  │  GÖRSEL DİL:                                                         │ │
│  │  ├── Canlı, iştah açıcı renkler (kırmızı, sarı, turuncu)           │ │
│  │  ├── Bold, okunabilir font                                          │ │
│  │  ├── Fiyat BÜYÜK ve belirgin                                       │ │
│  │  ├── Yemek fotoğrafları iştah açıcı                                │ │
│  │  └── Grid layout (hızlı tarama)                                    │ │
│  │                                                                       │ │
│  │  İÇERİK YAKLAŞIMI:                                                  │ │
│  │  ├── Kısa açıklamalar (max 1-2 satır)                              │ │
│  │  ├── Porsiyon/boyut belirgin                                       │ │
│  │  ├── Combo avantajı vurgulu ("₺X tasarruf")                        │ │
│  │  ├── Popüler badge'leri                                            │ │
│  │  └── Acılık seviyesi ikonu                                         │ │
│  │                                                                       │ │
│  │  FONKSİYONELLİK:                                                    │ │
│  │  ├── Hızlı sepete ekleme (tek tık)                                 │ │
│  │  ├── Ekstra seçenekler açılır menü                                 │ │
│  │  ├── Paket/gel-al toggle belirgin                                  │ │
│  │  ├── Sipariş takip ekranı                                          │ │
│  │  └── SMS/push bildirimi                                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Cafe / Kahve Dükkanı Personası

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CAFE / KAHVE DÜKKANI PERSONASI                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İŞLETME PROFİLİ:                                                          │
│  ├── Kahve çeşitliliği önemli                                              │
│  ├── Tatlı/pasta menüsü                                                    │
│  ├── Uzun oturma süresi                                                    │
│  ├── Wifi, laptop kullanıcıları                                           │
│  ├── Sohbet/buluşma mekanı                                                │
│  └── Sabah kahvaltısı segmenti                                            │
│                                                                             │
│  OWNER/MANAGER BEKLENTİSİ:                                                 │
│  ├── Estetik menü tasarımı                                                 │
│  ├── Kahve çeşitlerini açıklayabilmeli                                    │
│  ├── Sezonluk ürünler kolay güncellenebilir                               │
│  └── Instagram'da paylaşılabilir                                          │
│                                                                             │
│  MÜŞTERİ BEKLENTİSİ:                                                       │
│  ├── Kahve detayları (origin, demleme, notlar)                            │
│  ├── Şeker/süt seçenekleri                                                │
│  ├── Vegan/alternatif süt seçenekleri                                     │
│  ├── Kalori bilgisi                                                        │
│  └── Günlük öneri/mevsimlik                                               │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │ 
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TEMA ÖNERİSİ: Rustic Natural / Modern Minimal                      │ │
│  │                                                                       │ │
│  │  GÖRSEL DİL:                                                         │ │
│  │  ├── Sıcak, kahverengi tonlar                                       │ │
│  │  ├── Craft/artisanal his                                            │ │
│  │  ├── Temiz tipografi                                                │ │
│  │  ├── Instagram-worthy fotoğraflar                                   │ │
│  │  └── Pattern/doku (kahve tanesi, bitki)                            │ │
│  │                                                                       │ │
│  │  İÇERİK YAKLAŞIMI:                                                  │ │
│  │  ├── Kahve origin hikayesi                                         │ │
│  │  ├── Demleme yöntemi açıklaması                                    │ │
│  │  ├── Tat notları (çikolata, fındık vb.)                           │ │
│  │  ├── Barista önerisi                                               │ │
│  │  └── Pairing önerileri (kahve + tatlı)                            │ │
│  │                                                                       │ │
│  │  FONKSİYONELLİK:                                                    │ │
│  │  ├── Customization: Süt, şeker, boyut seçimi kolay                 │ │
│  │  ├── "Favorilerim" kaydetme                                        │ │
│  │  ├── Loyalty program entegrasyonu                                  │ │
│  │  └── Pre-order (sıra beklemeden al)                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Çiğ Köfte / Lahmacun Personası

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  ÇİĞ KÖFTE / LAHMACUN PERSONASI                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İŞLETME PROFİLİ:                                                          │
│  ├── Geleneksel Türk mutfağı                                               │
│  ├── Hızlı hazırlık                                                        │
│  ├── Paket servis yoğun                                                    │
│  ├── Standart porsiyon/fiyat                                               │
│  ├── Sos/garnitür seçenekleri                                              │
│  └── Bölgesel varyasyonlar                                                 │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TEMA ÖNERİSİ: Turkish Classic / Rustic Natural                     │ │
│  │                                                                       │ │
│  │  GÖRSEL DİL:                                                         │ │
│  │  ├── Geleneksel motifler (subtle kullanım)                          │ │
│  │  ├── Kırmızı ve yeşil aksan (biber, maydanoz)                      │ │
│  │  ├── Sıcak, samimi renkler                                         │ │
│  │  ├── Otantik fotoğraflar                                           │ │
│  │  └── Lokasyon/şehir vurgusu (Adıyaman, Urfa vb.)                   │ │
│  │                                                                       │ │
│  │  İÇERİK YAKLAŞIMI:                                                  │ │
│  │  ├── Porsiyon seçenekleri net (1'lik, 1.5'luk, 2'lik)              │ │
│  │  ├── İçecek eşleştirme (Ayran, Şalgam)                             │ │
│  │  ├── Acılık seviyesi seçimi                                        │ │
│  │  └── Sos/garnitür checklist                                        │ │
│  │                                                                       │ │
│  │  FONKSİYONELLİK:                                                    │ │
│  │  ├── Hızlı sipariş (tek ürün odaklı)                               │ │
│  │  ├── Ekstra seçenekler (nar ekşisi, acı sos)                       │ │
│  │  ├── Combo menü kolay oluşturma                                    │ │
│  │  └── Paket servis optimize                                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 Börekçi / Poğaçacı / Pastane Personası

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 BÖREKÇİ / POĞAÇACI / PASTANE PERSONASI                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İŞLETME PROFİLİ:                                                          │
│  ├── Sabah kahvaltı segmenti önemli                                        │
│  ├── Paket satış yoğun                                                     │
│  ├── Günlük taze üretim                                                    │
│  ├── Çeşit fazla, fiyat benzer                                            │
│  ├── Görsel çekicilik kritik                                               │
│  └── Toplu sipariş (ofis, toplantı)                                       │
│                                                                             │
│  UI/UX YAKLAŞIMI:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  TEMA ÖNERİSİ: Classic Elegant / Modern Minimal                     │ │
│  │                                                                       │ │
│  │  GÖRSEL DİL:                                                         │ │
│  │  ├── Sıcak, ev yapımı hissi                                         │ │
│  │  ├── Kahverengi, krem, gold tonlar                                 │ │
│  │  ├── Yakın çekim, doku gösteren fotoğraflar                        │ │
│  │  ├── Grid görünüm (çeşitleri karşılaştır)                          │ │
│  │  └── "Taze" badge'i                                                │ │
│  │                                                                       │ │
│  │  İÇERİK YAKLAŞIMI:                                                  │ │
│  │  ├── İçerik listesi (peynirli, patatesli vb.)                      │ │
│  │  ├── "Bugün Taze" göstergesi                                       │ │
│  │  ├── Adet/gram seçimi                                              │ │
│  │  └── Toplu sipariş fiyatı                                          │ │
│  │                                                                       │ │
│  │  FONKSİYONELLİK:                                                    │ │
│  │  ├── Hızlı çoklu seçim (sepete ekle + devam)                       │ │
│  │  ├── Karma tabak oluşturma                                         │ │
│  │  ├── İleri tarihli sipariş (özel gün)                              │ │
│  │  └── Toplu sipariş formu                                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. KRİTİK KULLANICI AKIŞLARI

### 6.1 Müşteri: QR'dan Siparişe Akışı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MÜŞTERİ SİPARİŞ AKIŞI                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AŞAMA 1: GİRİŞ (0-3 saniye)                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Eylem: QR kod tarama                                                │ │
│  │  Beklenti: Anında açılmalı                                           │ │
│  │  UI: Splash/loading state (max 2 saniye)                             │ │
│  │  Erişilebilirlik: Otomatik cihaz ayarlarını algıla                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 2: MENÜ KARŞILAMA (3-10 saniye)                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Gördükleri:                                                         │ │
│  │  ├── İşletme logosu ve adı                                          │ │
│  │  ├── Kategoriler (horizontal scroll veya grid)                      │ │
│  │  ├── Öne çıkan ürünler                                              │ │
│  │  └── Arama çubuğu                                                   │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Above the fold: En az 3 ürün görünmeli                        │ │
│  │  ├── Kategori seçimi 1 tıkla olmalı                                │ │
│  │  ├── Fiyat her üründe görünür                                      │ │
│  │  └── Sepet ikonu sürekli görünür (badge ile miktar)                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 3: ÜRÜN KEŞFİ (30 saniye - 5 dakika)                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Davranışlar:                                                        │ │
│  │  ├── Kategoriler arası geçiş                                        │ │
│  │  ├── Ürün detayı görüntüleme                                        │ │
│  │  ├── Fiyat karşılaştırma                                            │ │
│  │  └── Filtreleme (vegan, glutensiz vb.)                              │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Geri butonu her zaman erişilebilir                             │ │
│  │  ├── Scroll pozisyonu hatırlanır                                   │ │
│  │  ├── Ürün detay modal/sheet (sayfa değişimi yok)                   │ │
│  │  ├── Swipe ile kategori değiştirme                                 │ │
│  │  └── Alerjen/diyet filtreleri kolay erişim                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 4: SEPETE EKLEME (5-30 saniye per item)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Akış:                                                               │ │
│  │  1. "Sepete Ekle" tıklama                                           │ │
│  │  2. Varyant seçimi (varsa): Boyut, porsiyon                        │ │
│  │  3. Modifier seçimi (varsa): Ekstralar, çıkarılacaklar             │ │
│  │  4. Adet belirleme                                                  │ │
│  │  5. Onaylama                                                        │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Quick add: Varyant/modifier yoksa tek tıkla                   │ │
│  │  ├── Fiyat güncelleme: Seçimlere göre anlık                        │ │
│  │  ├── Sepet badge: Anlık güncelleme + animasyon                     │ │
│  │  ├── Toast: "Ürün eklendi" onayı (2 saniye)                        │ │
│  │  └── "Alışverişe devam" + "Sepete git" seçenekleri                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 5: SEPET İNCELEME (30 saniye - 2 dakika)                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Gösterilecek:                                                       │ │
│  │  ├── Tüm ürünler detaylı                                            │ │
│  │  ├── Adet değiştirme                                                │ │
│  │  ├── Ürün kaldırma                                                  │ │
│  │  ├── Ara toplam                                                     │ │
│  │  └── İndirim kodu girişi (varsa)                                   │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Boş sepet: Empty state + CTA (menüye dön)                     │ │
│  │  ├── Silme: Swipe veya ikon + onay                                 │ │
│  │  ├── Toplam: Sticky footer'da                                      │ │
│  │  └── "Sipariş Ver" butonu belirgin                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 6: SİPARİŞ TAMAMLAMA (30 saniye - 1 dakika)                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Form alanları:                                                      │ │
│  │  ├── Masa numarası (zorunlu, QR'dan otomatik gelebilir)            │ │
│  │  ├── Özel not (opsiyonel)                                           │ │
│  │  └── Telefon (opsiyonel, bildirim için)                            │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Minimum form alanı                                             │ │
│  │  ├── Klavye otomatik açılma                                        │ │
│  │  ├── Sipariş özeti görünür                                         │ │
│  │  └── "Sipariş Ver" butonu tek aksiyon                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AŞAMA 7: ONAY VE TAKİP                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Gösterilecek:                                                       │ │
│  │  ├── Sipariş numarası (BÜYÜK)                                       │ │
│  │  ├── Tahmini süre                                                   │ │
│  │  ├── Sipariş özeti                                                  │ │
│  │  └── Durum takip linki/QR                                          │ │
│  │                                                                       │ │
│  │  UI Kuralları:                                                       │ │
│  │  ├── Başarı animasyonu (confetti subtle)                           │ │
│  │  ├── Sipariş numarası kopyalanabilir                               │ │
│  │  ├── Push notification izni iste (opsiyonel)                       │ │
│  │  └── "Yeni sipariş" + "Menüye dön" seçenekleri                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 İşletme: Günlük Operasyon Akışı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   İŞLETME GÜNLÜK OPERASYON AKIŞI                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SABAH AÇILIŞ (Manager):                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Dashboard kontrolü (dün özet, bugün hedef)                       │ │
│  │  2. Stok durumu kontrolü (tükenen ürünler)                          │ │
│  │  3. Personel durumu (kim çalışıyor)                                 │ │
│  │  4. Kampanya durumu (aktif kampanyalar)                             │ │
│  │  5. Menü güncelleme (günlük değişiklikler)                          │ │
│  │                                                                       │ │
│  │  UI: Dashboard → Quick actions → Checklist                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SERVİS SAATİ (Staff):                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Tekrarlayan eylemler:                                               │ │
│  │  1. Yeni sipariş bildirimi alma                                     │ │
│  │  2. Sipariş durumu güncelleme                                       │ │
│  │  3. Servis talebi yanıtlama                                         │ │
│  │  4. Stok durumu bildirme (tükenen)                                  │ │
│  │                                                                       │ │
│  │  UI: Bildirim odaklı, büyük butonlar, minimal navigasyon           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  YOĞUN SAAT (Manager + Staff):                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öncelikler:                                                         │ │
│  │  ├── Sipariş akışı takibi (bottleneck tespiti)                     │ │
│  │  ├── Hızlı stok güncelleme ("86" butonu)                           │ │
│  │  ├── Müşteri şikayeti çözme                                        │ │
│  │  └── Ek personel koordinasyonu                                      │ │
│  │                                                                       │ │
│  │  UI: Minimal, sadece kritik bilgi, hızlı aksiyonlar                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AKŞAM KAPANIŞ (Manager):                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Günlük rapor inceleme                                           │ │
│  │  2. Kasa kapama (varsa)                                             │ │
│  │  3. Stok kontrolü (eksikler)                                        │ │
│  │  4. Yarın için hazırlık notları                                     │ │
│  │  5. Shift handoff                                                   │ │
│  │                                                                       │ │
│  │  UI: Rapor odaklı, özet kartları, export seçenekleri               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. PERSONA-UI MAPPING ÖZETİ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSONA-UI MAPPING ÖZETİ                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Persona        │ Cihaz     │ Yoğunluk │ Öncelik            │ Stil         │
│  ──────────────────────────────────────────────────────────────────────────│
│  Super Admin    │ Desktop   │ Yüksek   │ Güç, kontrol       │ Profesyonel  │
│  Admin          │ Desktop   │ Orta-Y   │ Verimlilik         │ Kurumsal     │
│  Sales          │ Mobil     │ Düşük-O  │ Hız, hareket       │ Enerjik      │
│  Support        │ Desktop   │ Orta     │ Empati, çözüm      │ Sakin        │
│  Owner          │ Mobil     │ Düşük    │ Özet, karar        │ Premium      │
│  Manager        │ Tablet    │ Orta-Y   │ Operasyon          │ Fonksiyonel  │
│  Staff          │ Mobil     │ Düşük    │ Hız, hatasızlık    │ Minimal      │
│  Cashier        │ Tablet    │ Düşük    │ Rakamlar, ödeme    │ PoS odaklı   │
│  Viewer         │ Desktop   │ Düşük    │ Rapor, analiz      │ Analitik     │
│  Genç Müşteri   │ Mobil     │ Düşük    │ Hız, görsel        │ Trend        │
│  Yaşlı Müşteri  │ Mobil     │ Çok düşük│ Okunabilirlik      │ Basit        │
│  Turist         │ Mobil     │ Düşük    │ Dil, görsel        │ Universal    │
│                                                                             │
│  Yoğunluk: Bilgi yoğunluğu tercihi                                         │
│  Yüksek = Çok veri, compact                                                │
│  Düşük = Az veri, spacious                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Bu döküman, E-Menum persona ve kullanıcı akışlarını tanımlar. Tüm UI kararları bu personalar göz önünde bulundurularak alınmalıdır.*
