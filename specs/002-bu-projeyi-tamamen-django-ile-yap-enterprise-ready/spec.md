# Specification: E-Menum Django Migration - Enterprise QR Menu SaaS

## Overview

E-Menum is an enterprise-grade QR menu SaaS platform for restaurants, cafes, and F&B businesses in Turkey (350,000+ potential customers). This specification defines the complete migration from the current Express.js/TypeScript stack to a Django-based enterprise-ready modular architecture. The platform provides AI-powered digital menus, order management, analytics, and multi-tenant operations supporting multiple subscription tiers (Free to Enterprise at ₺2K-8K/month).

The migration will preserve all existing business logic, data models, and domain rules while leveraging Django's batteries-included approach for authentication, admin, ORM, and REST API capabilities. The modular architecture will enable feature isolation, independent deployment of modules, and easier maintenance.

## Workflow Type

**Type**: migration

**Rationale**: This is a complete technology stack migration from Express.js + TypeScript + Prisma to Django + Python + Django ORM. It requires:
- Full domain model recreation in Django models
- API endpoint reimplementation with Django REST Framework
- Authentication/authorization system migration
- Admin panel migration from EJS to Django Admin
- Multi-tenant architecture adaptation
- Template system migration (EJS → Django Templates)

## Task Scope

### Services Involved
- **e-menum-django** (primary) - Complete Django application with modular architecture
- **PostgreSQL** (database) - Existing PostgreSQL database (schema recreation)
- **Redis** (cache/queue) - Celery task queue and caching layer

### This Task Will:
- [ ] Create Django project with enterprise-ready configuration (settings split by environment)
- [ ] Implement modular Django app architecture mirroring existing module system
- [ ] Recreate all Prisma models as Django ORM models with multi-tenancy support
- [ ] Implement JWT authentication with djangorestframework-simplejwt
- [ ] Create RBAC/ABAC authorization using django-guardian and custom permissions
- [ ] Build REST API with Django REST Framework following existing API contracts
- [ ] Configure Celery for async task processing (AI content generation, analytics)
- [ ] Implement Django Admin customization for tenant administration
- [ ] Create Django templates for SSR views (menu display, public pages)
- [ ] Set up production deployment configuration (Gunicorn + Nginx)
- [ ] Implement comprehensive test suite (pytest + pytest-django)

### Out of Scope:
- Data migration scripts (will be separate phase)
- Frontend redesign (preserving existing UI patterns)
- Third-party integration changes (preserving existing integration patterns)
- Mobile app development
- AI model training/fine-tuning

## Service Context

### e-menum-django (Primary Service)

**Tech Stack:**
- Language: Python 3.10+
- Framework: Django 5.0+
- API: Django REST Framework 3.15+
- Authentication: djangorestframework-simplejwt
- Async Tasks: Celery 5.4+ with Redis broker
- Configuration: django-environ
- Permissions: django-guardian (object-level)

**Key Directories:**
```
e_menum/
├── config/                     # Project configuration
│   ├── settings/
│   │   ├── base.py            # Base settings
│   │   ├── development.py     # Dev environment
│   │   ├── staging.py         # Staging environment
│   │   └── production.py      # Production environment
│   ├── urls.py                # Root URL configuration
│   ├── celery.py              # Celery configuration
│   ├── wsgi.py                # WSGI entry point
│   └── asgi.py                # ASGI entry point
│
├── apps/                       # Django applications (modular)
│   ├── core/                  # Core models (Organization, User, Role, Permission)
│   ├── menu/                  # Menu, Category, Product, Theme
│   ├── orders/                # Order, OrderItem, Table, Zone, QRCode
│   ├── subscriptions/         # Plan, Subscription, Invoice, Feature
│   ├── customers/             # Customer, Feedback, Loyalty
│   ├── media/                 # Media, MediaFolder
│   ├── notifications/         # Notification system
│   ├── analytics/             # Analytics and reporting
│   └── ai/                    # AI content generation
│
├── shared/                     # Shared utilities
│   ├── middleware/            # Custom middleware
│   ├── permissions/           # CASL-like permission definitions
│   ├── serializers/           # Base serializers
│   ├── views/                 # Base view classes
│   └── utils/                 # Utility functions
│
├── templates/                  # Django templates
│   ├── layouts/               # Base layouts
│   ├── admin/                 # Admin templates
│   ├── public/                # Public-facing templates
│   └── components/            # Reusable components
│
├── static/                     # Static files (CSS, JS, images)
├── locale/                     # Internationalization files (tr, en)
├── tests/                      # Test suite
└── manage.py                   # Django management script
```

