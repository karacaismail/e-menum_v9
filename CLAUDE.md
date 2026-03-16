# E-Menum - Enterprise QR Menu SaaS

> **Auto-Claude Master Reference Document**
> Bu dosya, Auto-Claude agent'in projeyi anlamasi icin tek yetkili kaynaktir.
> Son Guncelleme: 2026-03-16

---

## 1. PRODUCT OVERVIEW

### 1.1 Urun Tanimi

E-Menum, restoran ve kafelere yonelik yapay zeka destekli dijital menu platformudur. Temel deger onerisi: **"Akilli menuler, veri odakli kararlar."**

| Ozellik | Deger |
|---------|-------|
| **Hedef Pazar** | Turkiye F&B sektoru (350.000+ isletme) |
| **Hedef Segment** | Kafeler, restoranlar, zincir isletmeler |
| **Fiyatlandirma** | Freemium + 4 ucretli tier (₺2K-8K/ay) |
| **Diferansiyator** | AI-powered icerik uretimi, analitik, tahminleme |

### 1.2 Hedef Kullanici Rolleri

| Rol | Organizasyon Ici | Sorumluluk |
|-----|------------------|------------|
| `owner` | Evet | Tam yetki, fatura, abonelik |
| `manager` | Evet | Menu, siparis, personel yonetimi |
| `staff` | Evet | Siparis alma, masa yonetimi |
| `viewer` | Evet | Salt okunur dashboard |

| Rol | Platform (Sistem) | Sorumluluk |
|-----|-------------------|------------|
| `super_admin` | Platform | Tam sistem yetkisi |
| `admin` | Platform | Musteri, fatura, destek |
| `sales` | Platform | CRM, lead yonetimi |
| `support` | Platform | Destek ticket'lari |

| Rol | Public | Sorumluluk |
|-----|--------|------------|
| `customer` | Hayir | Menu goruntuleme, siparis |
| `anonymous` | Hayir | Sadece public menu |

---

## 2. TECH STACK

### 2.1 Backend

```yaml
Runtime:        Python 3.13
Framework:      Django 5.0
API:            Django REST Framework 3.15
ORM:            Django ORM
Database:       PostgreSQL 15+ (SQLite for local dev)
Cache:          Redis 7.x (django-redis)
Queue:          Celery 5.4 + Redis broker
Task Scheduler: django-celery-beat
Process:        Gunicorn (production)
```

### 2.2 Libraries

```yaml
Auth:           djangorestframework-simplejwt (JWT)
Authorization:  django-guardian (object-level RBAC/ABAC)
Filtering:      django-filter
CORS:           django-cors-headers
Email:          django-anymail (Mailgun backend)
Media:          django-filer + easy-thumbnails
Translations:   django-modeltranslation
Impersonate:    django-impersonate (superadmin)
Environment:    django-environ
Static:         whitenoise
DB URL:         dj-database-url
```

### 2.3 Frontend

```yaml
Template:       Django Templates (SSR)
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
Process:        Gunicorn + Celery workers
Proxy:          Nginx (reverse proxy)
SSL:            Let's Encrypt (auto-renewal)
CI/CD:          GitHub Actions → Coolify webhook
Static:         WhiteNoise (compressed + cached)
```

---

## 3. CRITICAL RULES (KESINLIKLE KIRILMAMALI)

### 3.1 Multi-Tenancy

```python
# RULE: Her queryset'te organization filtresi ZORUNLU

# DOGRU:
Menu.objects.filter(organization=request.organization)

# YANLIS:
Menu.objects.all()  # TUM TENANT VERILERI!
```

TenantMiddleware (`shared/middleware/tenant.py`) her request'e `request.organization` inject eder.

### 3.2 Authorization

```python
# RULE: Her ViewSet permission_classes ile korunmali

# DOGRU:
class MenuViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, HasOrganizationPermission]

# YANLIS:
class MenuViewSet(ModelViewSet):
    permission_classes = []  # Koruma yok!
```

### 3.3 Soft Delete

```python
# RULE: Hicbir veri fiziksel silinmez

# DOGRU:
menu.deleted_at = timezone.now()
menu.save()

# YANLIS:
menu.delete()  # Fiziksel silme!
```

