# E-Menum Testing Strategy

> **Auto-Claude Testing Document**
> Test pyramid, coverage targets, mocking strategy, test patterns.
> Son Guncelleme: 2026-03-16

---

## 1. TESTING PHILOSOPHY

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Test Behavior, Not Implementation** | Test what code does, not how |
| **Fast Feedback Loop** | Unit tests < 10ms, suite < 90s |
| **Deterministic** | Same input = same result, always |
| **Isolated** | Tests don't affect each other |
| **Maintainable** | Tests are code, treat them well |

### 1.2 Test Pyramid

```
                    +-------------+
                    |     E2E     |  ~10%  (Critical paths only)
                    |    Tests    |  Slow, expensive, high confidence
                   +---------------+
                   |  Integration  |  ~30%  (API, DB interactions)
                   |     Tests     |  Medium speed, real dependencies
                  +-----------------+
                  |      Unit       |  ~60%  (Business logic)
                  |      Tests      |  Fast, isolated, comprehensive
                  +-----------------+

Execution Time Budget:
+-- Unit tests:        < 30 seconds total
+-- Integration tests: < 3 minutes total
+-- E2E tests:         < 5 minutes total
```

---

## 2. TESTING STACK

### 2.1 Tools

```yaml
Test Runner:      pytest 8.x + pytest-django
Factories:        factory_boy (model factories)
Fixtures:         pytest fixtures (conftest.py)
Coverage:         coverage.py + pytest-cov
API Testing:      Django REST Framework APITestCase / APIClient
View Testing:     Django test client (self.client)
Mocking:          unittest.mock (patch, MagicMock, PropertyMock)
Assertions:       pytest assert + DRF status helpers
```

### 2.2 Key Dependencies (requirements-test.txt)

```
pytest>=8.0
pytest-django>=4.8
pytest-cov>=5.0
factory-boy>=3.3
faker>=22.0
freezegun>=1.3
responses>=0.25
pytest-xdist>=3.5       # parallel test execution
pytest-timeout>=2.2
```

---

## 3. COVERAGE TARGETS

### 3.1 App Coverage Requirements

| App Category | Unit | Integration | E2E | Overall |
|-------------|:----:|:-----------:|:---:|:-------:|
| Core (core, accounts) | 90% | 80% | - | 85% |
| System (subscriptions, notifications) | 85% | 75% | Critical | 80% |
| Feature (menu, orders, customers) | 80% | 60% | Critical | 75% |
| AI modules (ai, seo_shield) | 70% | 50% | - | 60% |
| Utilities (media, seo, dashboard) | 80% | - | - | 80% |

### 3.2 Coverage Metrics

```
Coverage Types:

+-- Line Coverage      # Minimum 80%
+-- Branch Coverage    # Minimum 75%
+-- Function Coverage  # Minimum 85%
+-- Statement Coverage # Minimum 80%

Exclusions (from coverage via .coveragerc):
+-- */migrations/*
+-- */tests/*
+-- */conftest.py
+-- manage.py
+-- */wsgi.py
+-- */asgi.py
+-- */admin.py (unless custom logic)
+-- */apps.py
```

### 3.3 Coverage Configuration (.coveragerc)

```ini
[run]
source = apps
omit =
    */migrations/*
    */tests/*
    */conftest.py
    */admin.py
    */apps.py
    manage.py
    */wsgi.py
    */asgi.py

[report]
fail_under = 80
show_missing = true
exclude_lines =
    pragma: no cover
    def __repr__
    if TYPE_CHECKING:
    raise NotImplementedError
    pass

[html]
directory = htmlcov
```

### 3.4 Critical Path Coverage

```
Must Have E2E / Integration Tests:

Authentication:
+-- User registration
+-- User login (JWT obtain)
+-- Token refresh
+-- Password reset
+-- Logout (token blacklist)

Core Flows:
+-- Create organization -> Create menu -> Add products -> Publish
+-- QR code generation -> Public menu view
+-- Order creation -> Status updates -> Completion
+-- Subscription upgrade/downgrade
+-- AI content generation (mocked provider)
```

---

## 4. TEST STRUCTURE

