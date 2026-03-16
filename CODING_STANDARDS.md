# E-Menum Coding Standards

> **Auto-Claude Coding Standards Document**
> Python/Django conventions, naming, patterns, Git workflow.
> Son Guncelleme: 2026-03-16

---

## 1. GENERAL PRINCIPLES

### 1.1 Core Philosophy

| Principle | Description |
|-----------|-------------|
| **Readability First** | Code is read 10x more than written |
| **Explicit over Implicit** | No magic, clear intentions |
| **Consistency** | Same problem, same solution |
| **Fail Fast** | Validate early, error clearly |
| **DRY but DAMP** | Don't repeat, but descriptive is okay |

### 1.2 LLM-Friendly Code Patterns

```
LLM-Friendly Code Patterns:

DO:
  - Use established patterns (BaseTenantViewSet, SoftDeleteMixin)
  - Type hints on all public functions
  - Docstrings on modules, classes, and public methods
  - Consistent file structure per app
  - Descriptive variable names
  - Small, focused functions (<30 lines)

DON'T:
  - Custom abstractions without examples
  - Magic strings or numbers
  - Circular imports
  - Deep nesting (>3 levels)
  - Side effects in unexpected places
  - Bare except clauses
```

---

## 2. PYTHON CONVENTIONS

### 2.1 Type Hints

```python
# GOOD: Type hints on public methods
from __future__ import annotations
from typing import Optional
from apps.menu.models import Menu

def get_menu_by_id(menu_id: str, org_id: str) -> Optional[Menu]:
    return Menu.objects.filter(id=menu_id, organization_id=org_id).first()

# GOOD: Complex return types
def get_dashboard_data(org_id: str) -> dict[str, Any]:
    ...

# BAD: No type hints on public API
def process_data(data):  # Missing types!
    return [x.value for x in data]
```

### 2.2 Enums & Choices

```python
# Use Django TextChoices for database-backed enums
class OrderStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    CONFIRMED = "confirmed", _("Confirmed")
    PREPARING = "preparing", _("Preparing")
    READY = "ready", _("Ready")
    DELIVERED = "delivered", _("Delivered")
    CANCELLED = "cancelled", _("Cancelled")

# Use in model fields
status = models.CharField(
    max_length=20,
    choices=OrderStatus.choices,
    default=OrderStatus.PENDING,
)

# BAD: Plain strings without choices
status = models.CharField(max_length=20, default="pending")  # No validation!
```

### 2.3 None / Null Handling

```python
# GOOD: Explicit None checks with AppException
def get_menu(menu_id: str, org_id: str) -> Menu:
    menu = Menu.objects.filter(
        id=menu_id, organization_id=org_id
    ).first()
    if menu is None:
        raise ResourceNotFoundException("Menu", menu_id)
    return menu

# GOOD: get_object_or_404 for simple cases
from django.shortcuts import get_object_or_404
menu = get_object_or_404(Menu, id=menu_id, organization_id=org_id)

# BAD: Accessing attributes without null check
menu = Menu.objects.filter(id=menu_id).first()
return menu.name  # AttributeError if None!
```

---

## 3. NAMING CONVENTIONS

### 3.1 Files & Folders

```
Files:
  snake_case.py          # All Python files
  test_module.py         # Test files (test_ prefix)
  conftest.py            # pytest fixtures
  UPPER_CASE.md          # Documentation

Folders:
  snake_case/            # Django apps and packages
  tests/                 # Test directories
  migrations/            # Django migrations

Examples (menu app):
  apps/menu/
    __init__.py
    models.py
    views.py
    serializers.py
    urls.py
    admin.py
    services.py           # Business logic (optional)
    tasks.py              # Celery tasks (optional)
    signals.py            # Django signals (optional)
    tests/
      __init__.py
      test_views.py
      test_models.py
      test_services.py
```

### 3.2 Variables & Functions

```python
# Variables: snake_case
menu_items = []
is_active = True
has_permission = False
current_page = 1

# Constants: SCREAMING_SNAKE_CASE (module-level)
MAX_ITEMS_PER_PAGE = 100
DEFAULT_CURRENCY = "TRY"
API_VERSION = "v1"

# Functions: snake_case, verb prefix
def get_menu_by_id(menu_id: str) -> Menu: ...
def create_order(data: dict) -> Order: ...
def validate_email(email: str) -> bool: ...
def is_valid_price(price: Decimal) -> bool: ...
def has_permission(user: User, action: str) -> bool: ...

# Boolean variables: is/has/can/should prefix
is_loading = True
has_error = False
can_edit = user.role == "owner"
should_refresh = last_update < threshold
```