Tum business entity'ler `SoftDeleteMixin` kullanmali (`shared/mixins/soft_delete.py`).

### 3.4 Import Convention

```python
# RULE: Standard Python import'lari kullanilmali

# DOGRU:
from apps.core.models import Organization
from shared.permissions.plan_enforcement import RequiresPlanFeature
from shared.mixins.soft_delete import SoftDeleteMixin

# YANLIS:
from ../../../../core/models import Organization  # Relative import karmasasi
```

### 3.5 i18n Zorunlulugu

```python
# RULE: UI'da hardcoded string YASAK

# DOGRU (Template):
{% load i18n %}
<h1>{% trans "Menu Olustur" %}</h1>

# DOGRU (Python):
from django.utils.translation import gettext_lazy as _
raise ValidationError(_("Menu bulunamadi"))

# YANLIS:
<h1>Menu Olustur</h1>  # Hardcoded!
```

### 3.6 Error Handling

```python
# RULE: DRF exception handler ile tutarli hata formati

# DOGRU:
from rest_framework.exceptions import NotFound
raise NotFound(detail="Menu not found", code="MENU_NOT_FOUND")

# custom_exception_handler: shared/utils/exceptions.py
# Response format: {"success": false, "error": {"code": "...", "message": "..."}}

# YANLIS:
raise Exception("Menu not found")  # Format tutarsizligi!
```

### 3.7 Validation

```python
# RULE: Tum input'lar DRF Serializer ile validate edilmeli

# DOGRU:
class CreateMenuSerializer(serializers.ModelSerializer):
    name = serializers.CharField(min_length=1, max_length=255)
    class Meta:
        model = Menu
        fields = ['name', 'description', 'is_published']

# YANLIS:
name = request.data.get('name')  # Validation yok!
```

---

## 4. PROJECT STRUCTURE

```
e_menum/                          # Django project root (manage.py here)
├── config/
│   ├── settings/
│   │   ├── base.py               # Common settings
│   │   ├── development.py        # Dev overrides
│   │   ├── staging.py            # Staging overrides
│   │   └── production.py         # Production overrides
│   ├── urls.py                   # Root URL configuration
│   ├── celery.py                 # Celery app configuration
│   ├── wsgi.py                   # WSGI entry point
│   └── asgi.py                   # ASGI entry point
│
├── apps/
│   ├── core/                     # Users, Organizations, Roles, Permissions
│   ├── menu/                     # Menus, Categories, Products, Themes
│   ├── orders/                   # Zones, Tables, QR Codes, Orders
│   ├── subscriptions/            # Plans, Subscriptions, Invoices
│   ├── customers/                # Customer profiles, feedback
│   ├── accounts/                 # Account settings, team management
│   ├── dashboard/                # Dashboard views & widgets
│   ├── analytics/                # Visit & order analytics
│   ├── reporting/                # Report generation
│   ├── notifications/            # In-app notifications
│   ├── campaigns/                # Marketing campaigns
│   ├── inventory/                # Stock management
│   ├── media/                    # Media/file management
│   ├── ai/                       # AI content generation
│   ├── website/                  # Public marketing site & CMS
│   ├── seo/                      # SEO metadata, redirects, sitemaps
│   └── seo_shield/               # Bot protection, rate limiting
│
├── shared/
│   ├── middleware/
│   │   └── tenant.py             # Multi-tenant context injection
│   ├── mixins/
│   │   └── soft_delete.py        # SoftDeleteMixin
│   ├── permissions/
│   │   └── plan_enforcement.py   # PlanEnforcementService, RequiresPlanFeature
│   ├── serializers/              # Shared serializer mixins
│   ├── utils/
│   │   ├── exceptions.py         # Custom DRF exception handler
│   │   ├── media.py              # Filer upload helpers
│   │   └── impersonate.py        # Impersonation permission checks
│   ├── views/                    # Shared view mixins
│   ├── widgets/                  # Custom form widgets
│   └── context_processors.py     # Template context processors
│
├── templates/
│   ├── layouts/                  # Base layout templates
│   ├── partials/                 # Reusable partials (sidebar, navbar, etc.)
│   ├── components/               # UI components
│   └── modules/                  # App-specific templates
│       ├── menu/
│       ├── orders/
│       ├── subscriptions/
│       └── ...
│
├── static/
│   ├── css/                      # Compiled Tailwind + custom CSS
│   ├── js/                       # Alpine.js + custom JS
│   └── images/                   # Static images
│
├── locale/
│   ├── tr/                       # Turkish (default)
│   ├── en/                       # English
│   ├── ar/                       # Arabic
│   ├── fa/                       # Farsi
│   └── uk/                       # Ukrainian
│
├── media/                        # User uploads (gitignored)
├── staticfiles/                  # collectstatic output (gitignored)
└── manage.py
```