### 4.1 File Organization

```
apps/
+-- menu/
|   +-- models.py
|   +-- views.py
|   +-- serializers.py
|   +-- services.py
|   +-- tests/
|   |   +-- __init__.py
|   |   +-- test_models.py
|   |   +-- test_views.py
|   |   +-- test_serializers.py
|   |   +-- test_api.py
|   |   +-- test_services.py
|   |   +-- factories.py          # App-specific factories
|   |   +-- conftest.py           # App-specific fixtures
|
+-- orders/
|   +-- tests/
|   |   +-- __init__.py
|   |   +-- test_models.py
|   |   +-- test_views.py
|   |   +-- test_api.py
|   |   +-- factories.py
|   |   +-- conftest.py
|
+-- core/
|   +-- tests/
|   |   +-- __init__.py
|   |   +-- test_models.py
|   |   +-- test_middleware.py
|   |   +-- test_permissions.py
|   |   +-- test_mixins.py
|   |   +-- factories.py
|   |   +-- conftest.py
|
conftest.py                       # Root-level shared fixtures
pytest.ini                        # pytest configuration
```

### 4.2 All 17 Apps and Their Test Focus

| App | Primary Test Focus |
|-----|-------------------|
| `core` | BaseTenantViewSet, SoftDeleteMixin, TenantMiddleware, permissions |
| `accounts` | User model, authentication, JWT, profile |
| `menu` | Menu CRUD, categories, products, publish workflow |
| `orders` | Order lifecycle, status transitions, order items |
| `subscriptions` | Plan limits, upgrades, billing hooks |
| `customers` | Customer profiles, preferences, history |
| `analytics` | Event tracking, aggregation, dashboard data |
| `ai` | Content generation, AI provider mocking |
| `campaigns` | Campaign CRUD, targeting, scheduling |
| `inventory` | Stock tracking, availability updates |
| `media` | File upload, image processing, storage |
| `notifications` | Notification dispatch, channels, templates |
| `dashboard` | Dashboard widgets, data aggregation |
| `reporting` | Report generation, export |
| `seo` | Meta tags, sitemap, structured data |
| `seo_shield` | Bot detection, rate limiting |
| `website` | Public pages, landing, QR redirect |

### 4.3 Test File Naming

```
Naming Convention:

Unit tests:         test_models.py, test_services.py, test_serializers.py
Integration:        test_api.py, test_views.py
E2E tests:          test_e2e.py (or tests/e2e/ directory)

Examples:
+-- test_models.py          # Model unit tests
+-- test_views.py           # View integration tests
+-- test_api.py             # DRF API endpoint tests
+-- test_serializers.py     # Serializer validation tests
+-- test_services.py        # Service layer unit tests
+-- test_permissions.py     # Permission class tests
+-- test_middleware.py       # Middleware tests
```

---

## 5. PYTEST CONFIGURATION

### 5.1 pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --tb=short
    --cov=apps
    --cov-report=term-missing
    --cov-config=.coveragerc
    -x
    --timeout=30
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    e2e: end-to-end tests
    integration: integration tests requiring database
    unit: pure unit tests
```

### 5.2 Test Settings (config/settings/test.py)

```python
from .base import *  # noqa

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "emenum_test",
        "USER": "test",
        "PASSWORD": "test",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "emenum_test",
        },
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable caching in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable Celery / async tasks
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Media files
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# Email
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# AI provider
AI_PROVIDER = "mock"
```

---

## 6. UNIT TESTING

### 6.1 Model Tests

```python
# apps/menu/tests/test_models.py

import pytest
from django.utils import timezone
from apps.menu.tests.factories import MenuFactory, CategoryFactory, ProductFactory
from apps.core.tests.factories import OrganizationFactory


