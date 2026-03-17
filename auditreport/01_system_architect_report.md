# System Architect Audit Report

**Project:** E-Menum Enterprise QR Menu SaaS
**Date:** 2026-03-17
**SAFe Role:** System Architect
**Auditor:** E-Menum Engineering Team -- Automated Audit System
**Report Version:** 1.0.0

---

## Executive Summary

| Metric | Score |
|--------|-------|
| **Overall Architecture Health** | **82 / 100** |
| Technology Stack Fitness | 88 / 100 |
| Pattern Compliance | 85 / 100 |
| Scalability Readiness | 72 / 100 |
| Security Architecture | 84 / 100 |
| i18n Architecture | 80 / 100 |
| Deployment Architecture | 78 / 100 |

The E-Menum platform demonstrates a well-structured Django monolith following domain-driven design principles. The architecture employs 16 Django apps with clear separation of concerns, multi-tenant isolation through TenantFilterMixin, and a comprehensive soft-delete strategy. Key areas for improvement include the TenantMiddleware not yet being activated in the middleware chain, the absence of a connection pooler (PgBouncer), and the need for a CDN layer for static/media assets.

---

## 1. Technology Stack Assessment

| Component | Version | Rating | Notes |
|-----------|---------|--------|-------|
| Python | 3.13 | GREEN | Latest stable, excellent performance |
| Django | 5.0 | GREEN | Current LTS-compatible, well-maintained |
| DRF | 3.15 | GREEN | Mature REST framework |
| PostgreSQL | 15 | GREEN | Production-grade RDBMS |
| Redis | 7.x | GREEN | Cache + Celery broker, AOF persistence |
| Celery | 5.4 | GREEN | Production-grade async task processing |
| Gunicorn | 21.0+ | GREEN | gthread worker class configured |
| Alpine.js | 3.x | GREEN | Lightweight frontend interactivity |
| Tailwind CSS | 3.4.x | GREEN | Utility-first CSS, Flowbite components |
| Node.js | 20 | GREEN | LTS, used only for CSS build |
| WhiteNoise | 6.6+ | YELLOW | Good for moderate traffic, CDN needed for scale |
| python-magic | 0.4.27 | GREEN | MIME type validation for uploads |

**Stack Fitness Score: 88/100** -- Modern, well-chosen stack appropriate for the target market.

---

## 2. Architecture Pattern Analysis

### 2.1 Multi-Tenancy Pattern

**Implementation:** Organization-scoped tenant isolation via `TenantFilterMixin` in `shared/views/base.py`.

| Aspect | Status | Details |
|--------|--------|---------|
| TenantFilterMixin | IMPLEMENTED | `shared/views/base.py` lines 440-559 |
| Auto org-inject on create | IMPLEMENTED | `perform_create()` auto-injects `organization` |
| Empty queryset on no-org | IMPLEMENTED | Returns `queryset.none()` if no org context |
| TenantMiddleware | NOT ACTIVE | Commented out in `config/settings/base.py` line 204 |
| X-Organization-ID header | CONFIGURED | `EMENUM_TENANT_HEADER` in base.py line 816 |

**Finding ARCH-01 (MEDIUM):** TenantMiddleware at `shared/middleware/tenant.py` is commented out in the middleware chain (base.py line 204). Currently, organization context is set through view-level logic rather than a middleware injection. This is functional but inconsistent with CLAUDE.md Section 3.1 which states the middleware injects `request.organization`.

### 2.2 RBAC/ABAC Authorization

| Component | Location | Status |
|-----------|----------|--------|
| Role model | `apps/core/models.py` line 896 | IMPLEMENTED |
| Permission model | `apps/core/models.py` line 1020 | IMPLEMENTED |
| UserRole model | `apps/core/models.py` line 1259 | IMPLEMENTED |
| RolePermission model | `apps/core/models.py` line 1385 | IMPLEMENTED |
| django-guardian | `config/settings/base.py` line 145 | CONFIGURED |
| OrganizationScopedPermission | `shared/permissions/drf_permissions.py` | IMPLEMENTED |
| IsTenantMember | `shared/permissions/drf_permissions.py` | IMPLEMENTED |
| PlanEnforcementService | `shared/permissions/plan_enforcement.py` | IMPLEMENTED |