---

## 5. DJANGO APP SYSTEM

### 5.1 App Categories

| Kategori | Apps | Aciklama |
|----------|------|----------|
| System/Core | `core`, `accounts` | Kullanici, organizasyon, auth — kaldirilmaz |
| Feature | `menu`, `orders`, `subscriptions`, `customers`, `inventory` | Is ozellikleri |
| Analytics | `analytics`, `reporting`, `dashboard` | Veri & raporlama |
| AI | `ai` | AI-powered icerik uretimi |
| Marketing | `campaigns`, `website`, `seo`, `seo_shield` | Pazarlama & SEO |
| Infrastructure | `media`, `notifications` | Altyapi servisleri |

### 5.2 App Structure Convention

Her Django app su yapida olmalidir:

```
apps/menu/
├── __init__.py
├── apps.py                # AppConfig
├── models.py              # Django models
├── serializers.py         # DRF serializers
├── views.py               # DRF ViewSets + Django views
├── urls.py                # URL patterns
├── admin.py               # Django admin registration
├── forms.py               # Django forms (for template views)
├── signals.py             # Signal handlers
├── tasks.py               # Celery async tasks
├── filters.py             # django-filter FilterSets
├── translation.py         # modeltranslation registrations
├── management/
│   └── commands/          # Custom management commands
├── migrations/            # Django migrations
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_serializers.py
```

### 5.3 Custom Management Commands

```bash
# Core / Seeding
python manage.py seed_roles              # Seed roles & permissions
python manage.py seed_plans              # Seed subscription plans
python manage.py seed_menu_data          # Seed demo menu data
python manage.py seed_allergens          # Seed allergen list
python manage.py seed_demo_data          # Seed full demo dataset
python manage.py seed_all_data           # Seed everything
python manage.py seed_extra_orgs         # Seed additional organizations
python manage.py seed_cms_content        # Seed website CMS content
python manage.py seed_seo_data           # Seed SEO metadata
python manage.py seed_shield_data        # Seed SEO shield config
python manage.py seed_report_definitions # Seed report templates

# Database
python manage.py safe_migrate            # Migration with safety checks
python manage.py check_migrations        # Verify migration state

# SEO
python manage.py check_seo_health        # SEO health audit

# Media
python manage.py migrate_urls_to_media   # Migrate URL references to media

# Shield
python manage.py shield_status           # Check SEO shield status
```

---

## 6. COMMANDS QUICK REFERENCE

### 6.1 Development

```bash
# Start dev server
python manage.py runserver

# Start with specific settings
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver

# Celery worker (for async tasks)
celery -A config worker -l info

# Celery beat (for scheduled tasks)
celery -A config beat -l info

# Build Tailwind CSS
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# Lint (Python)
ruff check .
ruff format .
```

### 6.2 Database

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Safe migrate (custom command with checks)
python manage.py safe_migrate

# Create superuser
python manage.py createsuperuser

# Seed all demo data
python manage.py seed_all_data
```

### 6.3 Static & Media

```bash
# Collect static files (for production)
python manage.py collectstatic --noinput

# Compile translations
python manage.py compilemessages

