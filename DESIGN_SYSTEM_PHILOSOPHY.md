# E-Menum Design System Philosophy

> **Auto-Claude Design Philosophy Document**  
> Estetik felsefe, UED yaklaşımı, erişilebilirlik-güzellik dengesi, theming sistemi.  
> Son Güncelleme: 2026-01-31

---

## 1. TASARIM FELSEFESİ

### 1.1 Temel İlkeler

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     E-MENUM TASARIM FELSEFESİ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "HERKESİN GÜZELLİĞİ" (Beauty for Everyone)                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Erişilebilirlik + Estetik = Kapsayıcı Güzellik                      │ │
│  │                                                                       │ │
│  │  Bu iki kavram birbirine zıt DEĞİLDİR.                               │ │
│  │  Aksine, birbirini güçlendirir.                                      │ │
│  │                                                                       │ │
│  │  Yüksek kontrast = Okunabilirlik = Netlik = Profesyonellik           │ │
│  │  Geniş tıklama alanı = Rahatlık = Premium his                         │ │
│  │  Büyük tipografi = Dikkat çekici = Modern                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TASARIM İLKELERİ HİYERARŞİSİ:                                             │
│                                                                             │
│  1. KULLANILABILIRLIK (Usability)                                          │
│     └── Herkes kullanabilmeli: 8 yaşından 80 yaşına                        │
│                                                                             │
│  2. ERİŞİLEBİLİRLİK (Accessibility)                                        │
│     └── Engel tanımayan tasarım: görme, duyma, motor, bilişsel            │
│                                                                             │
│  3. ANLAŞILABİLİRLİK (Clarity)                                             │
│     └── İlk bakışta anlaşılır: karmaşıklık minimumda                      │
│                                                                             │
│  4. TUTARLILIK (Consistency)                                                │
│     └── Öğrenilen kalıplar tekrar eder: tahmin edilebilir davranış        │
│                                                                             │
│  5. ESTETİK (Aesthetics)                                                    │
│     └── Görsel çekicilik: profesyonel, modern, güvenilir                  │
│                                                                             │
│  6. MARKA UYUMU (Brand Alignment)                                          │
│     └── İşletme kimliğini yansıtır: özelleştirilebilir                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 "Güzel ama Erişilebilir" Dengesi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ERİŞİLEBİLİRLİK-ESTETİK DENGESİ                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  YANLIŞ DÜŞÜNCE:                                                            │
│  "Erişilebilir = çirkin, sıkıcı, kısıtlayıcı"                              │
│                                                                             │
│  DOĞRU YAKLAŞIM:                                                            │
│  "Erişilebilir = profesyonel, net, güvenilir"                              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  Yüksek Kontrast Çirkin mi?                                          │ │
│  │  ────────────────────────                                            │ │
│  │  Apple, Google, Airbnb: Tüm premium markalar yüksek kontrastlı.     │ │
│  │  Kontrast = Netlik = Premium = Güvenilirlik                          │ │
│  │                                                                       │ │
│  │  Büyük Yazı Tipi Yaşlılara mı Özel?                                  │ │
│  │  ────────────────────────────────                                    │ │
│  │  Büyük tipografi = Modern editorial tasarım trendi                   │ │
│  │  Medium, New York Times: Büyük, okunabilir, premium                  │ │
│  │                                                                       │ │
│  │  Geniş Touch Alanı Mobilde Sorun mu?                                 │ │
│  │  ────────────────────────────────                                    │ │
│  │  Geniş tıklama = Rahat kullanım = Hata azaltma = Memnuniyet          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DENGE STRATEJİSİ:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. Kontrastı Renk Paleti ile Dengele                                │ │
│  │     Yüksek kontrast + sofistike renk seçimi = Elegant                │ │
│  │                                                                       │ │
│  │  2. Büyük Tipoyu Kaliteli Font ile Destekle                          │ │
│  │     Büyük punto + premium font (Inter) = Editorial                   │ │
│  │                                                                       │ │
│  │  3. Geniş Alanı White Space ile Harmanlа                             │ │
│  │     Büyük touch target + bol boşluk = Lüks his                       │ │
│  │                                                                       │ │
│  │  4. Erişilebilirliği Tasarımın Temeline Al                           │ │
│  │     Sonradan ekleme değil, en baştan düşün                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. HEDEFİ KİTLE SPEKTRUMU