**Finding ARCH-02 (LOW):** The permission system is comprehensive with three layers -- RBAC (Role/Permission), ABAC (django-guardian), and Plan Enforcement. This is well-architected.

### 2.3 Domain-Driven App Architecture

The project contains **16 Django apps** organized by domain:

| Category | Apps | Model Count |
|----------|------|-------------|
| System/Core | core, accounts | 14 models (Organization, User, Branch, Role, Permission, Session, UserRole, RolePermission, AuditLog, Shift, StaffSchedule, StaffMetric + support models) |
| Feature | menu, orders, subscriptions, customers, inventory | 35 models |
| Analytics | analytics, reporting, dashboard | 9 models |
| AI | ai | 2 models (AIGeneration, AIProviderConfig) |
| Marketing | campaigns, website, seo, seo_shield | 15 models |
| Infrastructure | media, notifications | 3 models |
| **Total** | **16 apps** | **~78 models** |

### 2.4 Soft Delete Pattern

**Implementation:** `SoftDeleteMixin` defined in `apps/core/models.py` line 59, with `SoftDeleteManager` at line 45.

| Aspect | Status |
|--------|--------|
| SoftDeleteMixin base class | IMPLEMENTED -- `deleted_at` timestamp field |
| SoftDeleteManager | IMPLEMENTED -- auto-filters `deleted_at__isnull=True` |
| `all_objects` manager | REFERENCED in docstring but not separately declared |
| View-level soft delete | IMPLEMENTED in `shared/views/base.py` `SoftDeleteMixin.perform_destroy()` |
| Cascade soft delete | NOT IMPLEMENTED -- children not auto-soft-deleted |

**Finding ARCH-03 (MEDIUM):** Cascade soft delete is not implemented. When a Menu is soft-deleted, its Categories and Products remain visible unless explicitly deleted. Consider adding cascading soft-delete for parent-child relationships.

---

## 3. Database Schema Analysis

### 3.1 Model Distribution by App

| App | Models | Lines of Code (models.py) |
|-----|--------|---------------------------|
| core | 14 | ~2000 |
| menu | 9 | ~2200 |
| orders | 10 | ~3500+ |
| subscriptions | 8 | ~2700+ |
| customers | 6 | ~1100 |
| inventory | 7 | ~900 |
| analytics | 4 | ~500 |
| campaigns | 4 | ~550 |
| seo | 10 | ~1200 |
| seo_shield | 4 | ~300 |
| media | 2 | ~400 |
| notifications | 1 | ~200 |
| dashboard | 2 | ~250 |
| ai | 2 | ~300 |
| reporting | 5 | ~900 |
| **Total** | **~78** | **~17,000+** |

### 3.2 Key Design Decisions

- **UUID primary keys:** All business entities use `uuid.uuid4` for external IDs alongside auto-increment PKs
- **TimeStampedMixin:** All models include `created_at` and `updated_at` timestamps
- **TextChoices enums:** Extensive use of Django TextChoices for type safety (located in `choices.py` per app)
- **Connection pooling:** `conn_max_age=600` configured in production (dj-database-url)
- **Health checks:** `conn_health_checks=True` enabled

**Finding ARCH-04 (MEDIUM):** No database index coverage audit has been performed. The orders app (3500+ LOC in models.py) and subscriptions app (2700+ LOC) are prime candidates for query optimization through composite indexes on frequently filtered fields (organization + status + created_at).

---

## 4. API Architecture

### 4.1 Endpoint Inventory

Total ViewSets and API Views identified: **~80** across all apps.