# Extract translation strings
python manage.py makemessages -l tr -l en -l ar -l fa -l uk
```

### 6.4 Build & Deploy

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for Tailwind)
npm install

# Build Tailwind for production
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Run tests
python manage.py test
# or with pytest
pytest

# Start production server
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 7. ARCHITECTURE DECISIONS (ADRs)

### ADR-001: Django over Node.js/Express

**Karar:** Django + DRF + Celery
**Gerekce:**
- Python ekosisteminde daha guclu ORM ve migration sistemi
- Admin panel built-in (gelistirme hizi)
- Celery ile production-grade async task yonetimi
- Django'nun security middleware'leri (CSRF, XSS, SQL injection korumalari)

### ADR-002: Django Templates over React/SPA

**Karar:** Server-side Django Templates + Alpine.js
**Gerekce:**
- SEO-friendly SSR varsayilan
- Daha hizli initial load
- Daha az bundle size, deployment karmasikligi yok
- Admin panel icin yeterli interaktivite (Alpine.js ile)

### ADR-003: django-guardian for Authorization

**Karar:** django-guardian (object-level permissions)
**Gerekce:**
- Object-level RBAC/ABAC esnekligi
- Tenant-scoped permissions
- Django'nun built-in permission sistemiyle entegre

### ADR-004: Multi-App Django Architecture

**Karar:** Her domain 1 Django app
**Gerekce:**
- Domain-driven modul bagimsizligi
- Her app kendi models, views, serializers, migrations
- Kolay maintenance ve test isolation

### ADR-005: Soft Delete Default

**Karar:** Tum entity'lerde `deleted_at` timestamp (SoftDeleteMixin)
**Gerekce:**
- Veri kaybi onleme
- Audit trail
- GDPR uyumlu (gercek silme proseduru ayri)

---

## 8. DOMAIN MODEL (Core Entities)

```
Organization (Tenant)
├── Users (many) ─── UserRole ─── Role ─── Permission
├── Branches (many)
├── Menus (many)
│   ├── Categories (many)
│   │   └── Products (many)
│   │       ├── ProductVariants (many)
│   │       ├── ProductModifiers (many)
│   │       ├── ProductAllergens (many-to-many)
│   │       └── NutritionInfo (one)
│   └── Themes (many)
├── Zones (many)
│   └── Tables (many)
│       └── QRCodes (many)
│           └── QRScans (many)
├── Orders (many)
│   ├── OrderItems (many)
│   └── Refunds (many)
├── ServiceRequests (many)
├── Reservations (many)
├── Discounts (many)
├── Customers (many)
├── Campaigns (many)
├── Notifications (many)
├── AuditLog (many)
└── Subscription (one)
    └── Plan (one)
        └── PlanFeatures (many)
```

---

## 9. API CONVENTIONS

### 9.1 URL Structure

```
/api/v1/{resource}/              # Collection (DRF Router)
/api/v1/{resource}/{id}/         # Single resource
/api/v1/{resource}/{id}/{sub}/   # Nested resource
```

### 9.2 Response Format

```json
// Success
{
  "success": true,
  "data": { ... }
}

// Success with pagination (DRF PageNumberPagination)
{
  "count": 150,
  "next": "http://api.example.com/items/?page=2",
  "previous": null,
  "results": [ ... ]
}

// Error (custom_exception_handler)
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

| Code | Kullanim |
|------|----------|
| 200 | GET, PUT, PATCH basarili |
| 201 | POST basarili (resource created) |
| 204 | DELETE basarili |
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

- JWT access token (15 min expiry) via `djangorestframework-simplejwt`
- Refresh token (7 days, rotate on use, blacklist after rotation)
- Password: bcrypt (BCryptSHA256PasswordHasher), min 12 chars
- Session auth for template-based views (7 day cookie)
- Custom `EmailOrUsernameBackend` for login

### 10.2 Authorization

- RBAC: Role-based baseline (Role, Permission, UserRole models in core)
- ABAC: Object-level via django-guardian
- Tenant isolation: `request.organization` injected by TenantMiddleware
- Plan enforcement: `PlanEnforcementService` gates features by subscription tier
- Impersonation: django-impersonate (superadmin only, 1hr max, read-only admin)

### 10.3 Data Protection

- Encryption in transit: TLS 1.3
- CSRF protection on all forms
- Security headers: XSS filter, X-Frame-Options DENY, Content-Type nosniff
- SEO Shield: Rate limiting, bot detection (`apps.seo_shield`)
- File uploads: MIME type whitelist, 10MB max

---

## 11. TESTING REQUIREMENTS

### 11.1 Coverage Targets

| Tur | Minimum |
|-----|---------|
| Unit | 80% |
| Integration | 60% |
| E2E | Critical paths |

### 11.2 Test File Locations

