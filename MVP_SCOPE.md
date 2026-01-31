# E-Menum MVP Scope Definition

> **Auto-Claude MVP Scope Document**  
> Bu döküman MVP'de NELER VAR ve NELER YOK'u kesin olarak tanımlar.  
> Vibecoding sırasında bu kapsam dışına çıkılmamalıdır.  
> Son Güncelleme: 2026-01-31

---

## 1. MVP VİZYONU

### 1.1 Tek Cümle

> **"Türkiye'deki restoran ve kafeler için QR kodlu dijital menü ve sipariş sistemi"**

### 1.2 MVP Hedefi

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MVP HEDEFİ                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  İşletme:                                                                   │
│  ├── Dijital menü oluşturabilir                                            │
│  ├── QR kod ile müşterilere sunabilir                                      │
│  ├── Sipariş alabilir                                                       │
│  └── Siparişleri yönetebilir                                               │
│                                                                             │
│  Müşteri:                                                                   │
│  ├── QR tarayarak menüyü görebilir                                         │
│  ├── Ürünleri inceleyebilir                                                │
│  └── Sipariş verebilir                                                      │
│                                                                             │
│  Sonuç: Minimum viable product ile market'a çıkış                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. KAPSAM MATRİSİ

### 2.1 Modüller

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MODÜL KAPSAM MATRİSİ                                    │
├────────────────────┬──────────┬──────────┬──────────────────────────────────┤
│ Modül              │ Durum    │ Tier     │ Açıklama                        │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ CORE MODULES (Sistem altyapısı - her zaman aktif)                          │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ auth               │ ✅ FULL  │ -        │ JWT auth, session, OAuth        │
│ organization       │ ✅ FULL  │ -        │ Tenant management               │
│ branch             │ ✅ FULL  │ -        │ Multi-branch support            │
│ user               │ ✅ FULL  │ -        │ User & role management          │
│ media              │ ✅ FULL  │ -        │ File/image management           │
│ notification       │ ✅ FULL  │ -        │ Email, in-app notifications     │
│ subscription       │ ✅ FULL  │ -        │ Plans, billing, limits          │
│ module-loader      │ ✅ FULL  │ -        │ Dynamic module system           │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ ENTERPRISE MODULES (Tam geliştirilen)                                       │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ menu               │ ✅ FULL  │ Free+    │ Dijital menü yönetimi           │
│ order              │ ✅ FULL  │ Starter+ │ Sipariş alma ve yönetimi        │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ EXAMPLE MODULES (Referans)                                                  │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ advanced-example   │ ✅ FULL  │ -        │ Modül geliştirme örneği         │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ STUB MODULES (Sadece interface, implementation yok)                         │
├────────────────────┼──────────┼──────────┼──────────────────────────────────┤
│ payment            │ 📝 STUB  │ Pro+     │ Ödeme entegrasyonu              │
│ analytics          │ 📝 STUB  │ Pro+     │ Raporlama & analitik            │
│ ai                 │ 📝 STUB  │ Pro+     │ AI içerik üretimi               │
│ campaign           │ 📝 STUB  │ Business+│ Kampanya yönetimi               │
│ loyalty            │ 📝 STUB  │ Business+│ Sadakat programı                │
│ inventory          │ 📝 STUB  │ Business+│ Stok yönetimi                   │
│ reservation        │ 📝 STUB  │ Pro+     │ Rezervasyon sistemi             │
│ feedback           │ 📝 STUB  │ Starter+ │ Müşteri geri bildirimi          │
│ integration        │ 📝 STUB  │ Enterpr. │ 3rd party entegrasyonlar        │
│ pos                │ 📝 STUB  │ Enterpr. │ PoS entegrasyonu                │
│ kitchen-display    │ 📝 STUB  │ Business+│ Mutfak ekranı                   │
│ table-management   │ 📝 STUB  │ Pro+     │ Masa yönetimi                   │
└────────────────────┴──────────┴──────────┴──────────────────────────────────┘