**Entry Point:** `e_menum/config/wsgi.py` (production) / `manage.py runserver` (development)

**How to Run:**
```bash
# Development
python manage.py runserver 0.0.0.0:8000

# Production
gunicorn e_menum.config.wsgi:application --bind 0.0.0.0:8000 --workers 3

# Celery Worker (run from project root containing manage.py)
celery -A e_menum.config worker -l INFO
```

**Ports:**
- Django: 8000
- PostgreSQL: 5432
- Redis: 6379

## Files to Create (Core Structure)

| File | Purpose | Priority |
|------|---------|----------|
| `e_menum/config/settings/base.py` | Base Django settings | P0 |
| `e_menum/config/settings/development.py` | Development settings | P0 |
| `e_menum/config/settings/production.py` | Production settings | P0 |
| `e_menum/config/urls.py` | Root URL routing | P0 |
| `e_menum/config/celery.py` | Celery configuration | P1 |
| `e_menum/apps/core/models.py` | Organization, User, Role, Permission | P0 |
| `e_menum/apps/menu/models.py` | Menu, Category, Product, Theme | P0 |
| `e_menum/apps/orders/models.py` | Order, Table, Zone, QRCode | P1 |
| `e_menum/apps/subscriptions/models.py` | Plan, Subscription, Invoice | P1 |
| `e_menum/apps/customers/models.py` | Customer, Feedback, Loyalty | P2 |
| `e_menum/shared/middleware/tenant.py` | Multi-tenant middleware | P0 |
| `e_menum/shared/permissions/abilities.py` | CASL-like permissions | P0 |
| `requirements.txt` | Python dependencies | P0 |
| `requirements-dev.txt` | Development dependencies | P0 |
| `.env.example` | Environment variables template | P0 |
| `Dockerfile` | Docker configuration | P2 |
| `docker-compose.yml` | Docker Compose for local dev | P2 |

## Files to Reference

These files from the existing codebase show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `prisma/schema/core.prisma` | Organization, User, Role, Permission model structure |
| `prisma/schema/menu.prisma` | Menu, Category, Product, Theme model structure |
| `prisma/schema/order.prisma` | Order, Table, Zone, QRCode model structure |
| `prisma/schema/subscription.prisma` | Plan, Subscription, Invoice model structure |
| `prisma/schema/base.prisma` | Enums and status definitions |
| `CLAUDE.md` | Business rules, critical constraints, domain model |

## Domain Model Mapping (Prisma → Django)

### Core Module Models

```python
# apps/core/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

class Organization(models.Model):
    """Tenant root - multi-tenancy anchor"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    settings = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('DELETED', 'Deleted'),
    ], default='ACTIVE')
    plan = models.ForeignKey('subscriptions.Plan', on_delete=models.SET_NULL, null=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete

    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['status', 'deleted_at']),
        ]


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'ACTIVE')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User accounts with optional organization membership"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('INVITED', 'Invited'),
        ('SUSPENDED', 'Suspended'),
    ], default='ACTIVE')
    is_staff = models.BooleanField(default=False)  # Required for Django admin
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'deleted_at']),
        ]


class Role(models.Model):
    """Roles for RBAC"""
    SCOPE_CHOICES = [
        ('PLATFORM', 'Platform'),
        ('ORGANIZATION', 'Organization'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='ORGANIZATION')
    is_system = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, related_name='roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        unique_together = [['name', 'scope', 'organization']]
        indexes = [
            models.Index(fields=['scope']),
        ]
```

### Menu Module Models

```python
# apps/menu/models.py

from django.db import models
from decimal import Decimal
import uuid

class Theme(models.Model):
    """Menu styling customization"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='themes')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#10B981')
    background_color = models.CharField(max_length=7, default='#FFFFFF')
    text_color = models.CharField(max_length=7, default='#1F2937')
    font_family = models.CharField(max_length=50, default='Inter')
    logo_position = models.CharField(max_length=20, default='left')
    custom_css = models.TextField(blank=True, null=True)
    settings = models.JSONField(default=dict)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'themes'
        unique_together = [['organization', 'slug']]


class Menu(models.Model):
    """Restaurant menu container"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True, related_name='menus')
    settings = models.JSONField(default=dict)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'menus'
        unique_together = [['organization', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_published']),
            models.Index(fields=['organization', 'deleted_at']),
        ]


class Category(models.Model):
    """Product categories with nested support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='categories')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='categories')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'categories'
        unique_together = [['menu', 'slug']]


class Product(models.Model):
    """Individual menu items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    short_description = models.CharField(max_length=100, blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='TRY')
    image = models.URLField(blank=True, null=True)
    gallery = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_chef_recommended = models.BooleanField(default=False)
    preparation_time = models.IntegerField(null=True, blank=True)  # minutes
    calories = models.IntegerField(null=True, blank=True)
    spicy_level = models.SmallIntegerField(null=True, blank=True)  # 0-5
    tags = models.JSONField(default=list)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'products'
        unique_together = [['category', 'slug']]
        indexes = [
            models.Index(fields=['organization', 'is_active', 'is_available']),
            models.Index(fields=['organization', 'is_featured']),
        ]
```