@pytest.mark.django_db
class TestMenuModel:
    def test_create_menu(self):
        """Menu should be created with auto-generated slug."""
        menu = MenuFactory(name="Ana Menu")
        assert menu.slug == "ana-menu"
        assert menu.is_published is False
        assert menu.deleted_at is None

    def test_soft_delete(self):
        """Menu.delete() should set deleted_at, not remove from DB."""
        menu = MenuFactory()
        menu.soft_delete()
        menu.refresh_from_db()
        assert menu.deleted_at is not None

    def test_soft_deleted_excluded_from_default_qs(self):
        """Default manager should exclude soft-deleted records."""
        menu = MenuFactory()
        menu.soft_delete()
        assert menu.__class__.objects.filter(pk=menu.pk).count() == 0
        assert menu.__class__.all_objects.filter(pk=menu.pk).count() == 1

    def test_publish_sets_published_at(self):
        menu = MenuFactory(is_published=False)
        menu.publish()
        menu.refresh_from_db()
        assert menu.is_published is True
        assert menu.published_at is not None

    def test_str_representation(self):
        menu = MenuFactory(name="Kahvalti Menusu")
        assert str(menu) == "Kahvalti Menusu"

    def test_organization_relation(self):
        org = OrganizationFactory()
        menu = MenuFactory(organization=org)
        assert menu.organization == org
        assert menu in org.menus.all()
```

### 6.2 Serializer Tests

```python
# apps/menu/tests/test_serializers.py

import pytest
from apps.menu.serializers import MenuCreateSerializer, MenuDetailSerializer
from apps.menu.tests.factories import MenuFactory
from apps.core.tests.factories import OrganizationFactory


class TestMenuCreateSerializer:
    def test_valid_data(self):
        data = {"name": "Yeni Menu", "description": "Test aciklama"}
        serializer = MenuCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_empty_name_invalid(self):
        data = {"name": "", "description": "Test"}
        serializer = MenuCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_name_max_length(self):
        data = {"name": "x" * 256}
        serializer = MenuCreateSerializer(data=data)
        assert not serializer.is_valid()

    @pytest.mark.django_db
    def test_output_serialization(self):
        menu = MenuFactory()
        serializer = MenuDetailSerializer(menu)
        data = serializer.data
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "organization_id" not in data  # should not leak tenant ID
```

### 6.3 Service Layer Tests

```python
# apps/menu/tests/test_services.py

import pytest
from unittest.mock import patch, MagicMock
from apps.menu.services import MenuService
from apps.menu.tests.factories import MenuFactory
from apps.core.tests.factories import OrganizationFactory


@pytest.mark.django_db
class TestMenuService:
    def setup_method(self):
        self.org = OrganizationFactory()
        self.service = MenuService()

    def test_create_menu(self):
        result = self.service.create_menu(
            organization=self.org,
            name="Test Menu",
            description="Aciklama",
        )
        assert result.name == "Test Menu"
        assert result.organization == self.org
        assert result.slug == "test-menu"

    def test_create_menu_duplicate_slug_appends_suffix(self):
        MenuFactory(organization=self.org, slug="test-menu")
        result = self.service.create_menu(
            organization=self.org,
            name="Test Menu",
        )
        assert result.slug != "test-menu"
        assert result.slug.startswith("test-menu")

    def test_publish_menu(self):
        menu = MenuFactory(organization=self.org, is_published=False)
        result = self.service.publish(menu.id)
        assert result.is_published is True

    def test_publish_nonexistent_menu_raises(self):
        from apps.core.exceptions import AppException

        with pytest.raises(AppException) as exc_info:
            self.service.publish(999999)
        assert exc_info.value.code == "MENU_NOT_FOUND"

    @patch("apps.ai.services.AIContentService.generate")
    def test_generate_description_calls_ai(self, mock_ai):
        mock_ai.return_value = "AI-generated description"
        menu = MenuFactory(organization=self.org)
        result = self.service.generate_description(menu.id)
        assert result == "AI-generated description"
        mock_ai.assert_called_once()
```

### 6.4 Unit Test Patterns

```python
# Pattern: Arrange-Act-Assert (AAA)
def test_should_do_something(self):
    # Arrange
    menu = MenuFactory(name="Test")

    # Act
    result = menu.get_display_name()

    # Assert
    assert result == "Test"


# Pattern: Parametrized tests (table-driven)
@pytest.mark.parametrize("price,expected", [
    (100.00, True),
    (0, False),
    (-10.00, False),
    (0.01, True),
])
def test_validate_price(price, expected):
    assert validate_price(price) is expected