Durum Açıklamaları:
✅ FULL  = Tam implement edilecek, production-ready
📝 STUB  = Sadece interface/types, implementation yok
```

### 2.2 Temalar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEMA KAPSAM MATRİSİ                                    │
├────────────────────┬──────────┬──────────────────────────────────────────────┤
│ Tema               │ Durum    │ Açıklama                                    │
├────────────────────┼──────────┼──────────────────────────────────────────────┤
│ admin-theme        │ ✅ FULL  │ Admin panel teması (tek tema)               │
│ product-theme      │ ✅ FULL  │ Varsayılan müşteri menü teması             │
│ example-theme      │ ✅ FULL  │ Tema geliştirme örneği/referans             │
├────────────────────┼──────────┼──────────────────────────────────────────────┤
│ Ek temalar         │ ❌ YOK   │ MVP sonrası                                 │
│ Tema marketplace   │ ❌ YOK   │ MVP sonrası                                 │
│ Custom tema upload │ ❌ YOK   │ MVP sonrası (Enterprise için düşünülebilir) │
└────────────────────┴──────────┴──────────────────────────────────────────────┘
```

---

## 3. ÖZELLİK DETAYLARI

### 3.1 Menu Module Features

```yaml
MVP'DE VAR (✅):
  Temel:
    - Menü oluşturma/düzenleme/silme
    - Kategori yönetimi (3 seviye hiyerarşi)
    - Ürün yönetimi (CRUD)
    - Görsel yükleme (max 3/ürün Free, 5/ürün Pro+)
    - Çoklu dil (TR, EN)
    - QR kod oluşturma
    - Menü yayınlama/yayından alma

  Ürün Detayları:
    - Fiyatlandırma (TRY)
    - Varyantlar (boyut, tip)
    - Seçenekler (ekstralar)
    - Alerjen bilgileri (14 standart)
    - Diyet etiketleri (vegan, helal, vb.)
    - Stok durumu (mevcut/tükendi)

  Admin:
    - Drag & drop sıralama
    - Toplu stok güncelleme
    - Arama/filtreleme

  Müşteri:
    - Responsive menü görüntüleme
    - Kategori navigasyonu
    - Ürün detay modal
    - Alerjen filtreleme
    - Dil değiştirme

MVP'DE YOK (❌):
    - Çoklu para birimi (sadece TRY)
    - Zamanlı görünürlük (kahvaltı menüsü sadece sabah)
    - Besin değerleri detayı
    - Menü versiyonlama/rollback
    - Bulk import/export (CSV/Excel)
    - AI açıklama üretimi
    - Dinamik fiyatlandırma
    - Happy hour pricing
```

### 3.2 Order Module Features

```yaml
MVP'DE VAR (✅):
  Sipariş Alma:
    - Sepete ekleme
    - Varyant/seçenek seçimi
    - Miktar ayarlama
    - Sipariş notu
    - Sepet özeti

  Sipariş Yönetimi:
    - Sipariş listesi (admin)
    - Sipariş detayı
    - Durum güncelleme (pending → preparing → ready → completed)
    - Sipariş geçmişi

  Bildirimler:
    - Yeni sipariş bildirimi (admin)
    - Sipariş durumu değişikliği (müşteri - in-app)

MVP'DE YOK (❌):
    - Online ödeme (payment modülü stub)
    - Masa bazlı sipariş
    - Garson çağırma
    - Mutfak ekranı
    - Sipariş yazdırma
    - SMS/WhatsApp bildirimi
    - Kurye entegrasyonu
    - Paket sipariş takibi
```

### 3.3 Core Features

