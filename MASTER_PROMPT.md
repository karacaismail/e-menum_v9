# E-Menum Master Prompt

> **Bu dosya, AI agent'a (Claude, GPT, vb.) projeyi tanıtmak için kullanılır.**  
> Tüm referans dosyaları @ mention ile listelenmiştir.  
> Agent bu dosyayı okuyarak projenin kapsamını, sınırlarını ve yapısını anlar.

---

## PROJE TANIMI

**E-Menum**, Türkiye F&B sektörü için **enterprise-ready, scale edilmiş** bir QR menü ve restoran yönetim platformudur.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ⚠️  BU PROJE MVP DEĞİLDİR                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Bu proje:                                                                  │
│  ├── Enterprise-ready altyapı ile tasarlanmıştır                           │
│  ├── Scale edilebilir modüler mimari kullanır                              │
│  ├── Sadece 2 modül (menu, order) tam implement edilir                     │
│  ├── Diğer 10+ modül sonradan eklenmek üzere STUB olarak tanımlıdır       │
│  ├── Tüm core sistem (auth, org, user, vb.) production-ready olmalıdır    │
│  └── WordPress plugin sistemi benzeri dinamik modül yükleme destekler      │
│                                                                             │
│  Yaklaşım: "Önce sağlam temel, sonra özellikler"                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## REFERANS DOSYALARI

### Önce Oku (Kapsam & Kısıtlar)

| Dosya | Amaç |
|-------|------|
| @CONSTRAINTS.md | **Yapılmaması gerekenler**, sınırlar, anti-patterns |
| @MVP_SCOPE.md | **Net kapsam**, hangi modüller var/yok, tier limitleri |
| @MODULE_SYSTEM.md | **Modül mimarisi**, lifecycle, aktivasyon mekanizması |
| @MODULE_DEVELOPMENT_GUIDE.md | **Yeni modül nasıl geliştirilir**, adım adım rehber |

### Proje Bağlamı

| Dosya | Amaç |
|-------|------|
| @CLAUDE.md | **Master reference**, tek sayfalık proje özeti |
| @PROJECT_CONTEXT.md | **İş bağlamı**, hedefler, metrikler, ekip |
| @GLOSSARY.md | **Terminoloji**, domain terimleri, kısaltmalar |

### Mimari

| Dosya | Amaç |
|-------|------|
| @SYSTEM_DESIGN.md | **C4 model**, deployment, request lifecycle |
| @DATABASE_SCHEMA.md | **ERD**, 25+ entity, multi-tenancy, migration policy |
| @API_CONTRACTS.md | **REST conventions**, 70+ endpoint, webhook events |
| @SECURITY_MODEL.md | **5-layer security**, JWT, RBAC/ABAC, audit logging |

### Standartlar

| Dosya | Amaç |
|-------|------|
| @CODING_STANDARDS.md | **TypeScript conventions**, Git workflow, naming |
| @TESTING_STRATEGY.md | **Test pyramid**, coverage targets, CI/CD integration |
| @COMPONENT_PATTERNS.md | **WCAG 2.1**, design tokens, accessibility patterns |

### Domain

| Dosya | Amaç |
|-------|------|
| @BUSINESS_RULES.md | **İş kuralları**, pricing, validation, workflows |

### Design

| Dosya | Amaç |
|-------|------|
| @DESIGN_SYSTEM_PHILOSOPHY.md | **UED yaklaşımı**, theming, accessibility modes |
| @PERSONA_USER_FLOWS.md | **Personalar**, sektör bazlı UI, kritik akışlar |
| @FRONTEND_ARCHITECTURE.md | **CSS/JS mimarisi**, Alpine.js, Tailwind, build |

### Module Specs

| Dosya | Amaç |
|-------|------|
| @specs/001-menu-module/spec.md | **Menu modülü** tam spesifikasyonu |
| @specs/001-menu-module/requirements.json | **Yapılandırılmış gereksinimler** |
| @specs/001-menu-module/context.json | **AI/vibecoding context** |

---

## MODÜL DURUMU

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MODÜL DURUMU                                        │
├────────────────────┬──────────┬─────────────────────────────────────────────┤
│ Modül              │ Durum    │ Açıklama                                    │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ CORE (8 modül)     │ ✅ FULL  │ auth, organization, branch, user, media,   │
│                    │          │ notification, subscription, module-loader   │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ menu               │ ✅ FULL  │ Dijital menü - TAM İMPLEMENT               │
│ order              │ ✅ FULL  │ Sipariş sistemi - TAM İMPLEMENT            │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ advanced-example   │ ✅ FULL  │ Modül geliştirme referansı                 │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ payment            │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ analytics          │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ ai                 │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ campaign           │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ loyalty            │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ inventory          │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ reservation        │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ feedback           │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ integration        │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ pos                │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ kitchen-display    │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
│ table-management   │ 📝 STUB  │ Sadece interface, sonradan geliştirilecek  │
└────────────────────┴──────────┴─────────────────────────────────────────────┘