# Pattern: Testing edge cases
class TestEdgeCases:
    def test_empty_queryset(self):
        result = process_items([])
        assert result == []

    def test_none_input_raises(self):
        with pytest.raises(ValueError):
            process_items(None)

    def test_maximum_length(self):
        items = ["x"] * 10000
        result = process_items(items)
        assert len(result) <= 10000
```

---

## 7. INTEGRATION TESTING

### 7.1 API Tests with DRF APITestCase

```python
# apps/menu/tests/test_api.py

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.menu.tests.factories import MenuFactory
from apps.core.tests.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
class TestMenuAPI:
    def setup_method(self):
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.user = UserFactory(organization=self.org, role="owner")
        self.client.force_authenticate(user=self.user)

    def test_list_menus_returns_own_org_only(self):
        """Tenant isolation: only return menus for authenticated user's org."""
        MenuFactory(organization=self.org)
        MenuFactory(organization=self.org)

        other_org = OrganizationFactory()
        MenuFactory(organization=other_org)

        response = self.client.get("/api/v1/menus/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # not 3

    def test_create_menu(self):
        data = {"name": "Yeni Menu", "description": "Test"}
        response = self.client.post("/api/v1/menus/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Yeni Menu"
        assert response.data["slug"] == "yeni-menu"

    def test_create_menu_validation_error(self):
        data = {"name": ""}
        response = self.client.post("/api/v1/menus/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/menus/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_viewer_cannot_create(self):
        """Permission test: viewer role lacks menu.create."""
        viewer = UserFactory(organization=self.org, role="viewer")
        self.client.force_authenticate(user=viewer)
        response = self.client.post("/api/v1/menus/", {"name": "Test"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_soft_delete_via_api(self):
        menu = MenuFactory(organization=self.org)
        response = self.client.delete(f"/api/v1/menus/{menu.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Record still exists in DB with deleted_at set
        menu.refresh_from_db()
        assert menu.deleted_at is not None

    def test_cannot_access_other_org_menu(self):
        other_org = OrganizationFactory()
        menu = MenuFactory(organization=other_org)
        response = self.client.get(f"/api/v1/menus/{menu.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

### 7.2 Middleware Tests

```python
# apps/core/tests/test_middleware.py

import pytest
from django.test import RequestFactory
from rest_framework.test import APIClient
from apps.core.tests.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
class TestTenantMiddleware:
    """Verify TenantMiddleware injects organization context."""

    def test_sets_organization_on_request(self):
        org = OrganizationFactory()
        user = UserFactory(organization=org)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/menus/")
        assert response.status_code == 200

    def test_rejects_user_without_organization(self):
        user = UserFactory(organization=None)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/menus/")
        assert response.status_code in (400, 403)


@pytest.mark.django_db
class TestMultiTenancyIsolation:
    """Cross-org data must never leak."""

    def test_org_a_cannot_see_org_b_data(self):
        org_a = OrganizationFactory()
        org_b = OrganizationFactory()
        user_a = UserFactory(organization=org_a, role="owner")

        from apps.menu.tests.factories import MenuFactory
        MenuFactory(organization=org_b, name="Secret Menu")

        client = APIClient()
        client.force_authenticate(user=user_a)
        response = client.get("/api/v1/menus/")
        names = [m["name"] for m in response.data["results"]]
        assert "Secret Menu" not in names
```

### 7.3 Permission Tests

```python
# apps/core/tests/test_permissions.py

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.core.tests.factories import OrganizationFactory, UserFactory


@pytest.mark.django_db
@pytest.mark.parametrize("role,method,url,expected_status", [
    ("owner", "GET", "/api/v1/menus/", 200),
    ("owner", "POST", "/api/v1/menus/", 201),
    ("manager", "GET", "/api/v1/menus/", 200),
    ("manager", "POST", "/api/v1/menus/", 201),
    ("staff", "GET", "/api/v1/menus/", 200),
    ("staff", "POST", "/api/v1/menus/", 403),
    ("viewer", "GET", "/api/v1/menus/", 200),
    ("viewer", "POST", "/api/v1/menus/", 403),
    ("viewer", "DELETE", "/api/v1/menus/{id}/", 403),
])
def test_role_based_access(role, method, url, expected_status):
    org = OrganizationFactory()
    user = UserFactory(organization=org, role=role)
    client = APIClient()
    client.force_authenticate(user=user)

    if "{id}" in url:
        from apps.menu.tests.factories import MenuFactory
        menu = MenuFactory(organization=org)
        url = url.replace("{id}", str(menu.id))

    request_fn = getattr(client, method.lower())
    if method == "POST":
        response = request_fn(url, {"name": "Test"})
    else:
        response = request_fn(url)

    assert response.status_code == expected_status
```

---

## 8. TEST DATA FACTORIES

### 8.1 Core Factories

```python
# apps/core/tests/factories.py

import factory
from faker import Faker
from apps.core.models import Organization
from apps.accounts.models import User

fake = Faker("tr_TR")


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.LazyFunction(lambda: fake.company())
    slug = factory.LazyAttribute(lambda o: factory.django.DjangoModelFactory
                                  ._get_or_create  # use slugify
                                  if False else fake.slug())
    is_active = True
    plan = "starter"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyFunction(fake.email)
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    organization = factory.SubFactory(OrganizationFactory)
    role = "owner"
    is_active = True
    is_email_verified = True
    password = factory.PostGenerationMethodCall("set_password", "testpass123")

    class Params:
        unverified = factory.Trait(
            is_email_verified=False,
            is_active=False,
        )
```

### 8.2 Menu Factories

```python
# apps/menu/tests/factories.py

import factory
from faker import Faker
from apps.menu.models import Menu, Category, Product
from apps.core.tests.factories import OrganizationFactory

fake = Faker("tr_TR")


class MenuFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Menu

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.LazyFunction(lambda: fake.word().capitalize() + " Menu")
    slug = factory.LazyAttribute(
        lambda o: o.name.lower().replace(" ", "-")
    )
    description = factory.LazyFunction(fake.sentence)
    is_published = False
    is_default = False
    sort_order = factory.Sequence(lambda n: n)

    class Params:
        published = factory.Trait(
            is_published=True,
            published_at=factory.LazyFunction(
                lambda: __import__("django.utils.timezone", fromlist=["now"]).now()
            ),
        )


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    organization = factory.SubFactory(OrganizationFactory)
    menu = factory.SubFactory(MenuFactory)
    name = factory.LazyFunction(fake.word)
    slug = factory.LazyAttribute(lambda o: o.name.lower())
    is_active = True
    sort_order = factory.Sequence(lambda n: n)


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    organization = factory.SubFactory(OrganizationFactory)
    category = factory.SubFactory(CategoryFactory)
    name = factory.LazyFunction(fake.word)
    slug = factory.LazyAttribute(lambda o: o.name.lower())
    base_price = factory.LazyFunction(
        lambda: round(fake.pyfloat(min_value=10, max_value=500), 2)
    )
    currency = "TRY"
    is_active = True
    is_available = True
    sort_order = factory.Sequence(lambda n: n)

    class Params:
        unavailable = factory.Trait(is_available=False)
        featured = factory.Trait(is_featured=True)
```

### 8.3 Order Factories

```python
# apps/orders/tests/factories.py

import factory
from faker import Faker
from apps.orders.models import Order, OrderItem
from apps.core.tests.factories import OrganizationFactory
from apps.menu.tests.factories import ProductFactory

fake = Faker("tr_TR")


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    organization = factory.SubFactory(OrganizationFactory)
    order_number = factory.Sequence(lambda n: f"ORD-{n:06d}")
    status = "pending"
    table_number = factory.LazyFunction(
        lambda: f"{fake.random_letter().upper()}{fake.random_int(1, 20)}"
    )
    total_amount = 0


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.LazyFunction(lambda: fake.random_int(1, 5))
    unit_price = factory.LazyAttribute(lambda o: o.product.base_price)
```

---

## 9. SHARED FIXTURES (conftest.py)

### 9.1 Root conftest.py

```python
# conftest.py (project root)

import pytest
from rest_framework.test import APIClient
from apps.core.tests.factories import OrganizationFactory, UserFactory


@pytest.fixture
def api_client():
    """Unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    return OrganizationFactory()


@pytest.fixture
def owner_user(organization):
    """Create an owner user linked to organization."""
    return UserFactory(organization=organization, role="owner")


@pytest.fixture
def manager_user(organization):
    """Create a manager user linked to organization."""
    return UserFactory(organization=organization, role="manager")


@pytest.fixture
def staff_user(organization):
    """Create a staff user linked to organization."""
    return UserFactory(organization=organization, role="staff")


@pytest.fixture
def viewer_user(organization):
    """Create a viewer user linked to organization."""
    return UserFactory(organization=organization, role="viewer")


@pytest.fixture
def authenticated_client(api_client, owner_user):
    """API client authenticated as owner."""
    api_client.force_authenticate(user=owner_user)
    return api_client


@pytest.fixture
def other_organization(db):
    """Second organization for tenant isolation tests."""
    return OrganizationFactory()


@pytest.fixture
def other_org_user(other_organization):
    """User from a different organization."""
    return UserFactory(organization=other_organization, role="owner")
```

### 9.2 App-level conftest.py

```python
# apps/menu/tests/conftest.py

import pytest
from apps.menu.tests.factories import MenuFactory, CategoryFactory, ProductFactory


@pytest.fixture
def menu(organization):
    """Create a menu for the test organization."""
    return MenuFactory(organization=organization)


@pytest.fixture
def published_menu(organization):
    """Create a published menu."""
    return MenuFactory(organization=organization, published=True)


@pytest.fixture
def menu_with_products(organization):
    """Create a menu with categories and products."""
    menu = MenuFactory(organization=organization)
    category = CategoryFactory(organization=organization, menu=menu)
    products = ProductFactory.create_batch(
        5, organization=organization, category=category
    )
    return menu, category, products
```

---

## 10. MOCKING STRATEGIES

### 10.1 Mocking External Services

```python
# Mocking AI provider
from unittest.mock import patch, MagicMock


@patch("apps.ai.services.AIContentService.generate")
def test_ai_content_generation(mock_generate):
    mock_generate.return_value = "Generated product description"
    result = generate_menu_description(menu_id=1)
    assert result == "Generated product description"
    mock_generate.assert_called_once()


# Mocking with responses library (HTTP calls)
import responses


@responses.activate
def test_external_api_call():
    responses.add(
        responses.POST,
        "https://api.anthropic.com/v1/messages",
        json={"content": [{"text": "Mocked AI response"}]},
        status=200,
    )
    result = call_ai_api("Generate something")
    assert result == "Mocked AI response"


# Mocking Redis/Cache
@patch("django.core.cache.cache")
def test_cached_value(mock_cache):
    mock_cache.get.return_value = {"cached": True}
    result = get_cached_menu(menu_id=1)
    assert result == {"cached": True}
```

### 10.2 Mocking Time

```python
from freezegun import freeze_time


@freeze_time("2026-03-16 12:00:00")
def test_subscription_expiry():
    from django.utils import timezone
    sub = SubscriptionFactory(expires_at=timezone.now())
    assert sub.is_expired is True


@freeze_time("2026-01-01")
def test_analytics_date_range():
    result = get_monthly_stats(year=2026, month=1)
    assert result["period"] == "2026-01"
```

### 10.3 Mocking File Uploads

```python
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_image_upload(authenticated_client):
    image = SimpleUploadedFile(
        "test.jpg",
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00",  # minimal GIF
        content_type="image/jpeg",
    )
    response = authenticated_client.post(
        "/api/v1/media/upload/",
        {"file": image},
        format="multipart",
    )
    assert response.status_code == 201
```

---

## 11. E2E TESTING

### 11.1 E2E with Django Test Client

```python
# apps/orders/tests/test_e2e.py

import pytest
from rest_framework.test import APIClient
from apps.core.tests.factories import OrganizationFactory, UserFactory
from apps.menu.tests.factories import MenuFactory, CategoryFactory, ProductFactory


@pytest.mark.django_db
@pytest.mark.e2e
class TestOrderFlowE2E:
    """Full order lifecycle: browse menu -> add to cart -> submit order."""

    def setup_method(self):
        self.client = APIClient()
        self.org = OrganizationFactory()
        self.owner = UserFactory(organization=self.org, role="owner")

        # Setup menu data
        self.menu = MenuFactory(organization=self.org, published=True)
        self.category = CategoryFactory(
            organization=self.org, menu=self.menu, name="Yemekler"
        )
        self.product = ProductFactory(
            organization=self.org,
            category=self.category,
            name="Kofte",
            base_price=120.00,
        )

    def test_full_order_flow(self):
        # 1. Anonymous user views public menu
        response = self.client.get(
            f"/api/v1/public/menus/{self.org.slug}/{self.menu.slug}/"
        )
        assert response.status_code == 200
        assert response.data["name"] == self.menu.name

        # 2. Browse categories
        response = self.client.get(
            f"/api/v1/public/menus/{self.org.slug}/{self.menu.slug}/categories/"
        )
        assert response.status_code == 200
        assert len(response.data) >= 1

        # 3. Submit order
        order_data = {
            "table_number": "A5",
            "items": [
                {"product_id": self.product.id, "quantity": 2},
            ],
        }
        response = self.client.post(
            f"/api/v1/public/orders/{self.org.slug}/",
            order_data,
            format="json",
        )
        assert response.status_code == 201
        order_number = response.data["order_number"]
        assert order_number.startswith("ORD-")
        assert response.data["total_amount"] == "240.00"

        # 4. Restaurant owner updates order status
        self.client.force_authenticate(user=self.owner)
        order_id = response.data["id"]

        response = self.client.patch(
            f"/api/v1/orders/{order_id}/",
            {"status": "preparing"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "preparing"

        # 5. Complete order
        response = self.client.patch(
            f"/api/v1/orders/{order_id}/",
            {"status": "completed"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["status"] == "completed"
```

### 11.2 Authentication E2E

```python
@pytest.mark.django_db
@pytest.mark.e2e
class TestAuthFlowE2E:
    def test_register_login_refresh_logout(self):
        client = APIClient()

        # 1. Register
        response = client.post("/api/v1/auth/register/", {
            "email": "test@example.com",
            "password": "securePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "Test Cafe",
        })
        assert response.status_code == 201

        # 2. Login
        response = client.post("/api/v1/auth/login/", {
            "email": "test@example.com",
            "password": "securePassword123!",
        })
        assert response.status_code == 200
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        # 3. Access protected resource
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get("/api/v1/menus/")
        assert response.status_code == 200

        # 4. Refresh token
        client.credentials()
        response = client.post("/api/v1/auth/refresh/", {
            "refresh": refresh_token,
        })
        assert response.status_code == 200
        new_access = response.data["access"]

        # 5. Logout (blacklist refresh token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        response = client.post("/api/v1/auth/logout/", {
            "refresh": refresh_token,
        })
        assert response.status_code == 200
```

---

## 12. TESTING KEY PATTERNS

### 12.1 Testing BaseTenantViewSet

```python
@pytest.mark.django_db
class TestBaseTenantViewSet:
    """All ViewSets extending BaseTenantViewSet auto-filter by org."""

    def test_get_queryset_filters_by_org(self, authenticated_client, organization):
        from apps.menu.tests.factories import MenuFactory

        MenuFactory(organization=organization)
        MenuFactory(organization=OrganizationFactory())  # other org

        response = authenticated_client.get("/api/v1/menus/")
        assert response.data["count"] == 1

    def test_perform_create_sets_organization(self, authenticated_client, organization):
        response = authenticated_client.post("/api/v1/menus/", {"name": "Auto Org"})
        assert response.status_code == 201
        from apps.menu.models import Menu
        menu = Menu.objects.get(pk=response.data["id"])
        assert menu.organization_id == organization.id
```

### 12.2 Testing SoftDeleteMixin

```python
@pytest.mark.django_db
class TestSoftDeleteMixin:
    def test_delete_sets_deleted_at(self):
        menu = MenuFactory()
        menu.soft_delete()
        menu.refresh_from_db()
        assert menu.deleted_at is not None

    def test_restore_clears_deleted_at(self):
        menu = MenuFactory()
        menu.soft_delete()
        menu.restore()
        menu.refresh_from_db()
        assert menu.deleted_at is None

    def test_hard_delete_removes_from_db(self):
        menu = MenuFactory()
        pk = menu.pk
        menu.hard_delete()
        from apps.menu.models import Menu
        assert not Menu.all_objects.filter(pk=pk).exists()
```

### 12.3 Testing Signals and Events

```python
from unittest.mock import patch


@pytest.mark.django_db
class TestMenuSignals:
    @patch("apps.analytics.signals.track_event")
    def test_menu_published_emits_event(self, mock_track):
        menu = MenuFactory(is_published=False)
        menu.publish()
        mock_track.assert_called_once_with(
            event="menu.published",
            organization_id=menu.organization_id,
            data={"menu_id": menu.id},
        )
```

---

## 13. CI/CD INTEGRATION

### 13.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml

name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"
  DJANGO_SETTINGS_MODULE: config.settings.test

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - run: pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest -m "not integration and not e2e" --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unit

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: emenum_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - run: pip install -r requirements-test.txt

      - name: Run migrations
        run: python manage.py migrate --run-syncdb

      - name: Run integration tests
        run: pytest -m "integration" --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: integration

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: emenum_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - run: pip install -r requirements-test.txt

      - name: Run migrations
        run: python manage.py migrate --run-syncdb

      - name: Run E2E tests
        run: pytest -m "e2e" --timeout=120
```

### 13.2 Makefile Commands

```makefile
# Makefile (test targets)

test:
	pytest

test-unit:
	pytest -m "not integration and not e2e" -x

test-integration:
	pytest -m "integration" -x

test-e2e:
	pytest -m "e2e" --timeout=120

test-cov:
	pytest --cov=apps --cov-report=html --cov-report=term-missing

test-fast:
	pytest -x -q --no-header

test-parallel:
	pytest -n auto -x

test-app:
	pytest apps/$(app)/tests/ -x -v

test-watch:
	ptw -- -x -q
```

---

## 14. TEST DOCUMENTATION

### 14.1 Test Naming Conventions

```python
# GOOD: Descriptive test names
class TestMenuService:
    def test_create_menu_with_auto_generated_slug_when_not_provided(self): ...
    def test_create_menu_raises_duplicate_error_when_slug_taken(self): ...
    def test_publish_sets_published_at_timestamp(self): ...
    def test_publish_nonexistent_menu_raises_menu_not_found(self): ...

# BAD: Vague test names
class TestMenuService:
    def test_works(self): ...
    def test_create(self): ...
    def test_something(self): ...
```

### 14.2 Test Docstrings

```python
class TestMenuAPI:
    """
    Integration tests for Menu API endpoints.

    Coverage:
    - CRUD operations via /api/v1/menus/
    - Tenant isolation (organization filtering)
    - Permission checks (role-based access)
    - Soft delete behavior

    Factories: MenuFactory, OrganizationFactory, UserFactory
    Fixtures: organization, owner_user, authenticated_client
    """

    def test_list_menus_returns_own_org_only(self):
        """Tenant isolation: menus from other orgs must never appear."""
        ...
```

### 14.3 Quick Reference: Running Tests

```bash
# Run all tests
pytest

# Run specific app
pytest apps/menu/tests/ -v

# Run specific test class
pytest apps/menu/tests/test_api.py::TestMenuAPI -v

# Run specific test method
pytest apps/menu/tests/test_api.py::TestMenuAPI::test_list_menus -v

# Run with coverage report
pytest --cov=apps --cov-report=html

# Run only failing tests from last run
pytest --lf

# Run tests matching keyword
pytest -k "soft_delete"

# Run with verbose output
pytest -v --tb=long

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

---

*Bu dokuman, E-Menum test stratejisini tanimlar. Tum kod icin uygun testler yazilmalidir.*