```yaml
AUTH (✅ FULL):
  - Email/password login
  - JWT tokens (access + refresh)
  - Password reset
  - Email verification
  - Google OAuth (müşteri için opsiyonel)
  ❌ 2FA (post-MVP)
  ❌ SSO (post-MVP)
  ❌ Magic link login (post-MVP)

ORGANIZATION (✅ FULL):
  - Tenant oluşturma
  - Temel bilgiler (isim, logo, iletişim)
  - Çalışma saatleri
  - Sosyal medya linkleri
  ❌ Multi-organization (tek org/kullanıcı)
  ❌ Organization transfer
  ❌ White label

BRANCH (✅ FULL):
  - Şube oluşturma
  - Şube bilgileri
  - Şubeye menü atama
  - Şube bazlı QR kod
  ❌ Şube gruplaması
  ❌ Bölge yönetimi

USER (✅ FULL):
  - Kullanıcı davet etme
  - Rol atama (owner, manager, staff, viewer)
  - Temel profil yönetimi
  ❌ Detaylı izin yönetimi (rol bazlı yeterli)
  ❌ Activity logging (basit audit var)

SUBSCRIPTION (✅ FULL):
  - 5 tier: Free, Starter, Professional, Business, Enterprise
  - Feature gating
  - Usage limits
  - Deneme süresi (14 gün)
  ❌ Otomatik ödeme (manual invoice)
  ❌ Usage-based billing
  ❌ Add-ons
```

---

## 4. TEKNİK KAPSAM

### 4.1 Backend

```yaml
MVP'DE VAR (✅):
  - Node.js + TypeScript + Express
  - PostgreSQL + Prisma ORM
  - Redis (caching, sessions)
  - JWT authentication
  - Role-based access control
  - Input validation (Zod)
  - Error handling
  - Logging (structured)
  - Rate limiting
  - CORS configuration
  - File upload (local + S3 ready)

MVP'DE YOK (❌):
  - GraphQL (REST only)
  - Real-time (WebSocket) - sadece polling
  - Message queue (BullMQ hazır ama minimal kullanım)
  - Full-text search (Elasticsearch)
  - Multi-region deployment
```

### 4.2 Frontend

```yaml
MVP'DE VAR (✅):
  - Server-rendered (EJS)
  - Tailwind CSS
  - Alpine.js (minimal JS)
  - Mobile-responsive
  - Dark mode (admin)
  - Accessibility (WCAG 2.1 AA)

MVP'DE YOK (❌):
  - SPA framework (React/Vue)
  - Offline support (PWA)
  - Native mobile app
  - Real-time updates (auto-refresh)
```

### 4.3 Infrastructure

```yaml
MVP'DE VAR (✅):
  - Single region deployment
  - Basic monitoring
  - Automated backups
  - SSL/HTTPS
  - CDN for static assets

MVP'DE YOK (❌):
  - Multi-region
  - Auto-scaling
  - Blue-green deployment
  - Advanced APM
  - Chaos engineering
```

---

## 5. SAYISAL LİMİTLER

### 5.1 Sistem Limitleri

```yaml
MVP Limitleri:

Performans:
  - API response: p95 < 200ms
  - Page load: < 3s
  - Concurrent users: 1000/tenant

Veri:
  - Max organizations: 1000 (MVP döneminde)
  - Max branches/org: 50
  - Max menus/org: 10
  - Max items/menu: 500
  - Max images/item: 5
  - Max file size: 5MB
  - Max total storage/org: 1GB

API:
  - Rate limit (authenticated): 300/dakika
  - Rate limit (public): 60/dakika
  - Max request body: 10MB
```

### 5.2 Tier Limitleri

```yaml
Free:
  - 1 menü
  - 5 kategori
  - 25 ürün
  - 2 görsel/ürün
  - 1 şube
  - 1 kullanıcı
  - E-Menum branding

Starter (₺2,000/ay):
  - 3 menü
  - 20 kategori
  - 100 ürün
  - 3 görsel/ürün
  - 3 şube
  - 5 kullanıcı
  - Sipariş modülü
  - Branding kaldırma

Professional (₺4,000/ay):
  - 5 menü
  - 50 kategori
  - 300 ürün
  - 5 görsel/ürün
  - 10 şube
  - 15 kullanıcı
  - Varyantlar & seçenekler
  - Çoklu dil (5 dil)

Business (₺6,000/ay):
  - 10 menü
  - 100 kategori
  - 500 ürün
  - 5 görsel/ürün
  - 25 şube
  - 30 kullanıcı
  - Tüm diller
  - Öncelikli destek

Enterprise (₺8,000/ay):
  - Sınırsız menü
  - Sınırsız kategori
  - Sınırsız ürün
  - 10 görsel/ürün
  - Sınırsız şube
  - Sınırsız kullanıcı
  - Özel özellikler
  - Dedicated destek
```

