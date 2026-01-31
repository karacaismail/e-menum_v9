# E-Menum - Enterprise QR Menu SaaS

> **Auto-Claude Master Reference Document**  
> Bu dosya, Auto-Claude agent'ın projeyi anlaması için tek yetkili kaynaktır.  
> Son Güncelleme: 2026-01-31

---

## 1. PRODUCT OVERVIEW

### 1.1 Ürün Tanımı

E-Menum, restoran ve kafelere yönelik yapay zeka destekli dijital menü platformudur. Temel değer önerisi: **"Akıllı menüler, veri odaklı kararlar."**

| Özellik | Değer |
|---------|-------|
| **Hedef Pazar** | Türkiye F&B sektörü (350.000+ işletme) |
| **Hedef Segment** | Kafeler, restoranlar, zincir işletmeler |
| **Fiyatlandırma** | Freemium + 4 ücretli tier (₺2K-8K/ay) |
| **Diferansiyatör** | AI-powered içerik üretimi, analitik, tahminleme |

### 1.2 Hedef Kullanıcı Rolleri

| Rol | Organizasyon İçi | Sorumluluk |
|-----|------------------|------------|
| `owner` | Evet | Tam yetki, fatura, abonelik |
| `manager` | Evet | Menü, sipariş, personel yönetimi |
| `staff` | Evet | Sipariş alma, masa yönetimi |
| `viewer` | Evet | Salt okunur dashboard |

| Rol | Platform (Sistem) | Sorumluluk |
|-----|-------------------|------------|
| `super_admin` | Platform | Tam sistem yetkisi |
| `admin` | Platform | Müşteri, fatura, destek |
| `sales` | Platform | CRM, lead yönetimi |
| `support` | Platform | Destek ticket'ları |

| Rol | Public | Sorumluluk |
|-----|--------|------------|
| `customer` | Hayır | Menü görüntüleme, sipariş |
| `anonymous` | Hayır | Sadece public menü |

---

## 2. TECH STACK

### 2.1 Backend

```yaml
Runtime:        Node.js 20+ LTS
Framework:      Express.js 4.x
Language:       TypeScript 5.x (strict mode)
ORM:            Prisma 6.x
Database:       PostgreSQL 15+
Cache:          Redis 7.x
Queue:          BullMQ (Redis-based)
```

### 2.2 Libraries

```yaml
Routing:        routing-controllers (decorator-based)
DI Container:   tsyringe (Microsoft)
Validation:     Zod (runtime + TypeScript inference)
Auth:           JWT + bcrypt + Passport
Authorization:  CASL (ABAC/RBAC)
Events:         EventEmitter2
i18n:           i18next
```

### 2.3 Frontend

```yaml
Template:       EJS 3.x (SSR)
CSS:            Tailwind CSS 3.4.x
Components:     Flowbite (Tailwind component library)
Icons:          Phosphor Icons (CDN) - priority
                FontAwesome (fallback)
Interactivity:  Alpine.js 3.x
Charts:         Chart.js / ApexCharts
```

### 2.4 Deployment

```yaml
Server:         Hetzner VPS (CX21+)
PaaS:           Coolify (self-hosted)
Process:        PM2 Cluster mode
Proxy:          Nginx (reverse proxy)
SSL:            Let's Encrypt (auto-renewal)
CI/CD:          GitHub Actions → Coolify webhook
```

---

## 3. CRITICAL RULES (KESİNLİKLE KIRILMAMALI)

### 3.1 Multi-Tenancy

```
RULE: Her query'de organizationId ZORUNLU

✅ DOĞRU:
await prisma.menu.findMany({ 
  where: { organizationId: ctx.organization.id } 
});

❌ YANLIŞ:
await prisma.menu.findMany(); // TÜM TENANT VERİLERİ!
```

### 3.2 Authorization

```
RULE: Her endpoint @Authorized decorator ile korunmalı

✅ DOĞRU:
@Authorized(['menu.view'])
@Get('/')
async getAll() {}

❌ YANLIŞ:
@Get('/') // Koruma yok!
async getAll() {}
```

### 3.3 Soft Delete

```
RULE: Hiçbir veri fiziksel silinmez

✅ DOĞRU:
await prisma.menu.update({
  where: { id },
  data: { deletedAt: new Date() }
});

❌ YANLIŞ:
await prisma.menu.delete({ where: { id } });
```

### 3.4 Import Alias

```
RULE: Tüm import'lar @/ alias kullanmalı

✅ DOĞRU:
import { BaseService } from '@/core/base/base.service';

❌ YANLIŞ:
import { BaseService } from '../../../core/base/base.service';
```

### 3.5 i18n Zorunluluğu

```
RULE: UI'da hardcoded string YASAK

✅ DOĞRU:
<%= t('menu.create.title') %>

❌ YANLIŞ:
<h1>Menü Oluştur</h1>
```