### Additional Models (from Prisma Schema)

The following models are also required based on the existing Prisma schema:

#### Core Module (apps/core/)
- `Branch` - Multi-location support with hierarchical structure
- `Session` - JWT refresh token management
- `Permission` - Granular resource.action permissions
- `UserRole` - Junction table linking users to roles
- `RolePermission` - Junction table linking roles to permissions
- `AuditLog` - System-wide audit logging

#### Menu Module (apps/menu/)
- `ProductVariant` - Size/portion options (Small, Medium, Large)
- `ProductModifier` - Add-on options (Extra Cheese, No Onions)
- `Allergen` - Platform-level allergen definitions
- `ProductAllergen` - Junction table for product-allergen relationships
- `NutritionInfo` - One-to-one nutritional data per product

#### Orders Module (apps/orders/)
- `Zone` - Table groupings (Garden, Indoor, VIP Section)
- `Table` - Physical restaurant tables
- `QRCode` - Generated QR codes for menus/tables
- `QRScan` - QR code scan tracking for analytics
- `Order` - Customer orders with full transaction details
- `OrderItem` - Individual line items within orders
- `ServiceRequest` - Waiter call/service requests from tables

#### Customers Module (apps/customers/)
- `Customer` - End customers who place orders
- `CustomerVisit` - Visit tracking for analytics
- `Feedback` - Customer feedback and ratings
- `LoyaltyPoint` - Loyalty points ledger

#### Subscriptions Module (apps/subscriptions/)
- `Plan` - Subscription tiers (Free, Starter, Professional, Business, Enterprise)
- `Subscription` - Organization-Plan relationship with billing
- `Invoice` - Billing records for subscriptions
- `Feature` - Individual capabilities enabled per plan
- `PlanFeature` - Junction table for plan-feature relationships
- `OrganizationUsage` - Resource usage tracking per organization

#### Media Module (apps/media/)
- `Media` - Uploaded files (images, documents)
- `MediaFolder` - Virtual folders for organization

#### Notifications Module (apps/notifications/)
- `Notification` - User notifications for orders, system, promotions

### Django Enums (Required)

All enums from Prisma schema need Django TextChoices equivalents:

```python
# apps/core/choices.py

from django.db import models

class OrganizationStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    DELETED = 'DELETED', 'Deleted'

class UserStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INVITED = 'INVITED', 'Invited'
    SUSPENDED = 'SUSPENDED', 'Suspended'

class BranchStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'

class RoleScope(models.TextChoices):
    PLATFORM = 'PLATFORM', 'Platform'
    ORGANIZATION = 'ORGANIZATION', 'Organization'

class TableStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    OCCUPIED = 'OCCUPIED', 'Occupied'
    RESERVED = 'RESERVED', 'Reserved'

class QRCodeType(models.TextChoices):
    MENU = 'MENU', 'Menu'
    TABLE = 'TABLE', 'Table'
    CAMPAIGN = 'CAMPAIGN', 'Campaign'

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    PREPARING = 'PREPARING', 'Preparing'
    READY = 'READY', 'Ready'
    DELIVERED = 'DELIVERED', 'Delivered'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class OrderType(models.TextChoices):
    DINE_IN = 'DINE_IN', 'Dine In'
    TAKEAWAY = 'TAKEAWAY', 'Takeaway'
    DELIVERY = 'DELIVERY', 'Delivery'

class SubscriptionStatus(models.TextChoices):
    TRIALING = 'TRIALING', 'Trialing'
    ACTIVE = 'ACTIVE', 'Active'
    PAST_DUE = 'PAST_DUE', 'Past Due'
    CANCELLED = 'CANCELLED', 'Cancelled'
    PAUSED = 'PAUSED', 'Paused'

class InvoiceStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
    OVERDUE = 'OVERDUE', 'Overdue'
    CANCELLED = 'CANCELLED', 'Cancelled'
    REFUNDED = 'REFUNDED', 'Refunded'

class PaymentMethod(models.TextChoices):
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    CASH = 'CASH', 'Cash'
```