```
apps/menu/
├── models.py
├── views.py
├── serializers.py
└── tests/
    ├── __init__.py
    ├── test_models.py          # Unit tests
    ├── test_views.py           # API/view tests
    ├── test_serializers.py     # Serializer tests
    └── test_e2e.py             # E2E tests (optional)
```

### 11.3 Test Tools

```yaml
Framework:      pytest + pytest-django
Fixtures:       factory_boy
API Testing:    DRF APIClient / APITestCase
Coverage:       pytest-cov
```

---

## 12. AI-ASSISTED DEVELOPMENT PATTERNS

### 12.1 High Success Rate Patterns (>90%)

- Django ORM CRUD operations
- DRF ModelSerializer + ModelViewSet
- DRF permission_classes
- django-filter FilterSets
- Django Template tags + Flowbite components
- Celery task definitions

### 12.2 Always Specify in Prompts

```
1. "ModelViewSet kullan"                    → CRUD otomatik
2. "organization ile tenant filter"         → Multi-tenancy
3. "permission_classes ekle"                → Yetkilendirme
4. "Serializer ile validation"              → Tip guvenligi
5. "SoftDeleteMixin kullan"                 → Veri koruma
6. "{% trans %} ile i18n"                   → Ceviriler
```

### 12.3 Avoid in Prompts

- Custom abstractions without examples
- Magic strings
- `Any` type annotations
- Manual URL patterns (use DRF routers)
- Circular imports between apps

---

## 13. REFERENCE DOCUMENTS

### 13.1 Kapsam & Kisitlamalar (ONCELIKLI OKUMA)

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| **CONSTRAINTS.md** | .auto-claude/ | Kisitlamalar, sinirlar, yapilmamasi gerekenler |
| **MVP_SCOPE.md** | .auto-claude/ | MVP kapsami, neler var/yok |

### 13.2 Proje Baglami

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| PROJECT_CONTEXT.md | .auto-claude/ | Detayli proje baglami |
| GLOSSARY.md | domain/ | Terminoloji, kisaltmalar |

### 13.3 Mimari

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| SYSTEM_DESIGN.md | architecture/ | C4 diagrams, data flow |
| DATABASE_SCHEMA.md | architecture/ | Entity relationships |
| API_CONTRACTS.md | architecture/ | Endpoint specifications |
| SECURITY_MODEL.md | security/ | Auth/authz details |

### 13.4 Standartlar

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| CODING_STANDARDS.md | standards/ | Python/Django code conventions |
| TESTING_STRATEGY.md | standards/ | pytest test approach |
| COMPONENT_PATTERNS.md | standards/ | Django Template + Flowbite patterns |

### 13.5 Domain

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| BUSINESS_RULES.md | domain/ | Domain logic, pricing |

### 13.6 Design

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| DESIGN_SYSTEM_PHILOSOPHY.md | design/ | UED, theming, accessibility |
| PERSONA_USER_FLOWS.md | design/ | Personas, user journeys |
| FRONTEND_ARCHITECTURE.md | design/ | Tailwind/Alpine.js approach |

### 13.7 Module Specs

| Dokuman | Konum | Icerik |
|---------|-------|--------|
| spec.md | specs/001-menu-module/ | Menu module specification |
| requirements.json | specs/001-menu-module/ | Structured requirements |
| context.json | specs/001-menu-module/ | AI/vibecoding context |

---

## 14. SPEC WRITING GUIDELINES

Her yeni ozellik icin `.auto-claude/specs/XXX-feature-name/` dizini olustur:

1. `spec.md` - Feature specification
2. `requirements.json` - Structured requirements
3. `context.json` - Related files and references

Spec numaralama: `001`, `002`, ... (uc haneli, sirali)

---

## 15. EMERGENCY CONTACTS

| Rol | Isim | Sorumluluk |
|-----|------|------------|
| Strategic Lead | Ismail | Mimari kararlar |
| Frontend | Ali | Istanbul bolge dev |
| Backend | Bora | Diger bolge dev |
| DevOps | Ahmet | GTM, Mautic, infra |
| Sales | Pinar | Musteri, destek |

---

*Bu dokuman, Auto-Claude agent'in E-Menum projesini anlayabilmesi icin tek yetkili referanstir. Tum spec'ler ve implementasyonlar bu dokumanla tutarli olmalidir.*