### 3.3 Classes

```python
# Models: PascalCase, singular noun
class Menu(models.Model): ...
class Category(models.Model): ...
class OrderItem(models.Model): ...

# ViewSets: PascalCase + ViewSet suffix
class MenuViewSet(BaseTenantViewSet): ...
class CategoryViewSet(BaseTenantViewSet): ...

# Serializers: PascalCase + Serializer suffix
class MenuCreateSerializer(TenantModelSerializer): ...
class MenuListSerializer(TenantModelSerializer): ...

# Mixins: PascalCase + Mixin suffix
class SoftDeleteMixin(models.Model): ...
class PlanEnforcementMixin: ...

# Services: PascalCase + Service suffix (optional layer)
class MenuService: ...
class AnalyticsService: ...
```

### 3.4 Database & API

```python
# Database tables: Django auto-generates as {app_label}_{model_name}
# e.g., menu_menu, menu_category, orders_order

# Database columns: snake_case
class Product(models.Model):
    id = models.UUIDField(primary_key=True)
    category = models.ForeignKey(Category, ...)  # FK
    base_price = models.DecimalField(...)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

# API endpoints: kebab-case plural
# GET  /api/v1/menus/
# GET  /api/v1/menu-items/
# POST /api/v1/qr-codes/

# Query params: snake_case
# GET /api/v1/products/?category_id=xxx&is_active=true&sort_by=name

# JSON keys: snake_case (DRF default)
# {
#   "menu_id": "xxx",
#   "category_name": "Drinks",
#   "is_published": true
# }
```

---

## 4. FILE STRUCTURE PATTERNS

### 4.1 Django App Structure

```
apps/menu/
  __init__.py
  admin.py              # Django admin config
  apps.py               # AppConfig
  models.py             # ORM models
  views.py              # DRF ViewSets + Django views
  serializers.py        # DRF serializers
  urls.py               # URL routing
  services.py           # Business logic (optional)
  tasks.py              # Celery tasks (optional)
  signals.py            # Signal handlers (optional)
  choices.py            # TextChoices enums (if many)
  filters.py            # django-filter FilterSets (optional)
  tests/
    __init__.py
    test_views.py
    test_models.py
    test_services.py
    conftest.py          # App-specific fixtures
```

### 4.2 File Organization Rules

```python
# File order within a module:

# 1. Docstring
"""Menu views for E-Menum."""

# 2. Standard library imports
import logging
from typing import Any, Optional

# 3. Third-party imports
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

# 4. Local app imports
from apps.menu.models import Menu, Category
from apps.menu.serializers import MenuListSerializer, MenuCreateSerializer

# 5. Shared/project imports
from shared.views.base import BaseTenantViewSet
from shared.utils.exceptions import AppException

# 6. Constants
MAX_CATEGORIES = 50

# 7. Module-level logger
logger = logging.getLogger(__name__)

# 8. Classes / Functions
class MenuViewSet(BaseTenantViewSet):
    ...
```

### 4.3 Import Conventions

```python
# GOOD: Explicit imports
from apps.menu.models import Menu, Category
from shared.views.base import BaseTenantViewSet

# GOOD: Grouped and ordered (isort compatible)
# 1. stdlib
# 2. third-party
# 3. django
# 4. drf
# 5. local apps
# 6. shared

# BAD: Wildcard imports
from apps.menu.models import *  # Never do this!

# BAD: Relative imports climbing up
from ...shared.views import BaseTenantViewSet  # Use absolute

# GOOD: Relative imports within same app only
from .models import Menu
from .serializers import MenuCreateSerializer
```

---

## 5. ASYNC & CELERY PATTERNS

### 5.1 Celery Task Best Practices

```python
# GOOD: Celery task with proper error handling
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_notification(self, order_id: str) -> None:
    """Send notification for new order."""
    try:
        order = Order.objects.get(id=order_id)
        # ... send notification
    except Order.DoesNotExist:
        logger.error("Order %s not found", order_id)
        return
    except Exception as exc:
        self.retry(exc=exc)

# GOOD: Pass IDs, not objects (serialization safety)
send_order_notification.delay(str(order.id))

# BAD: Passing ORM objects to tasks
send_order_notification.delay(order)  # Not serializable!
```

### 5.2 QuerySet Performance