---

## 6. ZAMAN ÇİZELGESİ

### 6.1 MVP Fazları

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MVP DEVELOPMENT TIMELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: Foundation (Hafta 1-2)                                           │
│  ├── Core system setup                                                     │
│  ├── Auth module                                                           │
│  ├── Organization/User modules                                             │
│  └── Module loader system                                                  │
│                                                                             │
│  PHASE 2: Menu Module (Hafta 3-5)                                          │
│  ├── Menu CRUD                                                             │
│  ├── Category management                                                   │
│  ├── Item management                                                       │
│  ├── Image upload                                                          │
│  ├── Public menu display                                                   │
│  └── QR code generation                                                    │
│                                                                             │
│  PHASE 3: Order Module (Hafta 6-8)                                         │
│  ├── Cart system                                                           │
│  ├── Order placement                                                       │
│  ├── Order management                                                      │
│  └── Notifications                                                         │
│                                                                             │
│  PHASE 4: Polish & Launch (Hafta 9-10)                                     │
│  ├── Admin UI refinement                                                   │
│  ├── Theme finalization                                                    │
│  ├── Testing & bug fixes                                                   │
│  ├── Documentation                                                         │
│  └── Deployment                                                            │
│                                                                             │
│  TOTAL: ~10 hafta (2.5 ay)                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. POST-MVP ROADMAP

### 7.1 Öncelik Sırası

```yaml
Phase 1 (Post-MVP, Q2):
  - Payment module implementation
  - Analytics module (basic)
  - SMS/WhatsApp notifications

Phase 2 (Q3):
  - AI module (description generation)
  - Kitchen display
  - Table management

Phase 3 (Q4):
  - Loyalty program
  - Campaign management
  - Advanced analytics

Phase 4 (Next Year):
  - Inventory management
  - POS integration
  - Native mobile app
```

---

## 8. KARAR AĞACI

### 8.1 "Bu özellik MVP'de mi?" Kontrolü

```
Özellik isteği geldiğinde:

1. Bu özellik olmadan ürün çalışır mı?
   ├── HAYIR → MVP'de olmalı
   └── EVET → Adım 2'ye git

2. Bu özellik ilk 10 müşteriyi kazanmak için gerekli mi?
   ├── EVET → MVP'de olmalı
   └── HAYIR → Adım 3'e git

3. Bu özellik rakiplerden farklılaşma sağlıyor mu?
   ├── EVET → Değerlendir (nice-to-have)
   └── HAYIR → MVP'de OLMAMALI

4. Bu özellik 2 haftadan kısa sürede yapılabilir mi?
   ├── EVET → Değerlendir
   └── HAYIR → MVP'de OLMAMALI, post-MVP'ye ekle
```

---

## 9. ÖZET TABLOSU

| Kategori | MVP'de | Post-MVP |
|----------|--------|----------|
| **Core Modules** | 8 | - |
| **Feature Modules** | 2 (menu, order) | 10+ |
| **Themes** | 3 | 5+ |
| **Diller** | 2 (TR, EN) | 10+ |
| **Para Birimi** | 1 (TRY) | 5+ |
| **Ödeme Gateway** | 0 (manual) | 3+ |
| **AI Özellikleri** | 0 | 5+ |
| **Mobile App** | 0 (responsive web) | 2 (iOS, Android) |

---

*Bu döküman MVP kapsamını kesin olarak tanımlar. Kapsam dışı özellik talepleri post-MVP backlog'a eklenir.*