### 3.6 Error Handling

```
RULE: Tüm hatalar AppException ile fırlatılmalı

✅ DOĞRU:
throw new AppException('MENU_NOT_FOUND', 404);

❌ YANLIŞ:
throw new Error('Menu not found');
```

### 3.7 Validation

```
RULE: Tüm input'lar Zod schema ile validate edilmeli

✅ DOĞRU:
const schema = z.object({ name: z.string().min(1) });
const data = schema.parse(req.body);

❌ YANLIŞ:
const { name } = req.body; // Validation yok!
```

---

## 4. PROJECT STRUCTURE

```
src/
├── config/
│   ├── env.ts                    # Zod-validated environment
│   ├── database.ts               # Prisma client singleton
│   └── redis.ts                  # Redis client config
│
├── core/
│   ├── kernel/
│   │   ├── bootstrap.ts          # Application bootstrap
│   │   ├── container.ts          # DI container setup
│   │   └── module-loader.ts      # Module discovery & loading
│   │
│   ├── base/
│   │   ├── base.controller.ts    # CRUD controller template
│   │   ├── base.service.ts       # CRUD service template
│   │   └── base.repository.ts    # Repository pattern base
│   │
│   ├── middleware/
│   │   ├── auth.middleware.ts    # JWT verification
│   │   ├── tenant.middleware.ts  # Multi-tenant context
│   │   ├── permission.middleware.ts  # CASL ability check
│   │   ├── rate-limit.middleware.ts  # Rate limiting
│   │   └── error.middleware.ts   # Global error handler
│   │
│   ├── services/
│   │   ├── auth.service.ts       # Authentication logic
│   │   ├── permission.service.ts # CASL ability builder
│   │   ├── event.service.ts      # Domain events
│   │   └── installer.service.ts  # Module installer
│   │
│   └── exceptions/
│       ├── app.exception.ts      # Custom exception base
│       └── error-codes.ts        # Centralized error codes
│
├── modules/
│   ├── _system/                  # System modules (prefix: _)
│   │   ├── auth/
│   │   ├── users/
│   │   ├── organizations/
│   │   └── permissions/
│   │
│   ├── menu/                     # Feature module example
│   │   ├── manifest.json
│   │   ├── menu.controller.ts
│   │   ├── menu.service.ts
│   │   ├── dto/
│   │   │   ├── create-menu.dto.ts
│   │   │   └── update-menu.dto.ts
│   │   ├── menu.schema.prisma
│   │   └── menu.routes.ts
│   │
│   └── [other-modules]/
│
├── shared/
│   ├── abilities/                # CASL ability definitions
│   ├── decorators/               # Custom decorators
│   ├── guards/                   # Route guards
│   ├── utils/                    # Utility functions
│   └── types/                    # Shared TypeScript types
│
├── prisma/
│   ├── schema/                   # Multi-file schema (merged)
│   │   ├── base.prisma           # Datasource, generator
│   │   ├── core.prisma           # Core entities
│   │   └── [module].prisma       # Module-specific schemas
│   ├── migrations/
│   └── seed.ts
│
├── views/
│   ├── layouts/
│   │   └── main.ejs
│   ├── partials/
│   └── [module]/                 # Module-specific views
│
├── public/
│   ├── css/
│   ├── js/
│   └── images/
│
├── locales/
│   ├── tr/
│   └── en/
│
└── llms.txt                      # AI documentation (optional)
```

---

## 5. MODULE SYSTEM

### 5.1 Module Categories

| Kategori | Prefix | Örnek | Açıklama |
|----------|--------|-------|----------|
| System | `_system/` | `_system/users` | Core işlevler, kaldırılamaz |
| Feature | - | `menu`, `orders` | İş özellikleri |
| AI | `ai/` | `ai/content-gen` | AI-powered özellikler |
| Integration | `integrations/` | `integrations/pos` | 3rd party bağlantılar |

### 5.2 Module Manifest Schema

Her modül `manifest.json` dosyası içermelidir:

```json
{
  "name": "module-name",
  "displayName": "Human Readable Name",
  "version": "1.0.0",
  "description": "Module purpose",
  "author": "E-Menum",
  "category": "feature|system|ai|integration",
  "enabled": true,
  "priority": 100,
  
  "dependencies": {
    "required": ["organizations"],
    "optional": ["analytics"]
  },
  
  "permissions": [
    "module.view",
    "module.create", 
    "module.update",
    "module.delete"
  ],
  
  "routes": {
    "prefix": "/api/v1/module",
    "admin": "/admin/module"
  },
  
  "database": {
    "schema": "module.schema.prisma",
    "migrations": true
  },
  
  "hooks": {
    "onEnable": "hooks/on-enable.ts",
    "onDisable": "hooks/on-disable.ts"
  },
  
  "admin": {
    "menu": {
      "label": "i18n:module.menu.label",
      "icon": "ph-icon-name",
      "position": 50
    }
  },
  
  "events": {
    "emits": ["module.created", "module.updated"],
    "listens": ["organization.created"]
  },
  
  "planRestrictions": {
    "minPlan": "starter",
    "features": {
      "advancedFeature": "professional"
    }
  }
}
```