```python
# GOOD: Parallel-like with select_related / prefetch_related
def get_dashboard_data(org):
    menus = Menu.objects.filter(
        organization=org
    ).select_related("theme").prefetch_related("categories")

    orders = Order.objects.filter(
        organization=org
    ).select_related("customer")[:10]

    return {"menus": menus, "orders": orders}

# BAD: N+1 queries
menus = Menu.objects.filter(organization=org)
for menu in menus:
    print(menu.theme.name)  # Separate query per menu!

# GOOD: Use .only() / .defer() for large models
products = Product.objects.filter(
    organization=org
).only("id", "name", "base_price", "is_active")
```

---

## 6. ERROR HANDLING

### 6.1 AppException Pattern

```python
# shared/utils/exceptions.py

class AppException(APIException):
    """Custom exception base for E-Menum API errors."""

    def __init__(
        self,
        code: str,
        message: str = "",
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.code = code
        self.detail = {"code": code, "message": message, "details": details}
        self.status_code = status_code
        super().__init__(detail=self.detail)


class ResourceNotFoundException(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, resource_id: str = ""):
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with given ID not found",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )

# Usage:
raise AppException("MENU_ALREADY_EXISTS", "A menu with this slug exists", 409)
raise ResourceNotFoundException("Menu", menu_id)
```

### 6.2 Error Codes Catalog

```python
class ErrorCodes:
    # Authentication
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"

    # Authorization
    FORBIDDEN_NO_PERMISSION = "FORBIDDEN_NO_PERMISSION"
    FORBIDDEN_INSUFFICIENT_PLAN = "FORBIDDEN_INSUFFICIENT_PLAN"

    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"

    # Resources
    # Pattern: {RESOURCE}_NOT_FOUND
    MENU_NOT_FOUND = "MENU_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    # Business Logic
    BUSINESS_PLAN_LIMIT_EXCEEDED = "BUSINESS_PLAN_LIMIT_EXCEEDED"

    # Server
    SERVER_INTERNAL_ERROR = "SERVER_INTERNAL_ERROR"
```

### 6.3 Validation with DRF Serializers

```python
# serializers.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

class MenuCreateSerializer(TenantModelSerializer):
    name = serializers.CharField(
        min_length=1,
        max_length=100,
        error_messages={"blank": _("Name is required")},
    )
    slug = serializers.SlugField(required=False, max_length=120)
    description = serializers.CharField(max_length=500, required=False)
    theme = serializers.PrimaryKeyRelatedField(
        queryset=Theme.objects.all(), required=False
    )

    class Meta:
        model = Menu
        fields = ["name", "slug", "description", "theme"]

    def validate_slug(self, value):
        org = self.context["request"].organization
        if Menu.objects.filter(organization=org, slug=value).exists():
            raise serializers.ValidationError(_("A menu with this slug already exists."))
        return value
```

---

## 7. CODE PATTERNS

### 7.1 ViewSet Pattern (API)

```python
# GOOD: BaseTenantViewSet handles org filtering + soft delete + response format
class MenuViewSet(BaseTenantViewSet):
    """
    CRUD ViewSet for menus.

    Inherits from BaseTenantViewSet which provides:
    - Automatic organization filtering via get_queryset()
    - Soft delete via perform_destroy()
    - Standard JSON response format
    """

    queryset = Menu.objects.all()
    permission_resource = "menu"

    serializer_classes = {
        "list": MenuListSerializer,
        "retrieve": MenuDetailSerializer,
        "create": MenuCreateSerializer,
        "update": MenuUpdateSerializer,
    }

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("theme").order_by("sort_order")

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish a menu."""
        menu = self.get_object()
        menu.is_published = True
        menu.published_at = timezone.now()
        menu.save(update_fields=["is_published", "published_at"])
        serializer = MenuDetailSerializer(menu)
        return self.success_response(serializer.data)
```

### 7.2 Model Pattern

```python
class Menu(TimeStampedMixin, SoftDeleteMixin, models.Model):
    """
    Restaurant menu container.

    Critical Rules:
    - EVERY query MUST filter by organization (multi-tenant)
    - Use soft_delete() - never call delete() directly
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="menus",
        verbose_name=_("Organization"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    slug = models.SlugField(max_length=120, verbose_name=_("Slug"))
    description = models.TextField(blank=True, default="", verbose_name=_("Description"))
    is_published = models.BooleanField(default=False, verbose_name=_("Published"))
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort order"))

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = [("organization", "slug")]
        verbose_name = _("Menu")
        verbose_name_plural = _("Menus")

    def __str__(self) -> str:
        return self.name
```

### 7.3 Django Template View Pattern (Restaurant Portal)

