# E-Menum System Design

> **Auto-Claude Architecture Document**
> Sistem mimarisi, veri akisi, entegrasyon noktalari ve deployment yapisi.
> Son Guncelleme: 2026-03-16

---

## 1. HIGH-LEVEL OVERVIEW

### 1.1 System Context (C4 Level 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL ACTORS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Customer │  │  Staff   │  │  Owner   │  │  Admin   │  │ Anonymous│     │
│  │ (Mobile) │  │ (Tablet) │  │(Desktop) │  │(Desktop) │  │ (Mobile) │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │             │             │            │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘
        │             │             │             │             │
        └─────────────┴──────┬──────┴─────────────┴─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            E-MENUM PLATFORM                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     Django Web Application                            │ │
│  │   • Public Menu Views (Django Templates, SSR)                        │ │
│  │   • Admin Dashboard (Django Templates + Alpine.js)                   │ │
│  │   • REST API (Django REST Framework)                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   AI APIs    │    │   Payment    │    │    Email     │
│  (Claude,    │    │  (Iyzico/    │    │  (SendGrid/  │
│   OpenAI)    │    │   Stripe)    │    │   AWS SES)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 1.2 Container Diagram (C4 Level 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            E-MENUM PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         NGINX (Reverse Proxy)                       │   │
│  │   • SSL Termination    • Static File Serving    • Load Balancing   │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                        │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 GUNICORN (WSGI Application Server)                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                   DJANGO APPLICATION                        │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │   │   │
│  │  │  │   PUBLIC    │  │ RESTAURANT  │  │   ADMIN     │        │   │   │
│  │  │  │   VIEWS     │  │   PANEL     │  │   PANEL     │        │   │   │
│  │  │  │  /menu/:slug│  │  /restaurant│  │  /admin/*   │        │   │   │
│  │  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │   │   │
│  │  │         │                │                │                │   │   │
│  │  │  ┌──────┴────────────────┴────────────────┘                │   │   │
│  │  │  │  ┌─────────────┐                                       │   │   │
│  │  │  │  │  DRF API    │                                       │   │   │
│  │  │  │  │  /api/v1/*  │                                       │   │   │
│  │  │  │  └─────────────┘                                       │   │   │
│  │  │  │                                                         │   │   │
│  │  │  ▼                                                         │   │   │
│  │  │  ┌───────────────────────────────────────────────────────┐ │   │   │
│  │  │  │                  MIDDLEWARE STACK                      │ │   │   │
│  │  │  │  Auth → Tenant → Permission → RateLimit → AuditLog   │ │   │   │
│  │  │  └───────────────────────────────────────────────────────┘ │   │   │
│  │  │                          │                                 │   │   │
│  │  │                          ▼                                 │   │   │
│  │  │  ┌───────────────────────────────────────────────────────┐ │   │   │
│  │  │  │                   DJANGO APPS (17)                    │ │   │   │
│  │  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │ │   │   │
│  │  │  │  │  Auth  │ │  Menu  │ │ Orders │ │   AI   │        │ │   │   │
│  │  │  │  ├────────┤ ├────────┤ ├────────┤ ├────────┤        │ │   │   │
│  │  │  │  │  Users │ │Products│ │  QR    │ │Analytic│        │ │   │   │
│  │  │  │  ├────────┤ ├────────┤ ├────────┤ ├────────┤        │ │   │   │
│  │  │  │  │  Orgs  │ │ Tables │ │Billing │ │  ...   │        │ │   │   │
│  │  │  │  └────────┘ └────────┘ └────────┘ └────────┘        │ │   │   │
│  │  │  └───────────────────────────────────────────────────────┘ │   │   │
│  │  │                          │                                 │   │   │
│  │  │                          ▼                                 │   │   │
│  │  │  ┌───────────────────────────────────────────────────────┐ │   │   │
│  │  │  │                 SHARED SERVICES                       │ │   │   │
│  │  │  │  Signals • Permissions • CacheService • CeleryTasks  │ │   │   │
│  │  │  │  PlanEnforcement • AuditLog • SoftDeleteMixin        │ │   │   │
│  │  │  └───────────────────────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                          │                                                 │
│         ┌────────────────┼────────────────┬────────────────┐              │
│         ▼                ▼                ▼                ▼              │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐      │
│  │ PostgreSQL │   │   Redis    │   │  Celery    │   │   File     │      │
│  │  15        │   │  7         │   │  Workers   │   │  Storage   │      │
│  │ (Primary)  │   │ (Cache +   │   │  (Async)   │   │ (Local/S3) │      │
│  │            │   │  Broker)   │   │            │   │            │      │
│  └────────────┘   └────────────┘   └────────────┘   └────────────┘      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Component Diagram (C4 Level 3) - Shared / Cross-Cutting Concerns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SHARED MODULE (shared/)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         BASE CLASSES                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ BaseTenant   │  │ SoftDelete   │  │  BaseModel   │              │   │
│  │  │  ViewSet     │  │   Mixin      │  │  (abstract)  │              │   │
│  │  │ (org-scoped  │  │ (deletedAt,  │  │ (timestamps, │              │   │
│  │  │  CRUD ops)   │  │  is_active)  │  │  uuid pk)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          MIDDLEWARE                                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │   │
│  │  │  Auth  │→│ Tenant │→│  Perm  │→│  Rate  │→│ Audit  │           │   │
│  │  │(Django │ │Middleware│ │ Check │ │ Limit │ │  Log   │           │   │
│  │  │ Auth)  │ │(sets   │ │(DRF   │ │(django-│ │(AuditLog│           │   │
│  │  │        │ │req.org)│ │perms) │ │ratelim)│ │model)  │           │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CORE SERVICES                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Auth       │  │  Permission  │  │   Django     │              │   │
│  │  │  (JWT +      │  │  Service     │  │   Signals    │              │   │
│  │  │   Sessions)  │  │  (RBAC/ABAC) │  │  (Events)    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │   Cache      │  │   Celery     │  │   Plan       │              │   │
│  │  │   (Redis     │  │   Tasks      │  │  Enforcement │              │   │
│  │  │   backend)   │  │  (async ops) │  │   Service    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          EXCEPTIONS                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  AppException │  │   Error     │  │  DRF Custom  │              │   │
│  │  │  (base)      │  │   Codes     │  │  Exception   │              │   │
│  │  │              │  │   (enum)    │  │   Handler    │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DJANGO APP BOUNDARIES

### 2.1 App Dependency Graph

```
                    ┌─────────────┐
                    │   SHARED    │
                    │  (mixins,   │
                    │ middleware)  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │   AUTH    │    │   CACHE   │    │  SIGNALS  │
   │(apps.auth)│    │  (Redis)  │    │ (events)  │
   └─────┬─────┘    └───────────┘    └───────────┘
         │
         ▼
   ┌───────────┐
   │   USERS   │
   │(apps.users)│
   └─────┬─────┘
         │
         ▼
   ┌───────────┐
   │   ORGS    │◄─────────────────────────────────────┐
   │(apps.orgs)│                                      │
   └─────┬─────┘                                      │
         │                                            │
    ┌────┴────┬────────────┬────────────┐            │
    │         │            │            │            │
    ▼         ▼            ▼            ▼            │
┌───────┐ ┌───────┐  ┌───────────┐ ┌─────────┐      │
│ MENU  │ │TABLES │  │  BILLING  │ │SETTINGS │      │
└───┬───┘ └───┬───┘  └───────────┘ └─────────┘      │
    │         │                                      │
    ▼         │                                      │
┌───────┐     │      ┌───────────┐                  │
│PRODUCTS│    └─────►│  ORDERS   │──────────────────┤
└───┬───┘            └─────┬─────┘                  │
    │                      │                        │
    │         ┌────────────┼────────────┐          │
    │         │            │            │          │
    │         ▼            ▼            ▼          │
    │    ┌─────────┐ ┌──────────┐ ┌─────────┐     │
    │    │ KITCHEN │ │ WAITER   │ │INVENTORY│     │
    │    │ DISPLAY │ │   APP    │ │         │     │
    │    └─────────┘ └──────────┘ └─────────┘     │
    │                                              │
    └──────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ANALYTICS │ │CAMPAIGNS │ │CUSTOMERS │
        └──────────┘ └──────────┘ └──────────┘
```

### 2.2 Django App Structure Convention

Each Django app under `apps/` follows this layout:

```
apps/<app_name>/
├── __init__.py
├── apps.py                  # AppConfig with signals import
├── models.py                # Django ORM models (SoftDeleteMixin)
├── serializers.py           # DRF serializers (validation)
├── views.py                 # DRF ViewSets (BaseTenantViewSet)
├── urls.py                  # URL patterns (router.register)
├── permissions.py           # DRF permission classes
├── signals.py               # Django signal handlers
├── tasks.py                 # Celery async tasks
├── admin.py                 # Django admin registration
├── filters.py               # django-filter FilterSets
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_tasks.py
└── migrations/
    └── 0001_initial.py
```

### 2.3 Cross-App Communication

| Pattern | Usage | Example |
|---------|-------|---------|
| Direct Model Import | Synchronous, same transaction | `from apps.products.models import Product` |
| Django Signals | Async-style, loose coupling | `order_created` signal -> inventory update |
| Celery Tasks | Background processing | `send_order_confirmation.delay(order_id)` |
| Shared Mixins | Cross-cutting behavior | `SoftDeleteMixin`, `BaseTenantViewSet` |

---

## 3. DATA FLOW

### 3.1 Request Lifecycle

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         REQUEST LIFECYCLE                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. INGRESS                                                              │
│  ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────┐             │
│  │ Client  │───►│  Nginx  │───►│ Gunicorn │───►│ Django  │             │
│  │ Request │    │  Proxy  │    │  (WSGI)  │    │  App    │             │
│  └─────────┘    └─────────┘    └──────────┘    └─────────┘             │
│                                                      │                  │
│  2. DJANGO MIDDLEWARE CHAIN                          ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  SecurityMiddleware → SessionMiddleware → CommonMiddleware       │  │
│  │  → CsrfViewMiddleware → AuthenticationMiddleware                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  3. CUSTOM MIDDLEWARE (AUTH & CONTEXT)                ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  TenantMiddleware (sets request.organization from subdomain/     │  │
│  │  header) → PlanEnforcementMiddleware → AuditLogMiddleware       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  4. DRF LAYER (API requests)                         ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  DRF Authentication → Permission Classes → Throttling           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  5. VIEW / VIEWSET                                   ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  URL Resolve → ViewSet Action → Serializer Validation           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  6. SERVICE / BUSINESS LOGIC                         ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Business Logic → QuerySet (org-scoped) → Signal Emit           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  7. DATA LAYER                                       ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Django ORM → PostgreSQL → Cache Update (Redis, if applicable)  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                      │                  │
│  8. RESPONSE                                         ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Serializer Output → DRF Response / Template Render → Send      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTHENTICATION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LOGIN FLOW:                                                            │
│  ┌────────┐  email/pass   ┌────────┐  validate   ┌────────┐            │
│  │ Client │──────────────►│  Auth  │────────────►│  User  │            │
│  └────────┘               │  View  │             │  Model │            │
│       ▲                   └────────┘             └────┬───┘            │
│       │                                               │                │
│       │                   ┌─────────┐  check_pass ┌───▼────┐           │
│       │                   │ Django  │◄────────────│   DB   │           │
│       │                   │ hasher  │             └────────┘           │
│       │                   └─────────┘                                  │
│       │                        │                                       │
│       │  access_token         │ match                                  │
│       │  refresh_token        ▼                                        │
│       │  (httpOnly cookie) ┌────────┐                                  │
│       └────────────────────│  JWT   │                                  │
│                            │ encode │                                  │
│                            └────────┘                                  │
│                                                                         │
│  REQUEST AUTH (API):                                                    │
│  ┌────────┐  Authorization  ┌──────────────┐  decode  ┌────────┐       │
│  │ Client │────────────────►│DRF JWT Auth  │────────►│  JWT   │       │
│  │        │  Bearer {token} │(custom class)│         │ decode │       │
│  └────────┘                 └──────────────┘         └────┬───┘       │
│       ▲                          │                        │            │
│       │                          │ valid                  │ payload    │
│       │  request.user            ▼                        ▼            │
│       │  request.organization ┌────────────┐  load   ┌────────┐       │
│       └───────────────────────│  Tenant    │◄────────│  User  │       │
│                               │ Middleware │         │  Model │       │
│                               └────────────┘         └────────┘       │
│                                                                         │
│  REQUEST AUTH (Dashboard - Session):                                    │
│  ┌────────┐  session cookie  ┌──────────────┐  lookup  ┌────────┐     │
│  │ Client │─────────────────►│ Django       │─────────►│ Redis  │     │
│  │        │                  │ Session Auth │          │(session│     │
│  └────────┘                  └──────────────┘          │ store) │     │
│       ▲                           │                     └────────┘     │
│       │  request.user             │ valid                              │
│       │  request.organization     ▼                                    │
│       └───────────────────────┌────────────┐                          │
│                               │  Tenant    │                          │
│                               │ Middleware │                          │
│                               └────────────┘                          │
│                                                                         │
│  TOKEN REFRESH:                                                         │
│  ┌────────┐  refresh_token  ┌────────┐  validate  ┌────────┐          │
│  │ Client │────────────────►│  Auth  │───────────►│ Redis  │          │
│  │        │  (cookie)       │  View  │            │(whitelist)│       │
│  └────────┘                 └────────┘            └────┬───┘          │
│       ▲                          │                     │               │
│       │  new access_token        │ valid               │ exists        │
│       │  new refresh_token       ▼                     ▼               │
│       └──────────────────────┌────────┐  rotate    ┌────────┐         │
│                              │  JWT   │◄───────────│ Revoke │         │
│                              │ encode │  old token │  Old   │         │
│                              └────────┘            └────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Event & Async Task Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVENT & ASYNC TASK FLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DJANGO SIGNALS (Synchronous Domain Events):                            │
│  ┌────────────┐  action   ┌────────────┐  signal  ┌────────────┐      │
│  │   ViewSet  │──────────►│   Model    │─────────►│  Signal    │      │
│  └────────────┘           │   .save()  │          │  Dispatch  │      │
│                           └────────────┘          └─────┬──────┘      │
│                                                         │              │
│  SIGNAL RECEIVERS:                                      ▼              │
│                           ┌─────────────────────────────────────────┐  │
│                           │              RECEIVERS                  │  │
│                           │  ┌──────────┐ ┌──────────┐ ┌─────────┐ │  │
│                           │  │ AuditLog │ │  Cache   │ │ Celery  │ │  │
│                           │  │  Create  │ │ Invalidate│ │Task Kick│ │  │
│                           │  └──────────┘ └──────────┘ └─────────┘ │  │
│                           └─────────────────────────────────────────┘  │
│                                                                         │
│  CELERY ASYNC TASKS:                                                    │
│  ┌────────────┐  .delay() ┌────────────┐  consume  ┌────────────┐     │
│  │  View /    │──────────►│   Redis    │──────────►│  Celery    │     │
│  │  Signal    │           │  (Broker)  │           │  Worker    │     │
│  └────────────┘           └────────────┘           └────────────┘     │
│                                                                         │
│  CELERY TASK CATALOG:                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  App             Task                        Purpose              │  │
│  │  ───             ────                        ───────              │  │
│  │  auth            send_welcome_email          Onboarding           │  │
│  │  auth            send_password_reset         Password recovery    │  │
│  │  menu            generate_qr_code            QR code creation     │  │
│  │  orders          send_order_confirmation     Email notification   │  │
│  │  analytics       aggregate_daily_stats       Nightly aggregation  │  │
│  │  ai              generate_ai_content         AI text generation   │  │
│  │  billing         process_subscription_webhook Payment processing  │  │
│  │  media           process_image_upload        Image resize/optimize│  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  CELERY BEAT (Periodic Tasks):                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Schedule          Task                                          │  │
│  │  ────────          ────                                          │  │
│  │  Every night 3AM   aggregate_daily_stats                         │  │
│  │  Every hour        cleanup_expired_sessions                      │  │
│  │  Every 5 min       process_webhook_retries                       │  │
│  │  Weekly Sunday     generate_weekly_reports                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. MULTI-TENANCY ARCHITECTURE

### 4.1 Tenant Resolution

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TENANT RESOLUTION FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TenantMiddleware (shared/middleware/tenant.py):                         │
│                                                                         │
│  ┌────────┐     ┌──────────────────────────────────────────────────┐   │
│  │Request │────►│  1. Extract org slug from:                       │   │
│  └────────┘     │     - Subdomain (cafe.emenum.com)                │   │
│                 │     - X-Organization header (API)                 │   │
│                 │     - Session data (dashboard)                    │   │
│                 │                                                   │   │
│                 │  2. Lookup Organization from DB (cached in Redis) │   │
│                 │                                                   │   │
│                 │  3. Set request.organization = org_instance       │   │
│                 │                                                   │   │
│                 │  4. Verify user belongs to organization           │   │
│                 └──────────────────────────────────────────────────┘   │
│                                                                         │
│  BaseTenantViewSet (shared/mixins/tenant_viewset.py):                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  class BaseTenantViewSet(ModelViewSet):                          │  │
│  │      def get_queryset(self):                                     │  │
│  │          return super().get_queryset().filter(                   │  │
│  │              organization=self.request.organization              │  │
│  │          )                                                       │  │
│  │                                                                  │  │
│  │      def perform_create(self, serializer):                       │  │
│  │          serializer.save(                                        │  │
│  │              organization=self.request.organization              │  │
│  │          )                                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  CRITICAL: Every business query MUST be scoped to organization.         │
│  BaseTenantViewSet enforces this automatically.                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. INTEGRATION POINTS

### 5.1 External API Integrations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL INTEGRATIONS                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  AI PROVIDERS (Failover Chain):                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────┐         ┌─────────┐         ┌─────────┐         │    │
│  │  │ Claude  │─failover─►│  GPT-4  │─failover─►│  Gemini │         │    │
│  │  │(Primary)│         │(Secondary)│         │(Tertiary)│         │    │
│  │  └─────────┘         └─────────┘         └─────────┘         │    │
│  │                                                                │    │
│  │  Circuit Breaker: 5 failures -> 30s open -> half-open -> retry │    │
│  │  Timeout: 30s (content), 60s (image)                          │    │
│  │  Rate Limit: Per-provider, per-tenant                         │    │
│  │  Implementation: Celery tasks with retry policy               │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  PAYMENT PROVIDERS:                                                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Turkey:  Iyzico (Primary)                                    │    │
│  │  Global:  Stripe (Future)                                     │    │
│  │                                                                │    │
│  │  Webhook Events:                                              │    │
│  │  • payment.success -> Activate subscription                   │    │
│  │  • payment.failed -> Notify, retry                            │    │
│  │  • subscription.cancelled -> Downgrade to free                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  EMAIL PROVIDERS:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Transactional: SendGrid / AWS SES (via django-anymail)       │    │
│  │  Marketing:     Mautic (self-hosted)                          │    │
│  │                                                                │    │
│  │  All emails dispatched via Celery tasks (non-blocking)        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  MEDIA SERVICES:                                                        │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Stock Photos:  Unsplash API (free tier)                      │    │
│  │  Image Gen:     DALL-E 3 / Midjourney API                     │    │
│  │  Storage:       Local (MEDIA_ROOT) -> S3 (future)             │    │
│  │  CDN:           Cloudflare (future)                           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Webhook Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       WEBHOOK SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  INBOUND WEBHOOKS (from external services):                             │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  POST /webhooks/iyzico/                                       │    │
│  │  POST /webhooks/stripe/                                       │    │
│  │                                                                │    │
│  │  Security:                                                    │    │
│  │  • Signature verification (HMAC-SHA256)                       │    │
│  │  • CSRF exempt (decorator)                                    │    │
│  │  • Idempotency key check                                      │    │
│  │  • Replay attack prevention (timestamp check)                 │    │
│  │  • Processing delegated to Celery task                        │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  OUTBOUND WEBHOOKS (to customer systems):                               │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Events:                                                      │    │
│  │  • menu.published                                             │    │
│  │  • order.created                                              │    │
│  │  • order.status_changed                                       │    │
│  │  • qr.scanned                                                 │    │
│  │                                                                │    │
│  │  Delivery:                                                    │    │
│  │  • Async via Celery task                                      │    │
│  │  • Retry: 3 attempts (1min, 5min, 30min) using Celery retry   │    │
│  │  • Signature: HMAC-SHA256 with org secret                    │    │
│  │  • Timeout: 10s (requests library)                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. SCALABILITY CONSIDERATIONS

### 6.1 Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SCALING ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PHASE 1 (Current - 500 orgs):                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Single VPS (Hetzner CX21: 2vCPU, 4GB RAM)                   │    │
│  │  ├── Nginx                                                    │    │
│  │  ├── Gunicorn (4 workers, sync)                               │    │
│  │  ├── Celery Worker (1 process, 4 threads)                     │    │
│  │  ├── Celery Beat (scheduler)                                  │    │
│  │  ├── PostgreSQL 15                                            │    │
│  │  └── Redis 7                                                  │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  PHASE 2 (5,000 orgs):                                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Load Balancer                                                │    │
│  │  ├── App Server 1 (Gunicorn: 8 workers)                      │    │
│  │  ├── App Server 2 (Gunicorn: 8 workers)                      │    │
│  │  │                                                            │    │
│  │  ├── Celery Worker Pool (2 servers, autoscale)                │    │
│  │  │                                                            │    │
│  │  ├── PostgreSQL Primary                                       │    │
│  │  │   └── Read Replica                                        │    │
│  │  │                                                            │    │
│  │  └── Redis Cluster                                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  PHASE 3 (50,000 orgs):                                                │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  CDN (Cloudflare)                                             │    │
│  │  ├── Load Balancer (HAProxy/Nginx)                           │    │
│  │  │   ├── Gunicorn App Pool (auto-scaling)                    │    │
│  │  │   └── Celery Worker Pool (auto-scaling, priority queues)  │    │
│  │  │                                                            │    │
│  │  ├── PostgreSQL Cluster                                       │    │
│  │  │   ├── Primary                                             │    │
│  │  │   ├── Read Replica 1                                      │    │
│  │  │   └── Read Replica 2                                      │    │
│  │  │                                                            │    │
│  │  ├── Redis Cluster (Sentinel)                                │    │
│  │  │                                                            │    │
│  │  └── S3 Compatible Storage (media)                           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CACHING LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LAYER 1: Browser Cache                                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Static Assets: 30 days (ManifestStaticFilesStorage hashes)   │    │
│  │  API Responses: No cache (Cache-Control: private)             │    │
│  │  Public Menus: 5 min (stale-while-revalidate)                │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  LAYER 2: Application Cache (Django cache framework + Redis)            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Session Data:        Redis-backed sessions, 15 min TTL       │    │
│  │  User Permissions:    5 min TTL (invalidate on change)        │    │
│  │  Organization Config: 10 min TTL                              │    │
│  │  Public Menu:         5 min TTL                               │    │
│  │  Rate Limit Counters: 1 min sliding window                    │    │
│  │  AI Response Cache:   24 hour TTL (same prompt hash)          │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  LAYER 3: Database Query Cache                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Django ORM: Connection pooling (django-db-connection-pool)   │    │
│  │  PostgreSQL: shared_buffers = 25% RAM                         │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  CACHE KEY PATTERNS:                                                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  user:{userId}:permissions                                    │    │
│  │  org:{orgId}:config                                           │    │
│  │  org:{orgId}:plan                                             │    │
│  │  menu:{menuId}:public                                         │    │
│  │  session:{sessionId}                                          │    │
│  │  rate:{ip}:{endpoint}                                         │    │
│  │  ai:content:{hash(prompt)}                                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. DEPLOYMENT ARCHITECTURE

### 7.1 Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT TOPOLOGY                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        CLOUDFLARE                               │   │
│  │  DNS | DDoS Protection | SSL Edge | (Future: CDN)              │   │
│  └────────────────────────────┬────────────────────────────────────┘   │
│                               │                                        │
│                               ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     HETZNER VPS (CX21)                          │   │
│  │  ┌───────────────────────────────────────────────────────────┐ │   │
│  │  │                      COOLIFY                              │ │   │
│  │  │  (Self-hosted PaaS - Docker orchestration)               │ │   │
│  │  └───────────────────────────────────────────────────────────┘ │   │
│  │                               │                                │   │
│  │  ┌───────────────────────────┴───────────────────────────┐    │   │
│  │  │                                                       │    │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │    │   │
│  │  │  │   NGINX     │  │  GUNICORN   │  │   CELERY    │   │    │   │
│  │  │  │  (Proxy)    │  │  (Django)   │  │  (Worker +  │   │    │   │
│  │  │  │  Port 80/443│  │  Port 8000  │  │   Beat)     │   │    │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘   │    │   │
│  │  │                                                       │    │   │
│  │  │  ┌─────────────┐  ┌─────────────┐                    │    │   │
│  │  │  │ PostgreSQL  │  │   Redis     │                    │    │   │
│  │  │  │  Port 5432  │  │  Port 6379  │                    │    │   │
│  │  │  └─────────────┘  └─────────────┘                    │    │   │
│  │  │                                                       │    │   │
│  │  └───────────────────────────────────────────────────────┘    │   │
│  │                                                                │   │
│  │  Storage:                                                      │   │
│  │  ├── /var/lib/postgresql/data (DB)                            │   │
│  │  ├── /var/lib/redis (Cache + Broker)                          │   │
│  │  └── /app/media (Uploads - future: S3)                        │   │
│  │                                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CI/CD PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DEVELOPMENT FLOW:                                                      │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Local   │───►│  Feature │───►│  Develop │───►│   Main   │         │
│  │   Dev    │    │  Branch  │    │  Branch  │    │  Branch  │         │
│  └──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│                       │               │               │                │
│                       ▼               ▼               ▼                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    GITHUB ACTIONS                                │ │
│  │                                                                  │ │
│  │  on: push                                                       │ │
│  │  ├── Lint (ruff check)                                          │ │
│  │  ├── Format (ruff format --check)                               │ │
│  │  ├── Type Check (mypy)                                          │ │
│  │  ├── Unit Tests (pytest)                                        │ │
│  │  ├── Integration Tests (pytest + PostgreSQL service)            │ │
│  │  └── Django Check (manage.py check --deploy)                    │ │
│  │                                                                  │ │
│  │  on: push to main                                               │ │
│  │  ├── All above +                                               │ │
│  │  ├── E2E Tests (Playwright)                                    │ │
│  │  ├── Security Scan (safety / bandit)                           │ │
│  │  ├── Migration Check (manage.py migrate --check)               │ │
│  │  └── Deploy to Coolify (webhook)                               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  DEPLOYMENT:                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  GitHub Webhook -> Coolify -> Pull -> Build -> collectstatic    │ │
│  │  -> migrate -> Deploy -> Health Check                           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ROLLBACK:                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Manual trigger in Coolify -> Previous image -> Deploy          │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Environment Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       ENVIRONMENT MATRIX                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┬─────────────┬─────────────┬─────────────┐           │
│  │   Variable   │    Local    │   Staging   │  Production │           │
│  ├──────────────┼─────────────┼─────────────┼─────────────┤           │
│  │ DJANGO_ENV   │ development │ staging     │ production  │           │
│  │ DEBUG        │ True        │ False       │ False       │           │
│  │ DATABASE_URL │ localhost   │ staging-db  │ prod-db     │           │
│  │ REDIS_URL    │ localhost   │ staging-redis│ prod-redis │           │
│  │ SECRET_KEY   │ dev-secret  │ staging-*** │ prod-***    │           │
│  │ AI_PROVIDER  │ mock        │ claude      │ claude      │           │
│  │ LOG_LEVEL    │ DEBUG       │ INFO        │ WARNING     │           │
│  │ CELERY_BROKER│ localhost   │ staging-redis│ prod-redis │           │
│  └──────────────┴─────────────┴─────────────┴─────────────┘           │
│                                                                         │
│  SECRET MANAGEMENT:                                                     │
│  ├── Local: .env file (git-ignored), loaded by django-environ          │
│  ├── CI: GitHub Secrets                                               │
│  └── Production: Coolify Environment Variables                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. MONITORING & OBSERVABILITY

### 8.1 Logging Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LOGGING ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  LOG LEVELS (Python logging):                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  CRITICAL → System failures, unrecoverable errors              │    │
│  │  ERROR    → Unhandled exceptions, integration failures         │    │
│  │  WARNING  → Recoverable issues, deprecations                   │    │
│  │  INFO     → Business events, state changes                     │    │
│  │  DEBUG    → Detailed flow (dev only)                           │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  LOG FORMAT (JSON via python-json-logger):                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  {                                                            │    │
│  │    "timestamp": "ISO8601",                                    │    │
│  │    "level": "INFO",                                           │    │
│  │    "message": "Order created",                                │    │
│  │    "logger": "apps.orders.views",                             │    │
│  │    "request_id": "uuid",                                      │    │
│  │    "user_id": "uuid",                                         │    │
│  │    "org_id": "uuid",                                          │    │
│  │    "duration_ms": 45                                          │    │
│  │  }                                                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  LOG DESTINATIONS:                                                      │
│  ├── Development: Console (colorized, verbose)                         │
│  ├── Production: stdout -> Coolify logs -> (future: Loki/ELK)         │
│  └── Errors: Sentry (future)                                          │
│                                                                         │
│  DJANGO LOGGING CONFIG (settings.py LOGGING dict):                      │
│  ├── django.request   -> WARNING                                       │
│  ├── django.db        -> WARNING (INFO to see SQL in dev)              │
│  ├── celery           -> INFO                                          │
│  └── apps.*           -> INFO (DEBUG in dev)                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Health Checks

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HEALTH ENDPOINTS                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GET /health/                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  {                                                            │    │
│  │    "status": "healthy",                                       │    │
│  │    "timestamp": "ISO8601",                                    │    │
│  │    "version": "1.0.0",                                        │    │
│  │    "uptime": 3600                                             │    │
│  │  }                                                            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  GET /health/ready/ (readiness probe)                                   │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Checks:                                                      │    │
│  │  ├── Database connection (SELECT 1)                           │    │
│  │  ├── Redis connection (PING)                                  │    │
│  │  ├── Celery broker reachable                                  │    │
│  │  └── Migrations applied                                       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  GET /health/live/ (liveness probe)                                     │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Checks:                                                      │    │
│  │  └── Django process responsive (200 OK)                       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. DISASTER RECOVERY

### 9.1 Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | pg_dump + S3 | Daily | 30 days |
| Redis | RDB snapshot | Hourly | 7 days |
| Media files | rsync + S3 | Daily | 90 days |
| Configs | Git | Every change | Forever |

### 9.2 Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| App server failure | 5 min | 0 (stateless) |
| Database failure | 30 min | 1 hour |
| Complete DC failure | 4 hour | 24 hour |
| Celery worker failure | 2 min | 0 (tasks re-queued) |

---

*This document defines the technical architecture of the E-Menum platform. All implementations must be consistent with this design.*
