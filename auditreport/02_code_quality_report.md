# Code Quality Audit Report

**Project:** E-Menum Enterprise QR Menu SaaS
**Date:** 2026-03-17
**SAFe Role:** Development Team Lead / Code Review Engineer
**Auditor:** E-Menum Engineering Team -- Automated Audit System
**Report Version:** 1.1.1

---

## Executive Summary

| Metric | Score |
|--------|-------|
| **Overall Code Quality** | **83 / 100** |
| CLAUDE.md Critical Rules Compliance | 85 / 100 |
| Linting & Formatting | 90 / 100 |
| Code Organization | 88 / 100 |
| Documentation Coverage | 75 / 100 |
| Dependency Health | 82 / 100 |
| Security Code Review | 80 / 100 |

The codebase demonstrates strong adherence to established patterns with consistent use of base view classes, serializer-based validation, and soft-delete patterns. The project contains approximately 444 Python files across 16 Django apps, with well-structured model definitions totaling ~78 models and ~17,000+ lines of model code. Key areas for improvement include ensuring TenantMiddleware activation, completing docstring coverage in newer modules, and addressing the `|| true` bypass in the security audit CI job.

---

## 1. Code Metrics

### 1.1 File Distribution

| Category | Count |
|----------|-------|
| Total Python files (apps/) | 444 |
| Model files | 15 |
| View files | 20+ (including split view modules) |
| Test files | 27 |
| Serializer files | ~15 |
| Migration files | ~40 |
| Management commands | 14 |
| Shared library files | 23 |

### 1.2 Lines of Code by App (models.py only)

| App | Estimated LOC | Model Count |
|-----|--------------|-------------|
| orders | 3,500+ | 10 |
| subscriptions | 2,700+ | 8 |
| menu | 2,200+ | 9 |
| core | 2,000+ | 14 |
| seo | 1,200+ | 10 |
| customers | 1,100+ | 6 |
| reporting | 900+ | 5 |
| inventory | 900+ | 7 |
| campaigns | 550+ | 4 |
| analytics | 500+ | 4 |
| media | 400+ | 2 |
| seo_shield | 300+ | 4 |
| ai | 300+ | 2 |
| dashboard | 250+ | 2 |
| notifications | 200+ | 1 |

### 1.3 ViewSet / API View Count

Total ViewSets and API Views: **~80** (see System Architect report for breakdown).

---

## 2. CLAUDE.md Critical Rules Compliance Audit

### Rule 3.1: Multi-Tenancy (Organization Filter in QuerySets)

**Status: PARTIAL COMPLIANCE (80%)**

| Finding | Details |
|---------|---------|
| BaseTenantViewSet | COMPLIANT -- `TenantFilterMixin.get_queryset()` at `shared/views/base.py:485` filters by `organization` |
| BaseTenantReadOnlyViewSet | COMPLIANT -- Inherits TenantFilterMixin |
| BaseTenantAPIView | COMPLIANT -- Inherits TenantFilterMixin |
| TenantMiddleware | NOT ACTIVE -- Commented out in `config/settings/base.py` line 204 |
| Safety fallback | COMPLIANT -- Returns `queryset.none()` when no org context (base.py:513) |