```python
# For SSR views (restaurant panel, admin panel)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

@login_required
def menu_list(request):
    """List menus for the current organization."""
    menus = Menu.objects.filter(
        organization=request.organization
    ).order_by("sort_order")
    return render(request, "modules/menu/list.html", {"menus": menus})

# For superadmin views
from shared.decorators import superadmin_required

@superadmin_required
def admin_dashboard(request):
    """Platform admin dashboard."""
    ...
```

---

## 8. GIT WORKFLOW

### 8.1 Branch Strategy

```
Branch Model: GitHub Flow (simplified)

main (production)
  |
  +-- feature/xxx -----------> PR -> main
  +-- fix/xxx ---------------> PR -> main
  +-- hotfix/xxx ------------> PR -> main (urgent)

Branch Naming:
  feature/menu-variants      # New feature
  fix/order-calculation      # Bug fix
  hotfix/auth-bypass         # Critical fix
  refactor/service-layer     # Code improvement
  docs/api-contracts         # Documentation
  chore/update-deps          # Maintenance
```

### 8.2 Commit Convention

```
Format: <type>(<scope>): <subject>

Types:
  feat     # New feature
  fix      # Bug fix
  docs     # Documentation
  style    # Formatting (no code change)
  refactor # Code restructure
  test     # Adding tests
  chore    # Maintenance
  perf     # Performance

Examples:
  feat(menu): add category reordering
  fix(orders): correct tax calculation
  refactor(auth): extract token service
  test(menu): add viewset unit tests
  chore(deps): update Django to 5.0.4
```

### 8.3 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation

## Checklist
- [ ] Code follows style guide
- [ ] Self-reviewed
- [ ] Tests added/updated
- [ ] No print() or debug code
- [ ] Migrations included (if model changes)
- [ ] PR title follows commit convention
```

### 8.4 Code Review Checklist

```
Correctness:
  - Does it solve the problem?
  - Are edge cases handled?

Security:
  - Tenant isolation maintained? (organization filtering)
  - Input validated via serializers?
  - No sensitive data exposed?

Performance:
  - N+1 queries avoided? (select_related / prefetch_related)
  - Unnecessary DB hits?
  - Pagination used for lists?

Maintainability:
  - Clear naming?
  - Docstrings present?
  - Tests included?
```

---

## 9. DOCUMENTATION

### 9.1 Docstring Standards

```python
def create_menu(org_id: str, data: dict) -> Menu:
    """
    Create a new menu for the organization.

    Args:
        org_id: Organization UUID.
        data: Menu creation data (name, slug, description).

    Returns:
        The created Menu instance.

    Raises:
        AppException: MENU_ALREADY_EXISTS if slug is taken.
        AppException: BUSINESS_PLAN_LIMIT_EXCEEDED if plan limit reached.

    Example:
        menu = create_menu("org_123", {
            "name": "Main Menu",
            "description": "Our main offerings",
        })
    """
    ...


class MenuViewSet(BaseTenantViewSet):
    """
    CRUD ViewSet for restaurant menus.

    Handles menu creation, listing, updating, and soft deletion.
    Enforces tenant isolation and plan-based limits.
    """
    ...
```

### 9.2 Inline Comments

```python
# GOOD: Explain WHY, not WHAT
# Using soft delete to maintain referential integrity with orders
instance.soft_delete()

# GOOD: Explain complex business logic
# Price includes 18% VAT for Turkey, but displayed separately
vat_rate = Decimal("0.18")
base_price = total_price / (1 + vat_rate)
vat_amount = total_price - base_price

# BAD: Obvious comments
# Get the menu
menu = get_menu(menu_id)

# BAD: Outdated comments
# TODO: Remove after Q1 2024  (It's 2026!)
```

---

## 10. LINTING & FORMATTING

### 10.1 Ruff Configuration (recommended)

```toml
# pyproject.toml
[tool.ruff]
target-version = "py313"
line-length = 120

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "DJ",   # flake8-django
]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.lint.isort]
known-first-party = ["apps", "shared", "config"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "DJANGO", "DRF", "FIRSTPARTY", "LOCALFOLDER"]

[tool.ruff.lint.isort.sections]
"DJANGO" = ["django"]
"DRF" = ["rest_framework"]
```

### 10.2 pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]
```

### 10.3 Editor Configuration

```ini
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{html,css,js,json,yml,yaml}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

---

*Bu dokuman, E-Menum kod standartlarini tanimlar. Tum kod bu kurallara uygun yazilmalidir.*