### 5.3 Module Lifecycle

```
discover → validate → resolve dependencies → load → register routes → ready
```

---

## 6. COMMANDS QUICK REFERENCE

### 6.1 Development

```bash
# Start dev server (hot reload)
npm run dev

# Type check
npm run type-check

# Lint
npm run lint
npm run lint:fix
```

### 6.2 Database

```bash
# Generate Prisma client
npm run prisma:generate

# Create migration
npm run prisma:migrate -- --name migration_name

# Apply migrations
npm run prisma:deploy

# Open Prisma Studio
npm run prisma:studio

# Merge multi-file schemas
npm run schema:merge
```

### 6.3 Modules

```bash
# Create new module scaffold
npm run module:create module-name

# Install module from zip
npm run module:install path/to/module.zip

# Enable/disable module
npm run module:enable module-name
npm run module:disable module-name
```

### 6.4 Build & Deploy

```bash
# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test
npm run test:coverage
```

---

## 7. ARCHITECTURE DECISIONS (ADRs)

### ADR-001: Express over NestJS

**Karar:** Express.js + routing-controllers + tsyringe kullanımı  
**Gerekçe:** 
- LLM training data'da daha fazla Express örneği
- Daha basit mental model
- NestJS'in %80'i, overhead'in %20'si

### ADR-002: EJS over React

**Karar:** Server-side EJS templates + Alpine.js  
**Gerekçe:**
- SEO-friendly SSR varsayılan
- Daha hızlı initial load
- Daha az bundle size
- Admin panel için yeterli interaktivite

### ADR-003: CASL for Authorization

**Karar:** CASL ABAC framework  
**Gerekçe:**
- Attribute-based access control esnekliği
- Tenant-scoped permissions
- Frontend + backend aynı ability tanımları

### ADR-004: Multi-file Prisma Schema

**Karar:** Her modül kendi .prisma dosyası  
**Gerekçe:**
- Modül bağımsızlığı
- Merge script ile tek schema'ya birleştirme
- Daha kolay maintenance

### ADR-005: Soft Delete Default

**Karar:** Tüm entity'lerde `deletedAt` timestamp  
**Gerekçe:**
- Veri kaybı önleme
- Audit trail
- GDPR uyumlu (gerçek silme prosedürü ayrı)

---

## 8. DOMAIN MODEL (Core Entities)

```
Organization (Tenant)
├── Users (many)
├── Menus (many)
│   ├── Categories (many)
│   │   └── Products (many)
│   │       ├── Variants (many)
│   │       ├── Modifiers (many)
│   │       └── Allergens (many-to-many)
│   └── Themes (many)
├── QRCodes (many)
├── Tables (many)
├── Orders (many)
│   └── OrderItems (many)
├── Customers (many)
└── Subscription (one)
    └── Plan (one)
```

---

## 9. API CONVENTIONS

### 9.1 URL Structure

```
/api/v1/{resource}              # Collection
/api/v1/{resource}/:id          # Single resource
/api/v1/{resource}/:id/{sub}    # Nested resource
```

### 9.2 Response Format

```json
// Success
{
  "success": true,
  "data": { ... }
}

// Success with pagination
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 150,
    "totalPages": 8
  }
}

// Error
{
  "success": false,
  "error": {
    "code": "MENU_NOT_FOUND",
    "message": "Menu with given ID not found",
    "details": { ... }
  }
}
```

### 9.3 HTTP Status Codes

| Code | Kullanım |
|------|----------|
| 200 | GET, PUT, PATCH başarılı |
| 201 | POST başarılı (resource created) |
| 204 | DELETE başarılı |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (no/invalid token) |
| 403 | Forbidden (no permission) |
| 404 | Not found |
| 422 | Unprocessable entity |
| 429 | Rate limited |
| 500 | Server error |

---

## 10. SECURITY REQUIREMENTS

### 10.1 Authentication

- JWT access token (15 min expiry)
- Refresh token (7 days, httpOnly cookie)
- Password: bcrypt, min 12 rounds

### 10.2 Authorization

- RBAC: Role-based baseline
- ABAC: Attribute-based fine-grained control
- Tenant isolation: organizationId her query'de

### 10.3 Data Protection

- Encryption at rest: PostgreSQL TDE
- Encryption in transit: TLS 1.3
- PII fields: encrypted with tenant-specific key

---

## 11. TESTING REQUIREMENTS