### 2.1 Görme Yetisi Spektrumu

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GÖRME YETİSİ TASARIM KRİTERLERİ                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  20/20 GÖRÜŞ (Normal):                                                      │
│  ├── Taban tasarım bu grup için optimize                                   │
│  ├── Standart kontrastlar yeterli                                          │
│  └── Varsayılan font boyutları uygun                                       │
│                                                                             │
│  MİYOP (Yakını Net Görür):                                                  │
│  ├── Ekranda okumada genellikle sorun yok                                  │
│  ├── Telefonu yakın tutma eğilimi                                          │
│  ├── Küçük detayları kaçırabilir uzaktan bakınca                          │
│  └── Tasarım yaklaşımı: Detayları büyüt, hover durumları belirgin         │
│                                                                             │
│  HİPERMETROP (Uzağı Net Görür):                                            │
│  ├── Ekran okumada zorlanma (özellikle küçük metin)                       │
│  ├── Telefonu uzak tutma eğilimi                                           │
│  ├── Küçük butonlara basmada zorluk                                        │
│  └── Tasarım yaklaşımı:                                                    │
│      • Minimum font: 18px (tercihen 20px)                                  │
│      • Buton yüksekliği: minimum 52px                                      │
│      • Satır aralığı: 1.7+ line-height                                     │
│      • Link altı çizgi: Kalın ve belirgin                                  │
│                                                                             │
│  PREZBİYOPİ (Yaşa Bağlı - 40+ yaş):                                        │
│  ├── Yakın odaklanmada zorluk                                              │
│  ├── Hipermetrop'a benzer sorunlar                                         │
│  ├── Gece görüşünde azalma                                                 │
│  └── Tasarım yaklaşımı:                                                    │
│      • Karanlık modda daha az parlak beyaz                                 │
│      • Daha yüksek kontrast (7:1 hedef)                                    │
│      • Font ağırlığı: medium tercih                                        │
│                                                                             │
│  70+ YAŞ ÖNCELİKLERİ:                                                       │
│  ├── Görme netliği düşüşü                                                  │
│  ├── Renk algısı azalması                                                  │
│  ├── Ekran parlamasına hassasiyet                                          │
│  ├── Motor beceri yavaşlaması                                              │
│  └── Tasarım yaklaşımı:                                                    │
│      • Senior Mode / Erişilebilirlik Modu sunulmalı                        │
│      • Font: 20-24px base                                                  │
│      • Kontrast: AAA seviyesi (7:1+)                                       │
│      • Touch target: 56px minimum                                          │
│      • Animasyon: Yavaş veya kapalı                                        │
│      • Parlak beyaz yerine kırık beyaz (#F8F8F8)                           │
│                                                                             │
│  RENK KÖRLÜĞÜ:                                                              │
│  ├── Kırmızı-Yeşil (en yaygın, erkeklerin %8'i)                           │
│  ├── Mavi-Sarı (nadir)                                                     │
│  └── Tasarım yaklaşımı:                                                    │
│      • Renk TEK BAŞINA bilgi taşımamalı                                    │
│      • Başarı/hata: İkon + metin + renk birlikte                          │
│      • Grafikler: Desen + renk kombinasyonu                               │
│      • Test: Renk körlüğü simülatörleri ile doğrulama                     │
│                                                                             │
│  DÜŞÜK GÖRÜŞ (Görme Engelli):                                              │
│  ├── Ekran büyüteci kullanımı                                              │
│  ├── Ekran okuyucu kullanımı                                               │
│  └── Tasarım yaklaşımı:                                                    │
│      • %400 zoom'da bile kullanılabilir olmalı                             │
│      • ARIA etiketleri eksiksiz                                            │
│      • Mantıksal DOM sırası                                                │
│      • Başlık hiyerarşisi doğru                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Erişilebilirlik Modları

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ERİŞİLEBİLİRLİK MOD SİSTEMİ                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STANDART MOD (Varsayılan):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Font boyutu:        16px base                                        │ │
│  │  Kontrast:           AA seviyesi (4.5:1)                              │ │
│  │  Touch target:       48px                                             │ │
│  │  Satır aralığı:      1.5                                              │ │
│  │  Animasyonlar:       Normal                                           │ │
│  │  Arka plan:          Pure white (#FFFFFF)                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KONFOR MODU (Uzun kullanım için):                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Font boyutu:        18px base                                        │ │
│  │  Kontrast:           AA+ seviyesi (5.5:1)                             │ │
│  │  Touch target:       52px                                             │ │
│  │  Satır aralığı:      1.6                                              │ │
│  │  Animasyonlar:       Azaltılmış                                       │ │
│  │  Arka plan:          Soft white (#FAFAFA)                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SENİOR MOD (65+ yaş optimize):                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Font boyutu:        20-22px base                                     │ │
│  │  Kontrast:           AAA seviyesi (7:1)                               │ │
│  │  Touch target:       56px                                             │ │
│  │  Satır aralığı:      1.8                                              │ │
│  │  Animasyonlar:       Minimal veya kapalı                              │ │
│  │  Arka plan:          Cream (#F8F6F3)                                  │ │
│  │  Font ağırlığı:      Medium (500)                                     │ │
│  │  Link stili:         Kalın altı çizgi                                 │ │
│  │  Buton stili:        Daha yuvarlak, daha dolgun                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  YÜKSEK KONTRAST MODU (Görme engelli uyumlu):                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Arka plan:          Saf beyaz veya saf siyah                         │ │
│  │  Metin:              Saf siyah veya saf beyaz                         │ │
│  │  Kenarlıklar:        Kalın, belirgin (2-3px)                          │ │
│  │  Gölgeler:           Kapalı                                           │ │
│  │  Degradeler:         Düz renklerle değiştirilmiş                      │ │
│  │  Odak göstergesi:    Çok belirgin (3px+ outline)                      │ │
│  │  İkonlar:            Dolgu ile, çizgi değil                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DİSLEKSİ DOSTU MOD:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Font ailesi:        OpenDyslexic veya Comic Sans                     │ │
│  │  Harf aralığı:       0.12em                                           │ │
│  │  Kelime aralığı:     0.16em                                           │ │
│  │  Satır aralığı:      2.0                                              │ │
│  │  Paragraf aralığı:   2em                                              │ │
│  │  Arka plan:          Krem veya açık sarı (göz yorgunluğu azaltır)    │ │
│  │  Metin hizalama:     Sola yaslı (iki yana değil)                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  MOD SEÇİM MEKANİZMASI:                                                     │
│  ├── İlk ziyarette: Sistem tercihlerini oku (prefers-reduced-motion, vb.) │
│  ├── Kolay erişim: Footer'da veya ayarlar ikonunda                        │
│  ├── Hatırlama: localStorage + kullanıcı profili (giriş yaptıysa)        │
│  └── Geçiş: Anlık, sayfa yenilemesi gerektirmeden                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. THEMING & SKIN SİSTEMİ

### 3.1 Tema Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TEMA MİMARİSİ KATMANlari                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  KATMAN 1: PLATFORM ÇEKİRDEĞİ (Değiştirilemez)                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Erişilebilirlik kuralları (WCAG minimum)                          │ │
│  │  • Güvenlik stilleri (input sanitization görünümü)                   │ │
│  │  • Temel layout yapısı (grid sistemi)                                │ │
│  │  • Responsive breakpoint'ler                                         │ │
│  │  • Z-index hiyerarşisi                                               │ │
│  │  • Focus durumu minimum standartları                                 │ │
│  │                                                                       │ │
│  │  Neden değiştirilemez: Accessibility ve UX tutarlılığı için          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KATMAN 2: TEMA PRESETLERI (Platform Sunuyor)                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Hazır tema şablonları - İşletme seçer:                              │ │
│  │                                                                       │ │
│  │  • Modern Minimal    │ Temiz, beyaz, minimal gölge                   │ │
│  │  • Classic Elegant   │ Serif font, sıcak tonlar, zarif               │ │
│  │  • Bold Contemporary │ Güçlü renkler, geometrik, enerjik             │ │
│  │  • Rustic Natural    │ Toprak tonları, organik şekiller              │ │
│  │  • Dark Luxe         │ Koyu arka plan, gold aksan, premium           │ │
│  │  • Playful Casual    │ Yuvarlak, renkli, samimi                      │ │
│  │  • Turkish Classic   │ Osmanlı motifleri, bordo-gold                 │ │
│  │  • Street Food       │ Neon, urban, dinamik                          │ │
│  │                                                                       │ │
│  │  Her preset içerir:                                                  │ │
│  │  ├── Renk paleti (primary, secondary, accent, neutral)              │ │
│  │  ├── Font kombinasyonu (heading + body)                             │ │
│  │  ├── Border radius profili (sharp, rounded, pill)                   │ │
│  │  ├── Shadow profili (flat, subtle, elevated)                        │ │
│  │  ├── Spacing profili (compact, comfortable, spacious)               │ │
│  │  └── Animasyon profili (none, subtle, expressive)                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KATMAN 3: MARKA ÖZELLEŞTİRME (İşletme Ayarlar)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Theme Options Panel (WordPress benzeri):                            │ │
│  │                                                                       │ │
│  │  RENKLER:                                                            │ │
│  │  ├── Primary Color (marka ana rengi)                                │ │
│  │  │   └── Otomatik: Light, dark, subtle varyantları üretilir         │ │
│  │  ├── Secondary Color (ikincil renk)                                 │ │
│  │  ├── Accent Color (vurgu rengi)                                     │ │
│  │  └── Kontrast doğrulama: Geçersiz kombinasyonlar reddedilir         │ │
│  │                                                                       │ │
│  │  TİPOGRAFİ:                                                          │ │
│  │  ├── Heading Font (onaylanmış font listesinden)                     │ │
│  │  ├── Body Font (onaylanmış font listesinden)                        │ │
│  │  └── Font size multiplier (0.9x - 1.2x)                             │ │
│  │                                                                       │ │
│  │  GÖRSEL:                                                             │ │
│  │  ├── Logo (light + dark versiyon)                                   │ │
│  │  ├── Favicon                                                        │ │
│  │  ├── Menü arka plan görseli (opsiyonel)                             │ │
│  │  └── Pattern/Desen seçimi (opsiyonel)                               │ │
│  │                                                                       │ │
│  │  GENEL:                                                              │ │
│  │  ├── Border radius: Sharp / Rounded / Pill                          │ │
│  │  ├── Shadow intensity: None / Subtle / Medium / Strong              │ │
│  │  ├── Animation level: Off / Subtle / Full                           │ │
│  │  └── Dark mode: Auto / Light only / Dark only                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KATMAN 4: GELİŞMİŞ ÖZELLEŞTIRME (Enterprise Planı)                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Custom CSS enjeksiyonu (doğrulanmış, güvenli)                     │ │
│  │  • Custom font yükleme (WOFF2)                                       │ │
│  │  • Tam renk paleti override                                          │ │
│  │  • White-label (E-Menum markası kaldırılır)                         │ │
│  │  • Custom domain                                                     │ │
│  │  • Custom email template                                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Sektör Bazlı Tema Önerileri

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  SEKTÖR BAZLI TEMA REHBERİ                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FİNE DİNİNG RESTORAN:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Dark Luxe veya Classic Elegant                        │ │
│  │  Renk: Koyu tonlar, gold/şampanya aksan                              │ │
│  │  Font: Serif heading (Playfair), sans body (Inter)                   │ │
│  │  Border: Sharp veya subtle rounded                                   │ │
│  │  Fotoğraf: Yüksek kalite, karanlık arka plan                        │ │
│  │  His: Lüks, sofistike, özel                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CASUAL DİNİNG / CAFE:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Modern Minimal veya Playful Casual                    │ │
│  │  Renk: Sıcak nötrler, pastel aksan                                   │ │
│  │  Font: Modern sans-serif (Inter, Poppins)                            │ │
│  │  Border: Rounded (8-12px)                                            │ │
│  │  Fotoğraf: Aydınlık, doğal ışık                                     │ │
│  │  His: Rahat, samimi, günlük                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FAST FOOD / DÖNER / PİDE:                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Bold Contemporary veya Street Food                    │ │
│  │  Renk: Canlı kırmızı, sarı, turuncu (iştah açıcı)                   │ │
│  │  Font: Bold, condensed sans-serif                                    │ │
│  │  Border: Rounded veya sharp                                          │ │
│  │  Fotoğraf: Yakın çekim, iştah açıcı                                 │ │
│  │  His: Hızlı, enerjik, erişilebilir                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ÇİĞ KÖFTE / LAHMACUN / PIDE:                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Turkish Classic veya Rustic Natural                   │ │
│  │  Renk: Kırmızı, yeşil (biber), toprak tonları                       │ │
│  │  Font: Geleneksel hisli, okunabilir                                 │ │
│  │  Border: Rounded                                                     │ │
│  │  Desen: Geleneksel motifler (subtle)                                │ │
│  │  His: Geleneksel, otantik, lezzetli                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BÖREK / POĞAÇA / PASTANE:                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Classic Elegant veya Modern Minimal                   │ │
│  │  Renk: Sıcak kahverengi, krem, gold                                 │ │
│  │  Font: Zarif, okunabilir                                            │ │
│  │  Border: Soft rounded                                                │ │
│  │  Fotoğraf: Yakın çekim, doku vurgusu                                │ │
│  │  His: Ev yapımı, sıcak, güvenilir                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KAHVE DÜKANI / ROASTERY:                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Rustic Natural veya Dark Luxe                         │ │
│  │  Renk: Kahve tonları, koyu yeşil, bakır                             │ │
│  │  Font: Vintage veya modern industrial                               │ │
│  │  Border: Mix (sharp + rounded)                                       │ │
│  │  Fotoğraf: Artisanal, detay odaklı                                  │ │
│  │  His: Craft, özenli, uzman                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  BAR / GECE KULÜBÜ:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Dark Luxe veya Street Food (neon varyant)            │ │
│  │  Renk: Koyu arka plan, neon aksan, mor/mavi                         │ │
│  │  Font: Modern, bold                                                  │ │
│  │  Border: Sharp veya pill                                             │ │
│  │  Efekt: Glow, gradient                                               │ │
│  │  His: Eğlenceli, gece, premium                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  SAĞLIKLI YEMEK / VEGAN:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Öneri Preset: Modern Minimal veya Rustic Natural                    │ │
│  │  Renk: Yeşil tonları, doğal, toprak                                 │ │
│  │  Font: Temiz, modern sans                                           │ │
│  │  Border: Soft rounded                                                │ │
│  │  Fotoğraf: Taze, doğal ışık, yeşillik                              │ │
│  │  His: Temiz, sağlıklı, bilinçli                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Theme Options Panel Yapısı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  THEME OPTIONS PANEL MİMARİSİ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PANEL BÖLÜMLERI:                                                           │
│                                                                             │
│  1. PRESET SEÇİMİ                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Grid görünümde tema kartları                                        │ │
│  │  Her kartta:                                                         │ │
│  │  ├── Önizleme görseli                                               │ │
│  │  ├── Tema adı                                                        │ │
│  │  ├── Kısa açıklama                                                  │ │
│  │  └── "Uygula" butonu                                                │ │
│  │                                                                       │ │
│  │  Seçim sonrası: Tüm alt ayarlar preset değerlerine resetlenir       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  2. RENK PALETİ                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Color picker bileşenleri:                                           │ │
│  │  ├── Primary Color (ana renk)                                       │ │
│  │  │   └── Alt varyantlar otomatik üretilir (gösterilir)              │ │
│  │  ├── Secondary Color                                                │ │
│  │  ├── Accent Color                                                   │ │
│  │  └── Background seçimi (açık/koyu/özel)                             │ │
│  │                                                                       │ │
│  │  Kontrast doğrulama:                                                │ │
│  │  ├── Yeşil tik: WCAG AA geçer                                       │ │
│  │  ├── Sarı uyarı: Sınırda                                            │ │
│  │  └── Kırmızı hata: Geçersiz (uygulama engellenir)                   │ │
│  │                                                                       │ │
│  │  Canlı önizleme: Değişiklikler anında menü preview'da görünür       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  3. TİPOGRAFİ                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Font seçiciler (dropdown + preview):                                │ │
│  │  ├── Başlık fontu (heading font)                                    │ │
│  │  ├── Gövde fontu (body font)                                        │ │
│  │  └── Font boyutu çarpanı (slider: 90% - 120%)                       │ │
│  │                                                                       │ │
│  │  Onaylı font listesi (performans + lisans):                         │ │
│  │  ├── Inter (varsayılan, çok yönlü)                                  │ │
│  │  ├── Poppins (modern, geometrik)                                    │ │
│  │  ├── Roboto (Google standard)                                       │ │
│  │  ├── Open Sans (nötr, okunabilir)                                   │ │
│  │  ├── Playfair Display (serif, elegant)                              │ │
│  │  ├── Merriweather (serif, okunabilir)                               │ │
│  │  ├── Nunito (yumuşak, samimi)                                       │ │
│  │  ├── Montserrat (geometric, modern)                                 │ │
│  │  └── Raleway (zarif, ince)                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  4. GÖRSEL AYARLAR                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Logo yönetimi:                                                      │ │
│  │  ├── Light mode logo (koyu arka planlarda kullanılır)               │ │
│  │  ├── Dark mode logo (açık arka planlarda kullanılır)                │ │
│  │  └── Favicon                                                         │ │
│  │                                                                       │ │
│  │  Arka plan:                                                          │ │
│  │  ├── Düz renk                                                        │ │
│  │  ├── Gradient                                                        │ │
│  │  ├── Görsel (bulanıklaştırma + overlay)                             │ │
│  │  └── Desen/pattern                                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  5. STİL DETAYLARI                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Border radius:                                                      │ │
│  │  ├── Sharp (0-2px)                                                  │ │
│  │  ├── Rounded (6-12px)                                               │ │
│  │  └── Pill (9999px - tam yuvarlak)                                   │ │
│  │                                                                       │ │
│  │  Shadow intensity:                                                   │ │
│  │  ├── None (flat design)                                             │ │
│  │  ├── Subtle                                                         │ │
│  │  ├── Medium                                                         │ │
│  │  └── Strong (elevated)                                              │ │
│  │                                                                       │ │
│  │  Animasyon:                                                         │ │
│  │  ├── Kapalı                                                         │ │
│  │  ├── Minimal (sadece geçişler)                                      │ │
│  │  └── Full (tüm mikro-etkileşimler)                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  6. ÖNİZLEME & KAYDET                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Canlı önizleme:                                                     │ │
│  │  ├── Desktop görünümü                                               │ │
│  │  ├── Tablet görünümü                                                │ │
│  │  ├── Mobil görünümü                                                 │ │
│  │  └── Dark mode toggle                                               │ │
│  │                                                                       │ │
│  │  Aksiyon butonları:                                                  │ │
│  │  ├── "Kaydet" (değişiklikleri uygula)                               │ │
│  │  ├── "Sıfırla" (preset'e geri dön)                                  │ │
│  │  └── "İptal" (son kaydedilene dön)                                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. UED (USER EXPERIENCE DESIGN) YAKLAŞIMI

### 4.1 Bilişsel Yük Yönetimi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BİLİŞSEL YÜK AZALTMA STRATEJİLERİ                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HICK'S LAW (Karar Süresi):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Seçenek sayısı arttıkça karar süresi logaritmik artar.              │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Kategori başına max 7±2 ürün görünür (chunking)                │ │
│  │  ├── Modifier grupları 5 seçeneği geçmemeli                         │ │
│  │  ├── Navigasyon max 5-7 ana öğe                                     │ │
│  │  ├── Önerilen/popüler ile seçimi kolaylaştır                        │ │
│  │  └── "Chef's Pick", "En Çok Satan" ile yönlendir                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  MILLER'S LAW (Working Memory):                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Kısa süreli bellek 7±2 öğe tutabilir.                               │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Formlar max 7 alan (gruplandırılmış)                           │ │
│  │  ├── Adım göstergeleri (1/3, 2/3...)                                │ │
│  │  ├── Sepet özeti her zaman görünür                                  │ │
│  │  ├── Progress bar ile ilerleme belli                                │ │
│  │  └── Otomatik kaydetme (form kaybı önleme)                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FITTS'S LAW (Tıklama Kolaylığı):                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Hedef büyük ve yakın = Daha hızlı erişim                            │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Primary butonlar büyük (52px+ yükseklik)                       │ │
│  │  ├── Sık kullanılan aksiyonlar thumb zone'da                        │ │
│  │  ├── "Sepete Ekle" her zaman erişilebilir                           │ │
│  │  ├── Modal kapatma butonu köşede + backdrop tıklama                 │ │
│  │  └── Floating action button kritik aksiyonlar için                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PROGRESSIVE DISCLOSURE (Kademeli Açılım):                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Önce temel, detay lazım olunca göster.                              │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Ürün kartı: İsim + fiyat + resim (temel)                       │ │
│  │  │   └── Tıkla: Açıklama, alerjen, besin, varyant (detay)          │ │
│  │  ├── Sipariş: Hızlı form (temel)                                    │ │
│  │  │   └── "Daha fazla seçenek" accordion'da                          │ │
│  │  ├── Ayarlar: Sık kullanılanlar üstte                               │ │
│  │  │   └── Gelişmiş ayarlar gizli/accordion                           │ │
│  │  └── Raporlar: Özet önce, "Detaylı Görüntüle" sonra                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Görsel Hiyerarşi İlkeleri

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GÖRSEL HİYERARŞİ KURALLARI                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Z-PATTERN (Tarama Örüntüsü):                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Batı okuma yönünde göz hareketi Z şeklinde.                         │ │
│  │                                                                       │ │
│  │  ┌──────────────────────────────────────────┐                        │ │
│  │  │  1 (Logo)  ─────────────────►  2 (CTA)   │                        │ │
│  │  │       \                           /      │                        │ │
│  │  │        \                         /       │                        │ │
│  │  │         \                       /        │                        │ │
│  │  │          \                     /         │                        │ │
│  │  │  3 (Content) ──────────────► 4 (Action) │                        │ │
│  │  └──────────────────────────────────────────┘                        │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Logo sol üst, ana aksiyon sağ üst                              │ │
│  │  ├── Ana içerik ortada                                              │ │
│  │  ├── Kritik CTA sağ alt veya merkez alt                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  F-PATTERN (İçerik Okuma):                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Metin ağırlıklı sayfalarda F şeklinde tarama.                       │ │
│  │                                                                       │ │
│  │  Uygulama:                                                           │ │
│  │  ├── Önemli bilgi sol tarafa hizalı                                 │ │
│  │  ├── Başlıklar sol başlangıçta                                      │ │
│  │  ├── Önemli kelimeler cümle başında                                 │ │
│  │  └── Alt satırlar daha az okunur - kritik bilgi üstte              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CONTRAST & SIZE:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Önem sırası = Görsel ağırlık sırası                                 │ │
│  │                                                                       │ │
│  │  1. En önemli:  En büyük, en koyu, en kontrastlı                    │ │
│  │  2. İkincil:    Orta boy, gri tonları                               │ │
│  │  3. Destekleyici: Küçük, açık, secondary color                      │ │
│  │                                                                       │ │
│  │  Örnek - Ürün kartı:                                                │ │
│  │  ├── 1. Ürün adı (24px, bold, siyah)                               │ │
│  │  ├── 2. Fiyat (20px, semibold, brand color)                        │ │
│  │  ├── 3. Açıklama (14px, regular, gri)                              │ │
│  │  └── 4. Alerjen ikonları (12px, subtle)                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  WHITE SPACE (Negatif Alan):                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Boşluk = Lüks, nefes alma, odaklanma                               │ │
│  │                                                                       │ │
│  │  Kurallar:                                                           │ │
│  │  ├── İlişkili öğeler birbirine yakın (proximity)                    │ │
│  │  ├── Farklı gruplar arası belirgin boşluk                           │ │
│  │  ├── Padding: İçerik konteynerde nefes almalı                       │ │
│  │  ├── Margin: Bölümler arası yeterli ayrım                           │ │
│  │  └── Kalabalık his = Kalitesiz his (önle)                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Duygu Tasarımı (Emotional Design)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     DUYGU TASARIMI PRENSİPLERİ                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DON NORMAN'IN 3 SEVİYESİ:                                                  │
│                                                                             │
│  1. VISCERAL (İçgüdüsel):                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  İlk izlenim - "Vay, güzel görünüyor!"                               │ │
│  │                                                                       │ │
│  │  Etkileyenler:                                                       │ │
│  │  ├── Renk paleti (sıcak = iştah, soğuk = ferahlik)                  │ │
│  │  ├── Görsel kalite (fotoğraf çözünürlüğü)                           │ │
│  │  ├── Tipografi estetiği                                             │ │
│  │  ├── Boşluk ve düzen                                                │ │
│  │  └── Animasyonların akıcılığı                                       │ │
│  │                                                                       │ │
│  │  Hedef: "Bu profesyonel görünüyor, güvenebilirim"                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  2. BEHAVIORAL (Davranışsal):                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Kullanım deneyimi - "Bu kolay ve hızlı!"                            │ │
│  │                                                                       │ │
│  │  Etkileyenler:                                                       │ │
│  │  ├── Görev tamamlama hızı                                           │ │
│  │  ├── Hata oranı düşüklüğü                                           │ │
│  │  ├── Öğrenme kolaylığı                                              │ │
│  │  ├── Geri bildirim netliği                                          │ │
│  │  └── Tutarlı davranış                                               │ │
│  │                                                                       │ │
│  │  Hedef: "Tam istediğim gibi çalışıyor"                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  3. REFLECTIVE (Yansıtıcı):                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Uzun vadeli his - "Bunu kullanmaktan memnunum"                      │ │
│  │                                                                       │ │
│  │  Etkileyenler:                                                       │ │
│  │  ├── Marka algısı                                                   │ │
│  │  ├── Prestij ve statü                                               │ │
│  │  ├── Kişiselleştirme                                                │ │
│  │  ├── Hikaye ve anlam                                                │ │
│  │  └── Sosyal kabul                                                   │ │
│  │                                                                       │ │
│  │  Hedef: "Bu benim/bizim işletmemize yakışıyor"                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  YEMEK SEKTÖRÜNE ÖZEL DUYGUSAL TASARIM:                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  İştah Açma:                                                         │ │
│  │  ├── Sıcak renkler (kırmızı, turuncu, sarı)                         │ │
│  │  ├── Yüksek kalite yemek fotoğrafları                               │ │
│  │  ├── Yakın çekim, doku görünür                                      │ │
│  │  └── Buhar, taze görünüm                                            │ │
│  │                                                                       │ │
│  │  Güven Oluşturma:                                                   │ │
│  │  ├── Temiz, düzenli arayüz                                          │ │
│  │  ├── Net fiyatlandırma                                              │ │
│  │  ├── Alerjen/besin bilgisi şeffaflığı                              │ │
│  │  └── Değerlendirme/yorumlar                                         │ │
│  │                                                                       │ │
│  │  Aciliyet Yaratma (dikkatli kullanım):                              │ │
│  │  ├── "Popüler", "Tükeniyor" etiketleri                             │ │
│  │  ├── Sınırlı süre kampanyaları                                     │ │
│  │  └── Canlı sipariş sayacı (opsiyonel)                              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. TEKNOLOJİ YAKLAŞIMI

### 5.1 CSS Mimarisi Prensipleri

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CSS MİMARİSİ YAKLAŞIMI                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  YAKLAŞIM: Tailwind CSS + CSS Custom Properties Hybrid                      │
│                                                                             │
│  NEDEN BU YAKLAŞIM:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Tailwind Avantajları:                                               │ │
│  │  ├── Utility-first: Hızlı geliştirme                                │ │
│  │  ├── Tutarlılık: Spacing, color scale sabit                         │ │
│  │  ├── Purge: Kullanılmayan CSS otomatik temizlenir                   │ │
│  │  ├── Responsive: Breakpoint prefix'leri (sm:, md:, lg:)             │ │
│  │  └── Dark mode: dark: prefix ile kolay                              │ │
│  │                                                                       │ │
│  │  CSS Variables Avantajları:                                          │ │
│  │  ├── Runtime theming: JavaScript ile değiştirilebilir               │ │
│  │  ├── Marka renkleri: Dinamik atanabilir                             │ │
│  │  ├── Erişilebilirlik modları: Anlık değişim                         │ │
│  │  └── Cascade: Doğal CSS özelliği                                    │ │
│  │                                                                       │ │
│  │  Hybrid Yaklaşım:                                                    │ │
│  │  ├── Tailwind: Layout, spacing, typography utility                  │ │
│  │  ├── CSS Variables: Renkler, theme values, brand                   │ │
│  │  └── Component CSS: Karmaşık component'lar için                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DOSYA YAPISI YAKLAŞIMI:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  styles/                                                             │ │
│  │  ├── base/                                                          │ │
│  │  │   ├── reset.css         # Normalize/reset                        │ │
│  │  │   ├── typography.css    # Font tanımları                         │ │
│  │  │   └── accessibility.css # A11y mode stilleri                     │ │
│  │  │                                                                   │ │
│  │  ├── tokens/                                                        │ │
│  │  │   ├── colors.css        # Renk değişkenleri                      │ │
│  │  │   ├── spacing.css       # Spacing scale                          │ │
│  │  │   ├── typography.css    # Type scale                             │ │
│  │  │   └── shadows.css       # Gölge değişkenleri                     │ │
│  │  │                                                                   │ │
│  │  ├── themes/                                                        │ │
│  │  │   ├── default.css       # Platform varsayılan                    │ │
│  │  │   ├── dark.css          # Dark mode override                     │ │
│  │  │   ├── high-contrast.css # Yüksek kontrast                       │ │
│  │  │   └── presets/          # Tema presetleri                        │ │
│  │  │       ├── modern-minimal.css                                     │ │
│  │  │       ├── classic-elegant.css                                    │ │
│  │  │       └── ...                                                    │ │
│  │  │                                                                   │ │
│  │  ├── components/                                                    │ │
│  │  │   ├── buttons.css                                                │ │
│  │  │   ├── cards.css                                                  │ │
│  │  │   ├── forms.css                                                  │ │
│  │  │   └── ...                                                        │ │
│  │  │                                                                   │ │
│  │  └── main.css              # Import hub                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  KURAL: Component CSS Yerine Tailwind Tercih Et                             │
│  ├── Basit component: Tailwind class'ları yeterli                          │
│  ├── Karmaşık state: @apply ile Tailwind kullan                            │
│  └── Çok karmaşık: Component CSS (nadir)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 JavaScript Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      JAVASCRIPT MİMARİSİ YAKLAŞIMI                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRENSİP: Minimal JS, Progressive Enhancement                               │
│                                                                             │
│  YAKLAŞIM:                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1. ÖNCE CSS:                                                        │ │
│  │     CSS ile yapılabilecek her şeyi CSS ile yap.                     │ │
│  │     ├── Hover/focus states: CSS :hover, :focus                      │ │
│  │     ├── Transitions: CSS transition                                 │ │
│  │     ├── Simple animations: CSS @keyframes                           │ │
│  │     ├── Toggles: :checked + sibling selector                        │ │
│  │     └── Details/summary: Native HTML                                │ │
│  │                                                                       │ │
│  │  2. SONRA ALPINE.JS:                                                │ │
│  │     Interaktif durumlar için Alpine.js tercih et.                   │ │
│  │     ├── Dropdown menus                                              │ │
│  │     ├── Modals                                                      │ │
│  │     ├── Tabs                                                        │ │
│  │     ├── Accordions                                                  │ │
│  │     ├── Form validation (client-side)                               │ │
│  │     └── Cart management                                             │ │
│  │                                                                       │ │
│  │  3. GEREKİRSE VANILLA JS:                                           │ │
│  │     Alpine.js'in yetersiz kaldığı durumlar için.                    │ │
│  │     ├── Karmaşık form işlemleri                                     │ │
│  │     ├── File upload                                                 │ │
│  │     ├── Canvas/WebGL                                                │ │
│  │     └── Third-party entegrasyonlar                                  │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  NEDEN ALPINE.JS:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Küçük boyut (~15KB minified)                                   │ │
│  │  ├── No build step (CDN'den yükle, çalışır)                         │ │
│  │  ├── HTML içinde deklaratif (x-data, x-show, x-on)                  │ │
│  │  ├── SSR uyumlu (EJS ile mükemmel çalışır)                          │ │
│  │  ├── Öğrenmesi kolay (Vue.js benzeri syntax)                        │ │
│  │  └── Tailwind ile ideal kombinasyon                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  JS DOSYA YAPISI YAKLAŞIMI:                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  public/js/                                                          │ │
│  │  ├── vendor/               # Third-party (CDN fallback)             │ │
│  │  │   ├── alpine.min.js                                              │ │
│  │  │   └── htmx.min.js       # (Opsiyonel, AJAX için)                 │ │
│  │  │                                                                   │ │
│  │  ├── utils/                # Utility fonksiyonlar                   │ │
│  │  │   ├── accessibility.js  # A11y helpers                           │ │
│  │  │   ├── storage.js        # LocalStorage wrapper                   │ │
│  │  │   └── validation.js     # Form validation                        │ │
│  │  │                                                                   │ │
│  │  ├── components/           # Component behaviors                    │ │
│  │  │   ├── cart.js           # Sepet yönetimi                        │ │
│  │  │   ├── theme-switcher.js # Tema değiştirme                       │ │
│  │  │   └── image-viewer.js   # Galeri lightbox                       │ │
│  │  │                                                                   │ │
│  │  └── app.js                # Ana başlatma dosyası                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ERİŞİLEBİLİRLİK JS GEREKSİNİMLERİ:                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ├── Focus management (modal açılınca focus içine, kapanınca geri)  │ │
│  │  ├── Keyboard navigation (arrow keys, escape, enter)                │ │
│  │  ├── Screen reader announcements (aria-live regions)                │ │
│  │  ├── Reduced motion respect (prefers-reduced-motion)                │ │
│  │  └── Focus trap (modal içinde Tab döngüsü)                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 İkon Sistemi Yaklaşımı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       İKON SİSTEMİ YAKLAŞIMI                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ÖNCELİK SIRASI:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Phosphor Icons (Birincil)                                        │ │
│  │     ├── 6 ağırlık: Thin, Light, Regular, Bold, Fill, Duotone        │ │
│  │     ├── 6000+ ikon                                                   │ │
│  │     ├── MIT lisansı                                                  │ │
│  │     ├── Tutarlı stil                                                │ │
│  │     └── CSS/SVG/Web Component seçenekleri                           │ │
│  │                                                                       │ │
│  │  2. FontAwesome (Yedek)                                              │ │
│  │     ├── Phosphor'da olmayan ikonlar için                            │ │
│  │     ├── Sadece Free tier                                            │ │
│  │     └── Brand ikonları (sosyal medya vb.)                           │ │
│  │                                                                       │ │
│  │  3. Custom SVG                                                       │ │
│  │     ├── Marka spesifik ikonlar                                      │ │
│  │     ├── Özel illüstrasyonlar                                        │ │
│  │     └── Inline SVG olarak kullan                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  İKON KULLANIM KURALLARI:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Erişilebilirlik:                                                    │ │
│  │  ├── Dekoratif ikon: aria-hidden="true"                             │ │
│  │  ├── Anlamlı ikon: aria-label veya sr-only metin                    │ │
│  │  ├── Buton ikonu: Buton'da aria-label veya visible text             │ │
│  │  └── Link ikonu: Link metnine ek bilgi olarak                       │ │
│  │                                                                       │ │
│  │  Boyutlandırma:                                                      │ │
│  │  ├── Inline text: 1em (metinle orantılı)                            │ │
│  │  ├── Buton ikonu: 20-24px                                           │ │
│  │  ├── Nav ikonu: 24-28px                                             │ │
│  │  └── Hero/empty state: 48-64px                                      │ │
│  │                                                                       │ │
│  │  Renklendirme:                                                       │ │
│  │  ├── currentColor kullan (parent'tan miras)                         │ │
│  │  ├── Hover durumunda parent ile değişir                             │ │
│  │  └── Disabled: opacity ile soluklaştır                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CDN KULLANIMI:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Phosphor: https://unpkg.com/@phosphor-icons/web                     │ │
│  │  FontAwesome: https://cdnjs.cloudflare.com/ajax/libs/font-awesome   │ │
│  │                                                                       │ │
│  │  Fallback: Local kopyalar /public/fonts/ altında                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. KALİTE GÜVENCESİ

### 6.1 Tasarım Review Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TASARIM REVIEW CHECKLIST                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HER COMPONENT/SAYFA İÇİN:                                                  │
│                                                                             │
│  GÖRSEL KALİTE:                                                             │
│  [ ] Görsel hiyerarşi net (neyin önemli olduğu belli)                      │
│  [ ] White space yeterli (sıkışık his yok)                                 │
│  [ ] Alignment doğru (grid/guide'lara uyuyor)                              │
│  [ ] Renk kullanımı tutarlı (design token'lardan)                          │
│  [ ] Tipografi ölçeği doğru (scale'den sapma yok)                          │
│  [ ] İkonlar tutarlı (aynı stil ailesi)                                    │
│                                                                             │
│  ERİŞİLEBİLİRLİK:                                                           │
│  [ ] Kontrast oranları geçer (4.5:1 text, 3:1 UI)                          │
│  [ ] Touch target yeterli (48px minimum)                                   │
│  [ ] Focus durumu görünür                                                  │
│  [ ] Renk tek başına bilgi taşımıyor                                       │
│  [ ] Başlık hiyerarşisi mantıklı (h1 > h2 > h3...)                        │
│  [ ] Form elemanları labeled                                               │
│  [ ] Hata mesajları net ve yapıcı                                          │
│                                                                             │
│  RESPONSIVE:                                                                │
│  [ ] Mobile görünüm kontrol edildi                                         │
│  [ ] Tablet görünüm kontrol edildi                                         │
│  [ ] Desktop görünüm kontrol edildi                                        │
│  [ ] Breakpoint geçişleri akıcı                                            │
│  [ ] Metin okunabilir her boyutta                                          │
│                                                                             │
│  THEMING:                                                                   │
│  [ ] Dark mode çalışıyor                                                   │
│  [ ] Brand renkleri değişince bozulmuyor                                   │
│  [ ] High contrast modunda görünür                                         │
│                                                                             │
│  PERFORMANS:                                                                │
│  [ ] Gereksiz CSS yok                                                      │
│  [ ] Animasyonlar GPU-accelerated (transform/opacity)                      │
│  [ ] Görseller optimize                                                    │
│  [ ] Font subset kullanılıyor                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Bu döküman, E-Menum tasarım felsefesini ve yaklaşımlarını tanımlar. Tüm UI geliştirmeleri bu prensipler çerçevesinde yapılmalıdır.*