STUB = Interface/types tanımlı, implementation YOK, modül sistemi hazır
```

---

## TEMA DURUMU

```
┌────────────────────┬──────────┬─────────────────────────────────────────────┐
│ Tema               │ Durum    │ Açıklama                                    │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ admin-theme        │ ✅ FULL  │ Admin panel teması (tek)                    │
│ product-theme      │ ✅ FULL  │ Müşteri menü teması (varsayılan)           │
│ example-theme      │ ✅ FULL  │ Tema geliştirme referansı                  │
├────────────────────┼──────────┼─────────────────────────────────────────────┤
│ Ek temalar         │ ❌ YOK   │ Sonradan eklenecek                         │
└────────────────────┴──────────┴─────────────────────────────────────────────┘
```

---

## KRİTİK KURALLAR

```yaml
YAPILACAKLAR:
  ✅ Core sistem enterprise-ready olmalı
  ✅ Modül sistemi WordPress plugin gibi dinamik olmalı
  ✅ Stub modüller için sadece interface tanımlanmalı
  ✅ Her kod multi-tenant olmalı (organizationId filtresi)
  ✅ Tüm API'lar versiyonlu olmalı (/api/v1/)
  ✅ Test coverage %80+ olmalı
  ✅ WCAG 2.1 AA uyumlu olmalı

YAPILMAYACAKLAR:
  ❌ Stub modüllerin implementation'ı
  ❌ Ek tema geliştirme
  ❌ Kapsam dışı özellikler (çoklu para birimi, native app, vb.)
  ❌ React/Vue/Angular (EJS + Alpine.js only)
  ❌ GraphQL (REST only)
  ❌ MongoDB (PostgreSQL only)
  ❌ Global state kullanımı
  ❌ Modüller arası doğrudan import
```

---

## GELİŞTİRME SIRASI

```
1. CORE SYSTEM
   └── auth → organization → user → branch → media → notification → subscription → module-loader

2. ENTERPRISE MODULES
   └── menu → order

3. THEMES
   └── admin-theme → product-theme → example-theme

4. STUB DEFINITIONS
   └── Tüm gelecek modüller için interface/types
```

---

## AI AGENT TALİMATLARI

```yaml
Geliştirme yaparken:
  1. Önce @CONSTRAINTS.md oku - sınırları bil
  2. Önce @MVP_SCOPE.md oku - kapsamı bil
  3. İlgili spec dosyasını oku (varsa)
  4. @CODING_STANDARDS.md'e uygun kod yaz
  5. @TESTING_STRATEGY.md'e uygun test yaz

Yeni modül geliştirirken:
  1. @MODULE_DEVELOPMENT_GUIDE.md'i takip et
  2. Mevcut enterprise modülleri referans al (menu, order)
  3. Modül bağımsızlığını koru (event-driven communication)

Asla yapma:
  - Stub modülü implement etme (interface dışında)
  - Kapsam dışı özellik ekleme
  - Başka modülün internal dosyasını import etme
  - Test yazmadan PR açma
```

---

## DOSYA YAPISI ÖZETİ

```
.auto-claude/
├── MASTER_PROMPT.md              ← BU DOSYA (giriş noktası)
├── CLAUDE.md                     ← Master reference
├── CONSTRAINTS.md                ← ⚠️ Kısıtlamalar
├── MVP_SCOPE.md                  ← ⚠️ Kapsam
├── MODULE_SYSTEM.md              ← Modül mimarisi
├── MODULE_DEVELOPMENT_GUIDE.md   ← Modül geliştirme rehberi
├── PROJECT_CONTEXT.md            ← İş bağlamı
│
├── architecture/
│   ├── SYSTEM_DESIGN.md          ← C4, deployment
│   ├── DATABASE_SCHEMA.md        ← ERD, entities
│   ├── API_CONTRACTS.md          ← REST endpoints
│   └── SECURITY_MODEL.md         ← Auth, RBAC/ABAC
│
├── domain/
│   ├── BUSINESS_RULES.md         ← İş kuralları
│   └── GLOSSARY.md               ← Terminoloji
│
├── standards/
│   ├── CODING_STANDARDS.md       ← Kod standartları
│   ├── TESTING_STRATEGY.md       ← Test stratejisi
│   └── COMPONENT_PATTERNS.md     ← UI patterns
│
├── design/
│   ├── DESIGN_SYSTEM_PHILOSOPHY.md ← UED, theming
│   ├── PERSONA_USER_FLOWS.md     ← Personalar, akışlar
│   └── FRONTEND_ARCHITECTURE.md  ← CSS/JS mimari
│
└── specs/
    └── 001-menu-module/
        ├── spec.md               ← Tam spesifikasyon
        ├── requirements.json     ← Yapılandırılmış req
        └── context.json          ← AI context

TOPLAM: 21 dosya, ~17,000 satır dokümantasyon
```

---

## ÖZET

> **E-Menum = Enterprise-Ready Core + 2 Full Module + 12 Stub Module + 3 Theme**
> 
> Temel hazır, modüller takılabilir.
> WordPress gibi plugin sistemi, ama type-safe ve enterprise-grade.

---

*Bu prompt, AI agent'ın E-Menum projesini tam olarak anlaması için gerekli tüm referansları içerir. Geliştirmeye başlamadan önce ilgili dosyaları okuyun.*