### 11.1 Coverage Targets

| Tür | Minimum |
|-----|---------|
| Unit | 80% |
| Integration | 60% |
| E2E | Critical paths |

### 11.2 Test File Locations

```
src/modules/menu/
├── menu.service.ts
├── menu.service.spec.ts        # Unit tests
├── menu.controller.spec.ts     # Unit tests
└── __tests__/
    └── menu.e2e.spec.ts        # E2E tests
```

---

## 12. VIBECODING PATTERNS

### 12.1 High Success Rate Patterns (>90%)

- Prisma CRUD operations
- Express middleware chains
- Zod validation schemas
- routing-controllers decorators
- CASL permission definitions
- EJS templates with partials

### 12.2 Always Specify in Prompts

```
1. "BaseController extend et"           → CRUD otomatik
2. "organizationId ile tenant filter"   → Multi-tenancy
3. "@Authorized decorator kullan"       → Yetkilendirme
4. "Zod schema ile validation"          → Tip güvenliği
5. "deletedAt ile soft delete"          → Veri koruma
6. "@/ alias kullan"                    → Import düzeni
```

### 12.3 Avoid in Prompts

- Custom abstractions without examples
- Magic strings
- `any` type
- Manual route definitions
- Circular dependencies

---

## 13. REFERENCE DOCUMENTS

### 13.1 Kapsam & Kısıtlamalar (ÖNCELİKLİ OKUMA)

| Döküman | Konum | İçerik |
|---------|-------|--------|
| **CONSTRAINTS.md** | .auto-claude/ | ⚠️ Kısıtlamalar, sınırlar, yapılmaması gerekenler |
| **MVP_SCOPE.md** | .auto-claude/ | ⚠️ MVP kapsamı, neler var/yok |
| **MODULE_SYSTEM.md** | .auto-claude/ | Modül mimarisi, lifecycle, aktivasyon |
| **MODULE_DEVELOPMENT_GUIDE.md** | .auto-claude/ | Yeni modül geliştirme rehberi |

### 13.2 Proje Bağlamı

| Döküman | Konum | İçerik |
|---------|-------|--------|
| PROJECT_CONTEXT.md | .auto-claude/ | Detaylı proje bağlamı |
| GLOSSARY.md | domain/ | Terminoloji, kısaltmalar |

### 13.3 Mimari

| Döküman | Konum | İçerik |
|---------|-------|--------|
| SYSTEM_DESIGN.md | architecture/ | C4 diagrams, data flow |
| DATABASE_SCHEMA.md | architecture/ | Entity relationships |
| API_CONTRACTS.md | architecture/ | Endpoint specifications |
| SECURITY_MODEL.md | security/ | Auth/authz details |

### 13.4 Standartlar

| Döküman | Konum | İçerik |
|---------|-------|--------|
| CODING_STANDARDS.md | standards/ | Code conventions |
| TESTING_STRATEGY.md | standards/ | Test approach |
| COMPONENT_PATTERNS.md | standards/ | UI component patterns |

### 13.5 Domain

| Döküman | Konum | İçerik |
|---------|-------|--------|
| BUSINESS_RULES.md | domain/ | Domain logic, pricing |

### 13.6 Design

| Döküman | Konum | İçerik |
|---------|-------|--------|
| DESIGN_SYSTEM_PHILOSOPHY.md | design/ | UED, theming, accessibility |
| PERSONA_USER_FLOWS.md | design/ | Personas, user journeys |
| FRONTEND_ARCHITECTURE.md | design/ | CSS/JS approach, build |

### 13.7 Module Specs

| Döküman | Konum | İçerik |
|---------|-------|--------|
| spec.md | specs/001-menu-module/ | Menu module specification |
| requirements.json | specs/001-menu-module/ | Structured requirements |
| context.json | specs/001-menu-module/ | AI/vibecoding context |

---

## 14. SPEC WRITING GUIDELINES

Her yeni özellik için `.auto-claude/specs/XXX-feature-name/` dizini oluştur:

1. `spec.md` - Feature specification
2. `requirements.json` - Structured requirements
3. `context.json` - Related files and references

Spec numaralama: `001`, `002`, ... (üç haneli, sıralı)

---

## 15. EMERGENCY CONTACTS

| Rol | İsim | Sorumluluk |
|-----|------|------------|
| Strategic Lead | İsmail | Mimari kararlar |
| Frontend | Ali | Istanbul bölge dev |
| Backend | Bora | Diğer bölge dev |
| DevOps | Ahmet | GTM, Mautic, infra |
| Sales | Pınar | Müşteri, destek |

---

*Bu döküman, Auto-Claude agent'ın E-Menum projesini anlayabilmesi için tek yetkili referanstır. Tüm spec'ler ve implementasyonlar bu dökümanla tutarlı olmalıdır.*