## Patterns to Follow

### Multi-Tenancy Pattern

Every query MUST include organization filtering:

```python
# CORRECT
def get_menus(request):
    return Menu.objects.filter(
        organization=request.organization,
        deleted_at__isnull=True
    )

# INCORRECT - SECURITY VIOLATION
def get_menus(request):
    return Menu.objects.all()  # Exposes ALL tenant data!
```

### Soft Delete Pattern

Never use hard deletes:

```python
# CORRECT
def soft_delete(instance):
    instance.deleted_at = timezone.now()
    instance.save()

# INCORRECT
def delete(instance):
    instance.delete()  # Physical deletion FORBIDDEN
```

### Authorization Pattern

Every view must have permission checks:

```python
from rest_framework.decorators import permission_classes
from shared.permissions import HasOrganizationPermission

# CORRECT
@permission_classes([HasOrganizationPermission('menu.view')])
class MenuViewSet(viewsets.ModelViewSet):
    pass

# INCORRECT
class MenuViewSet(viewsets.ModelViewSet):
    pass  # No protection!
```

### API Response Pattern

Standard JSON response format:

```python
# Success
{
    "success": True,
    "data": {...}
}

# Success with pagination
{
    "success": True,
    "data": [...],
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 150,
        "total_pages": 8
    }
}

# Error
{
    "success": False,
    "error": {
        "code": "MENU_NOT_FOUND",
        "message": "Menu with given ID not found",
        "details": {...}
    }
}
```

## Requirements

### Functional Requirements

1. **Multi-Tenant Architecture**
   - Description: Complete tenant isolation via organization_id on all models
   - Acceptance: No data leaks between organizations; all queries scoped to tenant

2. **User Authentication (JWT)**
   - Description: JWT-based authentication with access/refresh tokens
   - Acceptance: Login returns tokens; protected endpoints validate JWT; refresh token works

3. **Role-Based Access Control**
   - Description: RBAC with organization-scoped and platform-scoped roles
   - Acceptance: Users with different roles have appropriate access; unauthorized actions blocked

4. **Menu Management**
   - Description: CRUD operations for menus, categories, products with variants/modifiers
   - Acceptance: All menu operations work; hierarchical categories supported; product variants functional

5. **Order Management**
   - Description: Order creation, status workflow, table management
   - Acceptance: Orders can be created from menu; status transitions work; table assignment functional

6. **QR Code Generation**
   - Description: Generate QR codes linked to menus/tables with scan tracking
   - Acceptance: QR codes generated; scans tracked; redirect to correct menu

7. **Subscription & Billing**
   - Description: Plan management, subscription lifecycle, usage tracking
   - Acceptance: Organizations can subscribe to plans; limits enforced; usage tracked

8. **Internationalization (i18n)**
   - Description: Turkish and English language support
   - Acceptance: All UI strings translated; language switching works; no hardcoded strings

9. **Admin Dashboard**
   - Description: Django Admin customization for tenant management
   - Acceptance: Admins can manage organizations, users, subscriptions via admin panel

10. **Async Task Processing**
    - Description: Celery-based background jobs for AI generation, analytics
    - Acceptance: Tasks queued and processed; results delivered; failures handled

### Edge Cases

1. **Concurrent Updates** - Use optimistic locking with `updated_at` field comparison
2. **Orphaned Resources** - Implement cascade delete rules in models
3. **Plan Limit Exceeded** - Return 403 with clear error message and upgrade path
4. **Invalid QR Code** - Graceful error page with organization contact info
5. **Session Expiry** - Redirect to login with return URL preserved
6. **Database Connection Loss** - Retry logic with exponential backoff

## Implementation Notes

### DO
- Follow Django's MTV (Model-Template-View) pattern
- Use class-based views and viewsets for consistency
- Implement custom managers for common queries (e.g., `ActiveManager`)
- Use signals for audit logging
- Leverage Django's built-in security features (CSRF, XSS protection)
- Use `select_related` and `prefetch_related` for query optimization
- Implement proper pagination for all list endpoints
- Use environment variables for all configuration (django-environ)
- Write comprehensive docstrings for all public APIs
- Use `delay_on_commit()` for Celery tasks to prevent DB race conditions