**Finding CQ-01 (MEDIUM):** While the view-level tenant filtering is robust (empty queryset on missing org), the TenantMiddleware is not active. The CLAUDE.md states "TenantMiddleware injects request.organization" but the middleware is commented out. Organization context must be set through alternative means (e.g., the view's `get_organization()` method reading from request attributes).

### Rule 3.2: Authorization (permission_classes on ViewSets)

**Status: COMPLIANT (90%)**

| ViewSet Type | Default permission_classes | Compliance |
|-------------|---------------------------|------------|
| BaseTenantViewSet | `[IsAuthenticated, IsTenantMember, OrganizationScopedPermission]` | GREEN |
| BaseTenantReadOnlyViewSet | `[IsAuthenticated, IsTenantMember, OrganizationScopedPermission]` | GREEN |
| BaseTenantAPIView | `[IsAuthenticated, IsTenantMember]` | GREEN |
| BaseModelViewSet | Inherits DRF default `[IsAuthenticated]` | YELLOW |
| Core auth views (Login, TokenRefresh) | `[AllowAny]` | GREEN (appropriate) |
| AllergenViewSet | `[AllowAny]` | GREEN (public reference data) |

**Specific permission_classes findings across views.py files:**

- `apps/media/views.py`: Uses granular `HasOrganizationPermission("media.view")` etc. -- COMPLIANT
- `apps/analytics/views.py`: Uses `[permissions.IsAuthenticated]` -- COMPLIANT
- `apps/ai/views.py`: Uses `[IsAuthenticated]` for all 5 views -- COMPLIANT
- `apps/reporting/views.py`: Uses `[IsAuthenticated, IsTenantMember]` -- COMPLIANT
- `apps/menu/views.py`: ProductVariantViewSet and ProductModifierViewSet override with `[IsAuthenticated]` -- YELLOW (missing IsTenantMember)

**Finding CQ-02 (LOW):** `ProductVariantViewSet` (menu/views.py:597) and `ProductModifierViewSet` (menu/views.py:651) set `permission_classes = [IsAuthenticated]` without `IsTenantMember`. Since they inherit from view classes that include tenant filtering, the data isolation still works, but the permission layer is less strict than other tenant ViewSets.

### Rule 3.3: Soft Delete (SoftDeleteMixin Usage)

**Status: COMPLIANT (95%)**

The `SoftDeleteMixin` from `apps/core/models.py:59` is used consistently across all business models. The `SoftDeleteManager` at line 45 auto-filters `deleted_at__isnull=True`.

| Evidence | Status |
|----------|--------|
| SoftDeleteMixin on business models | 60+ models use it |
| SoftDeleteManager as default manager | IMPLEMENTED |
| View-level `perform_destroy()` uses `soft_delete()` | IMPLEMENTED in `shared/views/base.py:390` |
| Models without soft delete | Only junction tables (CouponUsage, QRScan, etc.) and metric models -- APPROPRIATE |

### Rule 3.4: Import Convention (Absolute Imports)

**Status: COMPLIANT (95%)**

| Pattern | Example | Status |
|---------|---------|--------|
| App imports | `from apps.core.models import Organization` | USED consistently |
| Shared imports | `from shared.permissions.plan_enforcement import PlanEnforcementService` | USED consistently |
| Intra-app imports | `from apps.core.choices import AuditAction` | USED consistently |
| Relative imports | Not found in sampled files | GREEN |

### Rule 3.5: i18n ({% trans %}, gettext_lazy)

**Status: COMPLIANT (95%)**

| Evidence | Status |
|----------|--------|
| `gettext_lazy as _` in models | USED in all 15 model files |
| TextChoices with `_()` | USED (e.g., `LEFT = "left", _("Left")` in menu/models.py:37) |
| Error messages with `_()` | USED in `shared/utils/exceptions.py` |
| Plan enforcement messages | USED with `_()` and `%` formatting |
| Template i18n | `{% load i18n %}` and `{% trans %}` usage (not fully audited in this pass) |

**Finding CQ-03 (LOW):** Some Python string literals in management commands and service files may not be wrapped in `_()`. A comprehensive `makemessages` extraction run would identify untranslated strings.

### Rule 3.6: Error Handling (DRF Exception Handler)

**Status: COMPLIANT (95%)**

The custom exception handler at `shared/utils/exceptions.py` is configured in `config/settings/base.py:381`:

```
"EXCEPTION_HANDLER": "shared.utils.exceptions.custom_exception_handler"
```

| Feature | Status |
|---------|--------|
| Centralized ErrorCodes class | IMPLEMENTED (40+ error codes) |
| AppException base class | IMPLEMENTED with code, message, status_code, details |
| Specialized exceptions | AuthenticationException, PermissionException, ResourceNotFoundException, BusinessLogicException |
| Standard error format | `{"success": false, "error": {"code": "...", "message": "..."}}` |
| DRF exception types handled | ValidationError, AuthenticationFailed, NotAuthenticated, PermissionDenied, NotFound, Throttled, ParseError |
| Django exception types handled | Http404, PermissionDenied, DjangoValidationError |

### Rule 3.7: Validation (Serializer Validation)

**Status: COMPLIANT (85%)**

Serializer files exist for all major apps. The DRF settings enforce serializer-based validation through the configured parsers and renderers.

**Finding CQ-04 (LOW):** Some template-based views in `apps/accounts/views.py` and `apps/website/views/` use Django Forms instead of DRF Serializers, which is appropriate for SSR views but means validation paths differ between API and template views.

---

## 3. CLAUDE.md Rules Compliance Summary

| Rule | Description | Score | Status |
|------|------------|-------|--------|
| 3.1 | Multi-Tenancy | 80% | YELLOW -- TenantMiddleware inactive |
| 3.2 | Authorization | 90% | GREEN -- 2 ViewSets missing IsTenantMember |
| 3.3 | Soft Delete | 95% | GREEN -- Consistent usage |
| 3.4 | Import Convention | 95% | GREEN -- Absolute imports throughout |
| 3.5 | i18n | 95% | GREEN -- gettext_lazy used, minor gaps possible |
| 3.6 | Error Handling | 95% | GREEN -- Comprehensive exception handler |
| 3.7 | Validation | 85% | GREEN -- Serializers for API, Forms for SSR |

---

## 4. Linting & Formatting

### 4.1 Ruff Configuration

The CI pipeline (`ci.yml`) runs:
- `ruff check . --output-format=github` (lint)
- `ruff format --check .` (format)

Ruff version is pinned to `0.15.6` in CI (commit `6128c90`).

**Status: GREEN** -- CI enforces lint and format checks on every push/PR to main.

### 4.2 Additional Tooling in requirements-dev.txt

| Tool | Purpose | Status in CI |
|------|---------|-------------|
| ruff | Linting + formatting | ACTIVE |
| black | Code formatting | INSTALLED but ruff primary |
| flake8 | Linting | INSTALLED but ruff primary |
| isort | Import sorting | INSTALLED but ruff primary |
| mypy + django-stubs | Type checking | INSTALLED, NOT in CI |

**Finding CQ-05 (LOW):** mypy is installed in dev dependencies but not run in CI. Adding mypy type-checking to the CI pipeline would catch type errors early.

---

## 5. Code Organization & Patterns

### 5.1 Base Class Hierarchy

The project uses a well-designed base class hierarchy in `shared/views/base.py`:

```
APIView
  +-- StandardResponseMixin
  |     +-- BaseAPIView
  |     +-- BaseTenantAPIView (+ TenantFilterMixin)
  |
ModelViewSet
  +-- StandardResponseMixin + SoftDeleteMixin
  |     +-- BaseModelViewSet
  |
  +-- TenantFilterMixin + StandardResponseMixin + SoftDeleteMixin
        +-- BaseTenantViewSet
        +-- BaseTenantReadOnlyViewSet (ReadOnlyModelViewSet)
```

### 5.2 Plan Enforcement Pattern

The `PlanEnforcementMixin` at `shared/permissions/plan_enforcement.py` provides:
- `PlanEnforcementService.check_limit()` -- Programmatic limit checking
- `PlanEnforcementService.check_feature()` -- Feature flag checking
- `RequiresPlanFeature` -- DRF permission class
- `CheckPlanLimit` -- DRF permission class
- `PlanEnforcementMixin` -- ViewSet mixin for auto-checking on create

Usage confirmed in:
- `apps/menu/views.py:177` -- `MenuViewSet(PlanEnforcementMixin, BaseTenantViewSet)`
- `apps/menu/views.py:324` -- `CategoryViewSet(PlanEnforcementMixin, BaseTenantViewSet)`
- `apps/menu/views.py:411` -- `ProductViewSet(PlanEnforcementMixin, BaseTenantViewSet)`
- `apps/orders/views.py:378` -- `QRCodeViewSet(PlanEnforcementMixin, BaseTenantViewSet)`

### 5.3 App Structure Convention Adherence

Checking against CLAUDE.md Section 5.2 expected structure:

| File | Expected | Present in All Apps |
|------|----------|-------------------|
| models.py | YES | 15/16 (website uses CMS models in separate files) |
| views.py | YES | 16/16 (some split into multiple files) |
| urls.py | YES | 16/16 |
| admin.py | YES | ~12/16 |
| serializers.py | YES | ~12/16 |
| forms.py | YES | ~8/16 |
| translation.py | YES | 10/16 |
| tests/ | YES | 7/16 apps have test directories |
| management/commands/ | OPTIONAL | 7/16 |
| choices.py | OPTIONAL | 8/16 |

**Finding CQ-06 (MEDIUM):** Only 7 of 16 apps have test directories. Apps without tests: campaigns, customers, inventory, notifications, analytics, reporting, ai, media, website. See Test & QA Report for details.

---

## 6. Documentation Coverage

### 6.1 Module-Level Docstrings

| File | Docstring | Quality |
|------|-----------|---------|
| `apps/core/models.py` | YES | Detailed -- lists models, critical rules |
| `apps/menu/models.py` | YES | Detailed -- lists all 9 models |
| `apps/orders/models.py` | YES | Detailed -- lists all models |
| `apps/subscriptions/models.py` | YES | Detailed -- lists models and rules |
| `shared/views/base.py` | YES | Comprehensive -- 78-line docstring with usage examples |
| `shared/permissions/plan_enforcement.py` | YES | Comprehensive -- 40-line docstring with examples |
| `shared/utils/exceptions.py` | YES | Comprehensive -- error format documentation |
| `config/settings/base.py` | YES | Section headers with comments |
| `config/settings/production.py` | YES | Security comments and warnings |

### 6.2 Class-Level Docstrings

All model classes in sampled files have docstrings explaining their purpose, relationships, and critical rules. ViewSet base classes have comprehensive docstrings with usage examples.

**Finding CQ-07 (LOW):** Documentation quality is high for core/shared modules. Newer feature modules (campaigns, inventory, analytics) would benefit from the same level of documentation.

---

## 7. Dependency Health

### 7.1 Production Dependencies (requirements.txt)

| Package | Version Spec | Status |
|---------|-------------|--------|
| Django | >=5.0,<6.0 | GREEN -- Current |
| djangorestframework | >=3.15,<4.0 | GREEN -- Current |
| simplejwt | >=5.3,<6.0 | GREEN -- Current |
| psycopg[binary] | >=3.1,<4.0 | GREEN -- psycopg3 |
| celery[redis] | >=5.4,<6.0 | GREEN -- Current |
| django-guardian | >=2.4 | GREEN |
| django-modeltranslation | >=0.18 | GREEN |
| django-filer | >=3.0 | GREEN |
| whitenoise | >=6.6 | GREEN |
| gunicorn | >=21.0 | GREEN |
| xhtml2pdf | >=0.2.16 | YELLOW -- Niche, limited maintenance |
| qrcode[pil] | >=8.0 | GREEN |
| django-anymail[mailgun] | >=12.0 | GREEN |

### 7.2 Dev Dependencies (requirements-dev.txt)

| Package | Purpose | Status |
|---------|---------|--------|
| pytest>=8.0 | Testing | GREEN |
| pytest-django>=4.8 | Django test integration | GREEN |
| pytest-cov>=5.0 | Coverage | GREEN |
| pytest-xdist>=3.5 | Parallel tests | GREEN |
| factory-boy>=3.3 | Test factories | GREEN |
| sentry-sdk[django]>=1.40 | Error tracking | GREEN |
| django-debug-toolbar>=4.3 | Dev debugging | GREEN |

### 7.3 Security Scan

The CI pipeline includes `pip-audit --strict --desc on` but with `|| true` (line 131-132 of ci.yml), meaning vulnerabilities do not block the build.

**Finding CQ-08 (MEDIUM):** The `pip-audit` step uses `|| true`, meaning known vulnerabilities in dependencies will not fail the CI pipeline. The comment acknowledges this is intentional during initial setup. This should be changed to a hard failure once known issues are resolved.

---

## 8. Complexity Analysis

### 8.1 High-Complexity Files (Estimated)

| File | Est. LOC | Complexity Concern |
|------|---------|-------------------|
| `apps/orders/models.py` | 3,500+ | 10 models, complex Order state machine |
| `apps/subscriptions/models.py` | 2,700+ | 8 models, billing logic in model methods |
| `apps/menu/models.py` | 2,200+ | 9 models, deep hierarchy (Menu->Category->Product->Variant) |
| `apps/core/models.py` | 2,000+ | 14 models, User manager, Shift/Schedule |
| `shared/views/base.py` | 750 | 6 base classes, 3 mixins -- well-structured |
| `shared/permissions/plan_enforcement.py` | 522 | Service + 2 permissions + mixin -- well-structured |

**Finding CQ-09 (LOW):** The orders and subscriptions model files are large but well-organized. Consider splitting `orders/models.py` into separate files (e.g., `models/zone.py`, `models/order.py`, `models/qr.py`) if they continue to grow.

---

## 9. Naming Convention Adherence

| Convention | Status | Notes |
|------------|--------|-------|
| App names (lowercase, singular/plural) | GREEN | Consistent: core, menu, orders, subscriptions |
| Model names (PascalCase) | GREEN | Organization, Menu, QRCode, OrderItem |
| Field names (snake_case) | GREEN | organization, created_at, deleted_at |
| ViewSet names ({Model}ViewSet) | GREEN | MenuViewSet, OrderViewSet |
| URL patterns (kebab-case or snake_case) | GREEN | /api/v1/menus/, /api/v1/qr-codes/ |
| Settings (UPPER_SNAKE_CASE) | GREEN | CELERY_BROKER_URL, EMENUM_PLAN_LIMITS |
| Error codes (UPPER_SNAKE_CASE) | GREEN | AUTH_INVALID_CREDENTIALS, MENU_NOT_FOUND |

---

## 10. Recommendations

### Immediate (Current Sprint)

| # | Recommendation | Effort |
|---|---------------|--------|
| CQ-R01 | Remove `|| true` from pip-audit CI step once known issues are resolved | 1h |
| CQ-R02 | Add `IsTenantMember` to ProductVariantViewSet and ProductModifierViewSet | 1h |

### Short-Term (Next PI)

| # | Recommendation | Effort |
|---|---------------|--------|
| CQ-R03 | Add mypy type-checking to CI pipeline | 4h |
| CQ-R04 | Run `makemessages` to identify untranslated strings | 2h |
| CQ-R05 | Add tests for 9 apps currently without test directories | 40h+ |

### Long-Term (Backlog)

| # | Recommendation | Effort |
|---|---------------|--------|
| CQ-R06 | Split large model files (orders, subscriptions) into model packages | 8h |
| CQ-R07 | Add comprehensive docstrings to newer feature modules | 8h |
| CQ-R08 | Activate and configure TenantMiddleware or document the current approach | 4h |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-17 | Automated Audit System | Initial code quality audit |
| 1.1.0 | 2026-03-17 | Automated Audit System | Updated with post-deploy fixes and accurate metrics |
| 1.1.1 | 2026-03-17 | Automated Audit System | Version bump for consistency with business context corrections across all reports |
