# E-Menum Constraints & Boundaries

> **Auto-Claude Constraint Document**  
> Bu dosya, projenin KESİN SINIRLARINI tanımlar.  
> Vibecoding sırasında bu kısıtlar İHLAL EDİLMEMELİDİR.  
> Son Güncelleme: 2026-01-31

---

## 1. KAPSAM SINIRLAMALARI (SCOPE BOUNDARIES)

### 1.1 MVP Kapsamı - SADECE BUNLAR

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MVP KAPSAMI - YAPILACAKLAR                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE SYSTEM (Sistem Çekirdeği):                                           │
│  ├── auth          → Kimlik doğrulama, oturum yönetimi                     │
│  ├── organization  → İşletme/tenant yönetimi                               │
│  ├── branch        → Şube yönetimi                                         │
│  ├── user          → Kullanıcı yönetimi, roller                            │
│  ├── media         → Dosya/görsel yönetimi                                 │
│  ├── notification  → Bildirim sistemi                                      │
│  ├── subscription  → Abonelik/faturalama                                   │
│  └── module-loader → Modül yükleme/etkinleştirme sistemi                   │
│                                                                             │
│  ENTERPRISE-READY MODULES (Tam Geliştirilen):                              │
│  ├── menu-module   → Dijital menü yönetimi (001)                           │
│  └── order-module  → Sipariş alma ve yönetimi (002)                        │
│                                                                             │
│  THEMES (Temalar):                                                          │
│  ├── admin-theme   → Admin panel teması (tek tema)                         │
│  ├── product-theme → Müşteri menü teması (varsayılan)                      │
│  └── example-theme → Örnek/referans tema                                   │
│                                                                             │
│  REFERENCE (Referans):                                                      │
│  └── advanced-example-module → Modül geliştirme örneği                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 MVP DIŞI - YAPILMAYACAKLAR

```
┌─────────────────────────────────────────────────────────────────────────────┐
│            ⛔ MVP DIŞI - KESİNLİKLE GELİŞTİRİLMEYECEK                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MODÜLLER (Sadece stub/interface tanımlanacak):                            │
│  ├── ❌ payment-module      → Ödeme entegrasyonu                           │
│  ├── ❌ analytics-module    → Analitik ve raporlama                        │
│  ├── ❌ ai-module           → AI içerik üretimi                            │
│  ├── ❌ campaign-module     → Kampanya yönetimi                            │
│  ├── ❌ loyalty-module      → Sadakat programı                             │
│  ├── ❌ inventory-module    → Stok yönetimi                                │
│  ├── ❌ reservation-module  → Rezervasyon sistemi                          │
│  ├── ❌ feedback-module     → Müşteri geri bildirimi                       │
│  ├── ❌ integration-module  → 3rd party entegrasyonlar                     │
│  └── ❌ pos-module          → PoS entegrasyonu                             │
│                                                                             │
│  ÖZELLİKLER:                                                                │
│  ├── ❌ Çoklu ödeme gateway entegrasyonu                                   │
│  ├── ❌ WhatsApp/SMS entegrasyonu                                          │
│  ├── ❌ Mutfak ekranı (Kitchen Display)                                    │
│  ├── ❌ Masa yönetimi                                                       │
│  ├── ❌ Garson çağırma sistemi                                             │
│  ├── ❌ Çoklu para birimi desteği (TRY only)                               │
│  ├── ❌ Franchise yönetimi                                                  │
│  ├── ❌ Marketplace                                                         │
│  ├── ❌ White-label çözüm                                                   │
│  └── ❌ Native mobil uygulama                                              │
│                                                                             │
│  TEMALAR:                                                                   │
│  ├── ❌ Ek admin temaları                                                   │
│  ├── ❌ Premium müşteri temaları                                           │
│  └── ❌ Tema marketplace                                                    │
│                                                                             │
│  NOT: Bu özellikler için SADECE interface/stub tanımlanır.                 │
│  Implementation yapılmaz, ancak modül sistemi hazır olur.                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MİMARİ KISITLAMALAR

### 2.1 Modül Kuralları

```yaml
MODÜL SINIRLAMALARI:

Toplam Modül Sayısı:
  - Core modules: 8 (auth, org, branch, user, media, notification, subscription, module-loader)
  - Enterprise modules: 2 (menu, order)
  - Example modules: 1 (advanced-example)
  - TOPLAM: 11 modül
  - Yeni modül eklenirse: MODULE_DEVELOPMENT_GUIDE.md takip edilmeli