### DON'T
- Don't use raw SQL except for complex analytics queries
- Don't hardcode organization IDs or skip tenant filtering
- Don't store sensitive data in plaintext
- Don't use synchronous operations for long-running tasks
- Don't skip migrations - always create and apply properly
- Don't bypass permission checks for "admin convenience"
- Don't use `*` imports
- Don't commit `.env` files or secrets

### Middleware Order (Critical)

The middleware order in `settings/base.py` is critical for proper functionality:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Must be after SecurityMiddleware
    'corsheaders.middleware.CorsMiddleware',  # Must be high, before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shared.middleware.tenant.TenantMiddleware',  # After AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Key Rules:**
- WhiteNoise: After `SecurityMiddleware`, before all others
- CorsMiddleware: As high as possible, definitely before `CommonMiddleware`
- TenantMiddleware: After `AuthenticationMiddleware` (needs user context)

### INSTALLED_APPS Configuration

```python
INSTALLED_APPS = [
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For logout functionality
    'django_filters',
    'corsheaders',
    'guardian',

    # E-Menum Apps
    'apps.core.apps.CoreConfig',
    'apps.menu.apps.MenuConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.subscriptions.apps.SubscriptionsConfig',
    'apps.customers.apps.CustomersConfig',
    'apps.media.apps.MediaConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.analytics.apps.AnalyticsConfig',
    'apps.ai.apps.AiConfig',
]

# Development only
if DEBUG:
    INSTALLED_APPS += [
        'django_extensions',
        'debug_toolbar',
    ]
```

### Authentication Backends (for django-guardian)

```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]
```

## Development Environment

### Prerequisites

```bash
# Required
Python 3.10+
PostgreSQL 15+
Redis 7+

# Optional
Docker & Docker Compose
```

### Python Dependencies (requirements.txt)

```txt
# Core Framework
Django>=5.0,<6.0

# REST API
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
django-filter>=25.0
django-cors-headers>=4.3

# Database
psycopg[binary]>=3.1,<4.0
dj-database-url>=2.1

# Configuration
django-environ>=0.12

# Permissions
django-guardian>=2.4

# Async Tasks
celery[redis]>=5.4,<6.0

# Caching
django-redis>=5.4

# Static Files (Production)
whitenoise>=6.6

# Production Server
gunicorn>=21.0
```

### Python Dev Dependencies (requirements-dev.txt)

```txt
# Testing
pytest>=8.0
pytest-django>=4.7
pytest-cov>=4.1
factory-boy>=3.3

# Development Tools
django-extensions>=3.2
werkzeug>=3.0  # For runserver_plus debugger

# Code Quality
black>=24.0
ruff>=0.2
mypy>=1.8
django-stubs>=4.2

# Debugging
django-debug-toolbar>=4.2

# Monitoring (Optional - Production)
sentry-sdk[django]>=1.40
```

### Initial Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed initial data
python manage.py loaddata initial_data
```

### Start Services

```bash
# Start Django development server
python manage.py runserver 0.0.0.0:8000

# Start Celery worker (separate terminal, from project root)
celery -A e_menum.config worker -l INFO