| App | ViewSets/Views | Type |
|-----|---------------|------|
| core | 9 | Auth (Login, Logout, Token, UserMe, PasswordChange, Sessions) + Organization + User |
| menu | 7 | Theme, Menu, Category, Product, ProductVariant, ProductModifier, Allergen |
| orders | 5 | Zone, Table, QRCode, Order, ServiceRequest, Discount |
| subscriptions | 6 | Feature, Plan, Subscription, Invoice, PlanFeature, OrganizationUsage |
| analytics | 5 | DashboardMetric, SalesAggregation, ProductPerformance, CustomerMetric |
| reporting | 10 | ReportCatalog, ReportExecution, RunReport, ExportReport, Conversational, etc. |
| campaigns | 4 | Campaign, Coupon, CouponUsage, Referral |
| inventory | 7 | Supplier, InventoryItem, StockMovement, PurchaseOrder, PurchaseOrderItem, Recipe, RecipeIngredient |
| customers | 2 | Customer, Feedback |
| media | 6 | MediaFolder (CRUD), Media (list, upload, detail, delete) |
| notifications | 1 | Notification |
| ai | 5 | GenerateDescription, ImproveText, SuggestNames, Credits, GenerationHistory |
| seo | 10 | Redirect, AuthorProfile, BrokenLink, TXTFileConfig, PSEOTemplate, PSEOPage, etc. |
| website | 20+ | Home, About, Features, Pricing, Blog, Contact, Legal, Support, etc. (template views) |
| accounts | 8 | Login, Register, Profile, Settings, Subscription, Invoices, Dashboard |

### 4.2 API Conventions Compliance

| Convention | Status | Reference |
|------------|--------|-----------|
| URL versioning `/api/v1/` | CONFIGURED | `DEFAULT_VERSIONING_CLASS: URLPathVersioning` |
| Standard response format | IMPLEMENTED | `StandardResponseMixin` in `shared/views/base.py` |
| Custom exception handler | IMPLEMENTED | `shared/utils/exceptions.py` -- `custom_exception_handler` |
| PageNumberPagination (20/page) | CONFIGURED | `StandardPagination` class, max 100 |
| DjangoFilterBackend | CONFIGURED | Default filter backend in DRF settings |
| Throttling | CONFIGURED | anon: 100/hr (50/hr prod), user: 1000/hr |

---

## 5. Async Task Architecture (Celery)

### 5.1 Configuration