Modül Bağımsızlığı:
  - Her modül kendi klasöründe izole
  - Modüller arası doğrudan import YASAK
  - İletişim sadece: Events, Shared Contracts, Core Services
  - Circular dependency YASAK

Modül Boyutu:
  - Tek modül 50+ dosyadan büyük olmamalı
  - Büyürse: Alt modüllere bölünmeli
  - Tek dosya 500 satırı geçmemeli

Modül State:
  - Global state YASAK
  - Her modül kendi state'ini yönetir
  - Cross-module state: Event-driven veya Core service üzerinden
```

### 2.2 Tema Kuralları

```yaml
TEMA SINIRLAMALARI:

Tema Sayısı:
  - Admin theme: 1 (admin-theme)
  - Product themes: 1 varsayılan (product-theme) + 1 örnek (example-theme)
  - TOPLAM: 3 tema
  - Yeni tema: TEMA_DEVELOPMENT_GUIDE.md takip edilmeli (oluşturulacak)

Tema Kapsamı:
  - Tema sadece görsel katman (CSS, assets, layout)
  - Tema iş mantığı içermez
  - Tema veritabanı erişimi yapmaz
  - Tema API çağrısı yapmaz (data, component'e prop olarak gelir)

Tema Dosya Yapısı:
  themes/
  ├── admin-theme/           # Admin panel
  │   ├── theme.json         # Manifest
  │   ├── assets/
  │   ├── layouts/
  │   ├── components/
  │   └── styles/
  ├── product-theme/         # Varsayılan müşteri teması
  └── example-theme/         # Referans tema

Tema Değişkenleri:
  - Tüm renkler CSS variable olmalı
  - Hardcoded renk YASAK
  - Tema arası geçiş runtime'da mümkün olmalı
```

### 2.3 Veritabanı Kısıtları

```yaml
VERİTABANI SINIRLAMALARI:

ORM:
  - SADECE Prisma kullanılacak
  - Raw SQL YASAK (istisnai performans durumları hariç, onay gerekli)
  - Query builder YASAK

Migration:
  - Her değişiklik migration ile
  - Manuel schema değişikliği YASAK
  - Production'da down migration YASAK

Tablo İsimlendirme:
  - snake_case (örn: menu_items)
  - Modül prefix'i YASAK (menu_menu_items değil, menu_items)
  - Plural (items, not item)

İlişkiler:
  - Foreign key zorunlu
  - Cascade delete dikkatli kullanılmalı (soft delete tercih)
  - Many-to-many için junction table

Index:
  - Her FK için index
  - Sık sorgulanan alanlar için index
  - Composite index 3 alandan fazla olmamalı
```

### 2.4 API Kısıtları

```yaml
API SINIRLAMALARI:

Versiyonlama:
  - URL path versioning: /api/v1/...
  - Sadece v1 geliştirilecek
  - v2 planlanmayacak (ihtiyaç olunca düşünülür)

Endpoint Sayısı:
  - Modül başına max 30 endpoint
  - Toplam max 150 endpoint (MVP)
  - Gereksiz endpoint eklenmeyecek

Response Format:
  - SADECE JSON
  - XML desteği YOK
  - GraphQL YOK (REST only)

Authentication:
  - SADECE JWT Bearer
  - API Key sadece webhook'lar için
  - OAuth provider olarak değil, consumer olarak (Google login vb.)

Rate Limiting:
  - Public endpoints: 60/dakika
  - Authenticated: 300/dakika
  - Webhook: 10/dakika
```

---

## 3. KOD KISITLAMALARI

### 3.1 Dil ve Framework

```yaml
TEKNOLOJİ SINIRLAMALARI:

Backend:
  ✅ İZİN VERİLEN:
    - Node.js (LTS)
    - TypeScript (strict mode)
    - Express.js
    - Prisma ORM
    - Zod validation
    - ioredis
    - bullmq (queues)
  
  ⛔ YASAK:
    - NestJS, Fastify, Koa (Express only)
    - TypeORM, Sequelize, Knex (Prisma only)
    - Yup, Joi (Zod only)
    - MongoDB, DynamoDB (PostgreSQL only)
    - GraphQL, gRPC (REST only)

Frontend:
  ✅ İZİN VERİLEN:
    - EJS templates
    - Tailwind CSS
    - Alpine.js
    - Vite
    - HTMX (opsiyonel)
  
  ⛔ YASAK:
    - React, Vue, Angular, Svelte
    - Next.js, Nuxt, SvelteKit
    - SCSS, LESS, Styled Components
    - jQuery
    - Bootstrap, Material UI

Genel:
  ⛔ YASAK:
    - Any tipi (TypeScript)
    - Console.log (logger kullan)
    - Callback hell (async/await kullan)
    - var keyword (const/let)
    - == operatörü (=== kullan)
```

### 3.2 Kod Organizasyonu

```yaml
DOSYA YAPISI KISITLAMALARI:

Modül Yapısı (Zorunlu):
  src/modules/{module-name}/
  ├── index.ts              # ZORUNLU: Public exports
  ├── {name}.module.ts      # ZORUNLU: Module definition
  ├── {name}.controller.ts  # ZORUNLU: HTTP handlers
  ├── {name}.service.ts     # ZORUNLU: Business logic
  ├── {name}.repository.ts  # ZORUNLU: Data access
  ├── {name}.schema.ts      # ZORUNLU: Validation
  ├── {name}.types.ts       # ZORUNLU: TypeScript types
  ├── {name}.routes.ts      # ZORUNLU: Route definitions
  ├── {name}.events.ts      # Opsiyonel: Event handlers
  ├── {name}.constants.ts   # Opsiyonel: Constants
  └── __tests__/            # ZORUNLU: Tests

Yasak Yapılar:
  ❌ src/controllers/        # Modül dışı controller
  ❌ src/services/           # Modül dışı service
  ❌ src/models/             # Modül dışı model
  ❌ src/helpers/            # helpers yerine utils/
  ❌ src/lib/                # lib yerine core/
  ❌ Barrel exports (index.ts'de re-export hariç)

İsimlendirme:
  - Dosya: kebab-case (menu-item.service.ts)
  - Sınıf: PascalCase (MenuItemService)
  - Fonksiyon/değişken: camelCase (getMenuItem)
  - Sabit: SCREAMING_SNAKE_CASE (MAX_ITEMS)
  - Type/Interface: PascalCase (MenuItem)
  - Enum: PascalCase (MenuStatus)
```

### 3.3 Import Kuralları

```yaml
IMPORT KISITLAMALARI:

İzin Verilen Import Yolları:
  ✅ @/core/*           → Core modüllerden
  ✅ @/shared/*         → Shared utilities
  ✅ @/modules/{name}   → Modül public API'den (index.ts)
  ✅ External packages  → node_modules

Yasak Import Yolları:
  ❌ ../../../          → Göreceli derin import
  ❌ @/modules/{name}/{internal-file}  → Modül internal dosyasından
  ❌ require()          → CommonJS require (ES import kullan)

Modüller Arası İletişim:
  ✅ Event emit/listen   → Gevşek bağlılık
  ✅ Shared contracts    → Interface tanımları
  ✅ Core services       → Ortak servisler üzerinden
  ❌ Direct import       → Doğrudan bağımlılık YASAK

Örnek:
  // ✅ DOĞRU
  import { MenuService } from '@/modules/menu';
  import { EventBus } from '@/core/events';
  
  // ❌ YANLIŞ
  import { validateMenuItem } from '@/modules/menu/menu.schema';
  import { MenuRepository } from '@/modules/menu/menu.repository';
```

---

## 4. GÜVENLİK KISITLAMALARI

### 4.1 Kesin Güvenlik Kuralları

```yaml
GÜVENLİK SINIRLAMALARI:

Kimlik Doğrulama:
  - Her API endpoint'te auth middleware ZORUNLU (public hariç)
  - Public endpoint'ler açıkça işaretlenmeli
  - JWT secret minimum 256-bit
  - Token expiry: access 15dk, refresh 7gün

Yetkilendirme:
  - Her mutation'da RBAC kontrolü ZORUNLU
  - Tenant isolation her query'de ZORUNLU
  - Admin endpoint'leri ayrı route prefix (/admin/...)

Input Validation:
  - Tüm input Zod ile validate edilmeli
  - Validation hatası detaylı response
  - File upload: whitelist extension, magic byte check

Output Sanitization:
  - HTML escape tüm user-generated content
  - JSON response'da sensitive field olmamalı (password, token)

YASAK PATTERN'LER:
  ❌ eval(), new Function()
  ❌ innerHTML (textContent kullan)
  ❌ SQL string concatenation
  ❌ Hardcoded secrets
  ❌ console.log sensitive data
  ❌ Error message'da stack trace (prod'da)
```

### 4.2 Veri Koruma

```yaml
VERİ KORUMA KISITLAMALARI:

Kişisel Veri:
  - PII loglanmaz
  - PII cache'lenmez (veya encrypted)
  - Silme talebi 30 gün içinde işlenir

Şifreleme:
  - Şifreler bcrypt (cost 12)
  - Sensitive data at-rest: AES-256
  - Transit: TLS 1.3 only

Loglama:
  - Request body loglanmaz (sadece endpoint, user, status)
  - Passwords, tokens, API keys ASLA loglanmaz
  - Log retention: 90 gün

Backup:
  - Daily automated backup
  - Encryption at rest
  - Cross-region replication (production)
```

---

## 5. PERFORMANS KISITLAMALARI

### 5.1 Response Time Limitleri

```yaml
PERFORMANS SINIRLAMALARI:

API Response Time (p95):
  - GET (single): < 100ms
  - GET (list): < 200ms
  - POST/PATCH: < 300ms
  - DELETE: < 200ms
  - File upload: < 5s
  - Bulk operations: < 2s

Database Query:
  - Single query: < 50ms
  - Complex join: < 100ms
  - N+1 query YASAK

Frontend:
  - LCP: < 2.5s
  - FID: < 100ms
  - CLS: < 0.1
  - Bundle size (gzipped): CSS < 30KB, JS < 50KB
```

### 5.2 Kaynak Limitleri

```yaml
KAYNAK SINIRLAMALARI:

Memory:
  - Node process: max 512MB (production)
  - Redis: max 1GB
  - Query result: max 10,000 rows

Concurrent:
  - DB connections: max 20 per instance
  - Redis connections: max 10 per instance
  - Worker threads: max 4

File:
  - Upload size: max 10MB
  - Image dimensions: max 4000x4000
  - Batch upload: max 10 files
```

---

## 6. TEST KISITLAMALARI

### 6.1 Zorunlu Test Kuralları

```yaml
TEST SINIRLAMALARI:

Coverage:
  - Minimum: 80% line coverage
  - Critical paths: 100%
  - Yeni kod: coverage düşürmemeli

Test Türleri (Zorunlu):
  - Unit tests: Her service method
  - Integration tests: Her API endpoint
  - E2E tests: Kritik user flow'lar

Test Türleri (Yasak):
  ❌ Snapshot tests (kırılgan)
  ❌ Sleep/delay based tests
  ❌ Production DB'ye bağlı testler
  ❌ Network-dependent tests (mock kullan)

Naming:
  - Test file: {name}.test.ts veya {name}.spec.ts
  - Test case: "should {expected behavior} when {condition}"

CI/CD:
  - PR merge: Tüm testler geçmeli
  - Main branch: %80 coverage altına düşmemeli
  - Deploy: E2E testler geçmeli
```

---

## 7. GELİŞTİRME SÜRECİ KISITLAMALARI

### 7.1 Git Kuralları

```yaml
GIT SINIRLAMALARI:

Branch Naming:
  ✅ feature/{ticket}-{description}
  ✅ fix/{ticket}-{description}
  ✅ hotfix/{description}
  ✅ chore/{description}
  ❌ Türkçe karakter
  ❌ Boşluk, özel karakter

Commit:
  - Conventional commits ZORUNLU
  - Max 72 karakter başlık
  - Body opsiyonel ama detaylı olmalı
  
  ✅ feat(menu): add variant support
  ✅ fix(order): resolve stock calculation
  ❌ fixed bug
  ❌ WIP
  ❌ asdasd

PR:
  - Squash merge ZORUNLU (main'e)
  - 1 approval minimum
  - CI geçmeli
  - Conflict olmamalı

Yasak:
  ❌ Force push to main
  ❌ Direct commit to main
  ❌ Merge commit (squash kullan)
  ❌ 1000+ satır PR (bölünmeli)
```

### 7.2 Dokümantasyon Kuralları

```yaml
DOKÜMANTASYON SINIRLAMALARI:

Zorunlu Docs:
  - Her modül: README.md
  - Her public API: JSDoc
  - Her complex function: inline comment
  - Mimari kararlar: ADR (Architecture Decision Record)

Format:
  - Markdown only
  - Mermaid for diagrams
  - English for code comments
  - Turkish for user-facing docs

Güncelleme:
  - Kod değişince doc da güncellenmeli
  - Outdated doc'dan kod yazmak YASAK
  - PR'da doc review zorunlu
```

---

## 8. YAPILMAMASI GEREKEN ANTI-PATTERNS

### 8.1 Kod Anti-Patterns

```yaml
YASAK PATTERN'LER:

Architecture:
  ❌ God class (500+ satır)
  ❌ Circular dependency
  ❌ Service locator pattern
  ❌ Singleton abuse
  ❌ Anemic domain model
  
Code:
  ❌ Magic numbers (constant tanımla)
  ❌ String typing ("admin" yerine enum)
  ❌ Nested callbacks (3+ level)
  ❌ Long parameter list (5+ param → object kullan)
  ❌ Feature envy (başka sınıfın datasını çok kullanma)
  
Database:
  ❌ N+1 queries
  ❌ SELECT * (explicit columns)
  ❌ Missing indexes on FK
  ❌ Storing JSON for queryable data
  ❌ Soft delete without index on deleted_at

API:
  ❌ Verb in URL (/api/getUsers → /api/users)
  ❌ Inconsistent naming
  ❌ Missing pagination
  ❌ Exposing internal IDs unnecessarily
  ❌ Over-fetching (return only needed fields)

Frontend:
  ❌ Inline styles
  ❌ !important
  ❌ Deep CSS nesting (3+ level)
  ❌ Non-semantic HTML
  ❌ Missing alt text
```

### 8.2 İş Mantığı Anti-Patterns

```yaml
İŞ MANTIĞI YASAK PATTERN'LER:

❌ Hardcoded business rules:
   // YANLIŞ
   if (items.length > 25) throw new Error('Too many items');
   
   // DOĞRU
   if (items.length > TIER_LIMITS[org.tier].maxItems) {...}

❌ UI'da business logic:
   // Business logic service'de olmalı, template'de değil
   
❌ Controller'da business logic:
   // Controller sadece request/response handle etmeli
   
❌ Scattered validation:
   // Tüm validation tek yerde (schema)
   
❌ Magic strings for status:
   // Enum kullan
```

---

## 9. MODÜL GELİŞTİRME SINIRLAMALARI

### 9.1 Yeni Modül Ekleme Kuralları

```yaml
YENİ MODÜL EKLENİRKEN:

Ön Koşullar:
  1. MODULE_DEVELOPMENT_GUIDE.md okunmalı
  2. Modül interface'i tanımlanmalı (stub)
  3. Core team onayı alınmalı
  4. Capacity planning yapılmalı

Zorunlu Adımlar:
  1. src/modules/{name}/ klasörü oluştur
  2. {name}.module.ts ile manifest tanımla
  3. Prisma schema ekle
  4. Migration oluştur
  5. Routes register et
  6. Events register et
  7. Tests yaz
  8. README yaz

Yasak:
  ❌ Core modülleri değiştirmek
  ❌ Başka modülün internal'ına erişmek
  ❌ Global state eklemek
  ❌ Yeni dependency eklemek (onay gerekli)
```

### 9.2 Tema Ekleme Kuralları

```yaml
YENİ TEMA EKLENİRKEN:

Ön Koşullar:
  1. example-theme kopyalanmalı
  2. theme.json düzenlenmeli
  3. Tüm required component'lar implement edilmeli

Zorunlu Bileşenler:
  - theme.json (manifest)
  - layouts/default.ejs
  - components/header.ejs
  - components/footer.ejs
  - components/menu-item.ejs
  - styles/main.css

Yasak:
  ❌ JavaScript business logic
  ❌ API çağrısı
  ❌ Database erişimi
  ❌ Hardcoded text (i18n kullan)
```

---

## 10. CHECKLIST - VİBECODING ÖNCESİ KONTROL

```yaml
Her coding session öncesi kontrol et:

□ Doğru modülde miyim?
□ Bu özellik MVP kapsamında mı?
□ Modül sınırlarını aşıyor muyum?
□ Başka modüle doğrudan bağımlılık var mı?
□ Test yazdım mı?
□ Hardcoded değer var mı?
□ Security check yaptım mı?
□ Performance impact düşündüm mü?
□ Documentation güncel mi?

Eğer bunlardan biri "hayır" ise, DURMA ve düzelt.
```

---

## 11. İSTİSNA SÜRECİ

Eğer bir kısıtlamayı ihlal etmek ZORUNLU ise:

1. **Dokümante et**: Neden gerekli?
2. **ADR yaz**: Architecture Decision Record
3. **Onay al**: Tech lead onayı
4. **Geçici işaretle**: `// EXCEPTION: {ADR-XXX} - {reason}`
5. **Takip et**: Technical debt olarak track et
6. **Plan yap**: Ne zaman düzeltilecek?

```typescript
// EXCEPTION: ADR-003 - Performance critical, raw SQL used
// TODO: Refactor with Prisma when v5 supports window functions
const result = await prisma.$queryRaw`...`;
```

---

*Bu döküman, E-Menum projesinin KESİN SINIRLARINI tanımlar. Tüm geliştirmeler bu kısıtlara uygun olmalıdır.*