# Start Celery beat (separate terminal, for periodic tasks)
celery -A e_menum.config beat -l INFO
```

### Service URLs
- Django App: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- API Documentation: http://localhost:8000/api/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Required Environment Variables
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/emenum

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15  # minutes
JWT_REFRESH_TOKEN_LIFETIME=10080  # minutes (7 days)

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Success Criteria

The task is complete when:

1. [ ] Django project structure created with modular app architecture
2. [ ] All core models implemented (Organization, User, Role, Permission, Session)
3. [ ] All menu models implemented (Menu, Category, Product, Variant, Modifier, Theme)
4. [ ] All order models implemented (Order, OrderItem, Table, Zone, QRCode)
5. [ ] All subscription models implemented (Plan, Subscription, Invoice, Feature)
6. [ ] JWT authentication working (login, logout, refresh)
7. [ ] RBAC permissions implemented and enforced
8. [ ] Multi-tenant middleware filtering all queries
9. [ ] Django Admin configured for administrative tasks
10. [ ] REST API endpoints created with DRF
11. [ ] Celery configured and processing tasks
12. [ ] i18n configured for Turkish and English
13. [ ] All migrations created and applied successfully
14. [ ] No console errors or warnings
15. [ ] Existing tests passing (if any)
16. [ ] New functionality verified via browser/API

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| Model Creation | `tests/core/test_models.py` | All models can be created with valid data |
| Soft Delete | `tests/core/test_soft_delete.py` | Objects marked as deleted, not physically removed |
| Permission Check | `tests/shared/test_permissions.py` | Permission decorators work correctly |
| JWT Auth | `tests/core/test_auth.py` | Token generation and validation works |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| API CRUD | Django ↔ PostgreSQL | Full CRUD operations on all endpoints |
| Auth Flow | Django ↔ Redis | JWT tokens stored and validated properly |
| Celery Tasks | Django ↔ Redis ↔ Celery | Tasks queued and processed successfully |
| Multi-Tenancy | Django ↔ PostgreSQL | Tenant isolation enforced in all queries |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| User Registration | 1. Register 2. Verify email 3. Login | User can access dashboard |
| Menu Creation | 1. Login 2. Create menu 3. Add category 4. Add product | Menu displayed in public view |
| Order Flow | 1. Scan QR 2. Add items 3. Place order | Order appears in admin, status updates work |
| Subscription | 1. Login 2. Select plan 3. Subscribe | Organization has active subscription |

### Browser Verification (if frontend)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| Admin Dashboard | `http://localhost:8000/admin` | Login works, dashboard renders |
| API Docs | `http://localhost:8000/api/docs` | Swagger UI loads correctly |
| Public Menu | `http://localhost:8000/m/{slug}` | Menu renders with products |

### Database Verification
| Check | Query/Command | Expected |
|-------|---------------|----------|
| Migrations Applied | `python manage.py showmigrations` | All migrations marked as [X] |
| Tables Created | `\dt` in psql | All model tables exist |
| Indexes Created | `\di` in psql | All defined indexes present |

### QA Sign-off Requirements
- [ ] All unit tests pass (pytest with 80%+ coverage)
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Browser verification complete
- [ ] Database state verified
- [ ] No regressions in existing functionality
- [ ] Code follows established patterns (Django conventions)
- [ ] No security vulnerabilities introduced
- [ ] Multi-tenancy verified (no data leaks)
- [ ] API response format matches specification
- [ ] i18n working for both TR and EN

---

## Appendix A: Role Definitions

| Role | Scope | Permissions |
|------|-------|-------------|
| `super_admin` | PLATFORM | Full system access |
| `admin` | PLATFORM | Customer, billing, support management |
| `sales` | PLATFORM | CRM, lead management |
| `support` | PLATFORM | Support tickets only |
| `owner` | ORGANIZATION | Full organization access, billing |
| `manager` | ORGANIZATION | Menu, order, staff management |
| `staff` | ORGANIZATION | Order taking, table management |
| `viewer` | ORGANIZATION | Read-only dashboard |

## Appendix B: Plan Limits

| Plan | Menus | Products | QR Codes | Users | Storage | AI Credits |
|------|-------|----------|----------|-------|---------|------------|
| Free | 1 | 50 | 3 | 2 | 100MB | 0 |
| Starter (₺2K) | 3 | 200 | 10 | 5 | 500MB | 100 |
| Professional (₺4K) | 10 | 500 | 50 | 15 | 2GB | 500 |
| Business (₺6K) | 25 | 1000 | 100 | 30 | 5GB | 1000 |
| Enterprise (₺8K+) | ∞ | ∞ | ∞ | ∞ | 20GB | ∞ |

## Appendix C: API Endpoint Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/` | User login, returns JWT |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| GET | `/api/v1/menus/` | List organization menus |
| POST | `/api/v1/menus/` | Create new menu |
| GET | `/api/v1/menus/{id}/` | Get menu details |
| PUT | `/api/v1/menus/{id}/` | Update menu |
| DELETE | `/api/v1/menus/{id}/` | Soft delete menu |
| GET | `/api/v1/categories/` | List categories |
| POST | `/api/v1/categories/` | Create category |
| GET | `/api/v1/products/` | List products |
| POST | `/api/v1/products/` | Create product |
| GET | `/api/v1/orders/` | List orders |
| POST | `/api/v1/orders/` | Create order |
| PATCH | `/api/v1/orders/{id}/status/` | Update order status |
| GET | `/api/v1/qr-codes/` | List QR codes |
| POST | `/api/v1/qr-codes/` | Generate QR code |

---

*Document Version: 1.0*
*Generated: 2026-02-14*
*Target Stack: Django 5.0+ / Python 3.10+ / PostgreSQL 15+ / Redis 7+*