| Setting | Value | Location |
|---------|-------|----------|
| Broker | Redis (redis://redis:6379/1) | docker-compose.yml |
| Result Backend | Redis | Same |
| Serializer | JSON | base.py line 503 |
| Soft time limit | 300s (5 min) | base.py line 509 |
| Hard time limit | 600s (10 min) | base.py line 510 |
| Acks late | True | base.py line 511 |
| Reject on worker lost | True | base.py line 512 |
| Prefetch multiplier | 1 (dev), 4 (prod) | base.py / production.py |
| Concurrency | 2 (Docker worker) | Dockerfile line 208 |
| Max tasks per child | 50 | Dockerfile line 209 |
| Beat scheduler | DatabaseScheduler | django-celery-beat |

### 5.2 Docker Topology

- **celery-worker stage:** Prefork pool, concurrency=2, max-tasks-per-child=50
- **celery-beat stage:** Single replica enforced (`deploy.replicas: 1` in docker-compose.prod.yml)

**Finding ARCH-05 (LOW):** Celery configuration is production-ready with proper timeouts, acks-late, and single-beat enforcement. The worker concurrency of 2 is appropriate for a CX21 VPS.

---

## 6. i18n Architecture

### 6.1 Language Support

| Language | Code | .po File | Translation Files | Seed Data |
|----------|------|----------|-------------------|-----------|
| Turkish | tr | EXISTS | 10 translation.py files | Primary |
| English | en | EXISTS | 10 translation.py files | Complete |
| Arabic | ar | EXISTS | 10 translation.py files | Partial |
| Farsi | fa | EXISTS | 10 translation.py files | Partial |
| Ukrainian | uk | EXISTS | 10 translation.py files | Partial |

### 6.2 modeltranslation Coverage

Translation registrations found in 10 apps:

- `apps/menu/translation.py` -- Theme, Menu, Category, Product, Allergen fields
- `apps/orders/translation.py` -- Zone, Table, QRCode fields
- `apps/subscriptions/translation.py` -- Plan, Feature fields
- `apps/core/translation.py` -- Organization, Branch, Role fields
- `apps/customers/translation.py` -- Customer-facing fields
- `apps/campaigns/translation.py` -- Campaign, Coupon fields
- `apps/inventory/translation.py` -- Supplier, InventoryItem fields
- `apps/notifications/translation.py` -- Notification fields
- `apps/seo/translation.py` -- SEO metadata fields
- `apps/website/translation.py` -- CMS content fields

### 6.3 Configuration

```
MODELTRANSLATION_DEFAULT_LANGUAGE = "tr"
MODELTRANSLATION_LANGUAGES = ("tr", "en", "ar", "fa", "uk")
MODELTRANSLATION_FALLBACK_LANGUAGES = {"default": ("tr", "en")}
```

**Finding ARCH-06 (LOW):** i18n architecture is comprehensive. All 5 .po files exist in `locale/`. The fallback chain (tr -> en) is appropriate. The `LocaleMiddleware` is properly positioned in the middleware chain.

---

## 7. Security Architecture

### 7.1 Authentication Layers

| Layer | Implementation | Config |
|-------|----------------|--------|
| JWT Access Token | simplejwt | 15 min expiry, HS256 |
| JWT Refresh Token | simplejwt | 7 days, rotate on use, blacklist |
| Session Auth | Django sessions | 7-day cookie, HTTPOnly, SameSite=Lax |
| Password Hashing | BCryptSHA256 | Primary hasher, min 12 chars |
| Custom Backend | EmailOrUsernameBackend | `apps/core/backends.py` |

### 7.2 Middleware Security Chain

```
1. SecurityMiddleware (Django built-in)
2. WhiteNoiseMiddleware (static files)
3. CorsMiddleware (CORS headers)
4. SEOShieldMiddleware (bot protection, rate limiting)
5. CanonicalDomainMiddleware (domain normalization)
6. RedirectMiddleware (SEO redirects)
7. SessionMiddleware
8. LocaleMiddleware
9. CommonMiddleware
10. CsrfViewMiddleware
11. AuthenticationMiddleware
12. ImpersonateMiddleware
13. MessageMiddleware
14. XFrameOptionsMiddleware
15. SEOHeadersMiddleware
16. Track404Middleware
```

### 7.3 Security Headers

| Header | Value | Status |
|--------|-------|--------|
| X-Frame-Options | DENY | CONFIGURED |
| X-Content-Type-Options | nosniff | CONFIGURED |
| XSS Filter | True | CONFIGURED |
| HSTS | Configurable (default 0) | READY |
| Referrer-Policy | strict-origin-when-cross-origin | CONFIGURED (prod) |
| CSP | Delegated to reverse proxy | NOT IN DJANGO |

**Finding ARCH-07 (MEDIUM):** Content Security Policy (CSP) headers are not configured at the Django level and are delegated to the reverse proxy. This should be documented and verified in the Nginx/Traefik configuration.

---

## 8. Docker & Deployment Architecture

### 8.1 Multi-Stage Dockerfile (5 Stages)

| Stage | Base Image | Purpose |
|-------|-----------|---------|
| css-builder | node:20-slim | Tailwind CSS compilation |
| builder | python:3.13-slim-bookworm | pip install + venv creation |
| production | python:3.13-slim-bookworm | Runtime image (non-root user) |
| development | extends production | Dev tools + runserver |
| celery-worker | extends production | Background task worker |
| celery-beat | extends production | Periodic task scheduler |

### 8.2 Production Service Topology (docker-compose.prod.yml)

```
                   +------------------+
                   |   Nginx/Traefik  |
                   |  (reverse proxy) |
                   +--------+---------+
                            |
                   +--------v---------+
                   |     web:8000     |
                   |   (Gunicorn 3w)  |
                   +---+----------+---+
                       |          |
              +--------v--+  +---v---------+
              |    db      |  |   redis     |
              | PG15-alpine|  | 7-alpine    |
              +--------+---+  +---+---------+
                       |          |
              +--------v--+  +---v---------+
              | celery_wkr |  | celery_beat |
              | (prefork)  |  | (single)    |
              +------------+  +-------------+
```

### 8.3 Key Docker Features

- Non-root user (`emenum`, UID/GID 1000)
- tini init system for signal handling
- Health checks on all services (pg_isready, redis-cli ping, curl /health/)
- Volume persistence for postgres_data, redis_data, media, staticfiles
- AMD64/EPYC compatibility via `Dockerfile.amd64linux`

**Finding ARCH-08 (LOW):** Production binding on ports is `"${WEB_PORT:-8000}:8000"` without localhost restriction for the web service. Database and Redis correctly bind to `127.0.0.1`. The web service should also bind to `127.0.0.1` when behind a reverse proxy.

---

## 9. Scalability Assessment

| Dimension | Current State | Rating | Bottleneck |
|-----------|--------------|--------|------------|
| Horizontal web scaling | Gunicorn 3 workers | YELLOW | Single VPS, no load balancer |
| Database scaling | Single PostgreSQL | YELLOW | No read replicas, no PgBouncer |
| Cache scaling | Redis 256MB, allkeys-lru | GREEN | Appropriate for current scale |
| Celery scaling | 2 workers, prefork | GREEN | Sufficient for MVP load |
| Static files | WhiteNoise | YELLOW | No CDN, increases server load |
| Media files | Local filesystem | RED | No S3/CDN, no backup strategy |
| Session storage | Database-backed | YELLOW | Should migrate to Redis |

**Finding ARCH-09 (HIGH):** Media files are stored on the local filesystem with no external storage backend (S3) or CDN. For a SaaS serving 350,000+ potential businesses, this is a significant scalability bottleneck. Media volume loss = data loss.

**Finding ARCH-10 (MEDIUM):** No PgBouncer or connection pooler is configured. With `conn_max_age=600`, connections are reused within a single worker process, but there is no external pooling for connection management across workers.

---

## 10. Technical Debt Register

| ID | Item | Severity | Effort | Impact |
|----|------|----------|--------|--------|
| TD-01 | TenantMiddleware commented out (base.py:204) | Medium | 2h | Consistency |
| TD-02 | No cascade soft-delete for parent-child | Medium | 8h | Data integrity |
| TD-03 | No database index audit | Medium | 4h | Performance |
| TD-04 | Media on local filesystem, no S3 | High | 16h | Scalability |
| TD-05 | No PgBouncer connection pooling | Medium | 4h | Performance |
| TD-06 | CSP headers not configured in Django | Medium | 2h | Security |
| TD-07 | No CDN for static/media files | Medium | 8h | Performance |
| TD-08 | Session storage on database, not Redis | Low | 2h | Performance |
| TD-09 | Web service port not localhost-bound in prod | Low | 1h | Security |
| TD-10 | `all_objects` manager not explicitly declared | Low | 1h | Consistency |

---

## 11. Recommendations (Prioritized)

### Priority 1 -- Critical (Next Sprint)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| R-01 | Configure S3-compatible storage for media files (Hetzner Object Storage) | 16h | HIGH |
| R-02 | Activate TenantMiddleware in middleware chain or document the alternative approach | 2h | MEDIUM |

### Priority 2 -- Important (Next PI)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| R-03 | Add PgBouncer as a sidecar container in docker-compose | 4h | MEDIUM |
| R-04 | Implement cascade soft-delete for Menu->Category->Product chain | 8h | MEDIUM |
| R-05 | Run database index audit and add composite indexes for hot queries | 4h | MEDIUM |
| R-06 | Set up CloudFlare or BunnyCDN for static/media serving | 8h | MEDIUM |

### Priority 3 -- Nice to Have (Backlog)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| R-07 | Switch session backend to Redis | 2h | LOW |
| R-08 | Add CSP headers at Django level as defense-in-depth | 2h | LOW |
| R-09 | Bind web port to 127.0.0.1 in docker-compose.prod.yml | 1h | LOW |
| R-10 | Implement OpenTelemetry tracing for distributed observability | 24h | MEDIUM |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-17 | Automated Audit System | Initial audit report |
