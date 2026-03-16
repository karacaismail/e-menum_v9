# E-Menum Security Model

> **Auto-Claude Security Document**
> Authentication, authorization, data protection, audit logging, threat model.
> Son Guncelleme: 2026-03-16

---

## 1. SECURITY OVERVIEW

### 1.1 Security Principles

| Principle | Implementation |
|-----------|----------------|
| Defense in Depth | Multiple security layers |
| Least Privilege | Minimal required permissions |
| Zero Trust | Verify every request |
| Secure by Default | Safe configurations out-of-box |
| Audit Everything | Complete activity trail |

### 1.2 Security Stack

```yaml
Framework:        Django 5.0 + Django REST Framework 3.15
Auth:             djangorestframework-simplejwt (JWT)
Password:         BCrypt (12 rounds)
Object Perms:     django-guardian
Custom RBAC/ABAC: EMenumPermissionMixin + Ability system
Tenant Isolation:  TenantMiddleware (shared/middleware/tenant.py)
Plan Gating:      PlanEnforcementService (shared/permissions/plan_enforcement.py)
Admin Protection:  @superadmin_required decorator
CSRF:             Django CsrfViewMiddleware on all forms
Audit:            AuditLog model (apps/core/models.py)
```

### 1.3 Security Layers

```
Layer 1: NETWORK
  - Cloudflare DDoS protection
  - TLS 1.3 encryption
  - HSTS enforcement
  - IP reputation filtering

Layer 2: APPLICATION
  - Django CsrfViewMiddleware on all forms
  - DRF throttling (rate limiting)
  - DRF serializer validation
  - Django SecurityMiddleware (secure headers)
  - CORS via django-cors-headers

Layer 3: AUTHENTICATION
  - JWT access tokens (15 min, simplejwt)
  - Refresh tokens (7 days, httpOnly cookie)
  - Password hashing (BCrypt, 12 rounds)
  - Session management

Layer 4: AUTHORIZATION
  - Custom RBAC via Role / Permission / UserRole / RolePermission models
  - ABAC via Ability system with conditions (shared/permissions/abilities.py)
  - Tenant isolation via TenantMiddleware
  - Object-level permissions via django-guardian
  - Plan enforcement via PlanEnforcementService

Layer 5: DATA
  - Encryption at rest (PostgreSQL TDE)
  - Encryption in transit (TLS 1.3)
  - PII field encryption
  - Secure key management
```

---

## 2. AUTHENTICATION

### 2.1 Authentication Flow

```
REGISTRATION:

  Client                    Server                    Database
    |                         |                          |
    |--POST /api/v1/auth/register-->                     |
    |  {email, password}      |                          |
    |                         |--DRF serializer validate-|
    |                         |--Check email exists----->|
    |                         |<-------------------------|
    |                         |--BCrypt hash password----|
    |                         |--User.objects.create---->|
    |                         |--Send verification email-|
    |<--201 Created-----------|                          |
    |  {userId, message}      |                          |

LOGIN:

  Client                    Server                    Database
    |                         |                          |
    |--POST /api/v1/auth/login-->                        |
    |  {email, password}      |                          |
    |                         |--DRF throttle check------|
    |                         |--authenticate(email, pw)-|
    |                         |--BCrypt verify----------->|
    |                         |<-------------------------|
    |                         |--simplejwt.tokens--------|
    |                         |  TokenObtainPairView     |
    |                         |  accessToken (15min)     |
    |                         |  refreshToken (7d)       |
    |                         |--AuditLog.create-------->|
    |<--200 OK----------------|                          |
    |  {access, refresh}      |                          |
    |  Set-Cookie: refresh    |                          |

TOKEN REFRESH:

  Client                    Server                    Database
    |                         |                          |
    |--POST /api/v1/auth/refresh-->                      |
    |  Cookie: refreshToken   |                          |
    |                         |--simplejwt validate------|
    |                         |--Check blacklist-------->|
    |                         |<-------------------------|
    |                         |--Rotate tokens-----------|
    |                         |  Blacklist old refresh   |
    |                         |  Issue new pair          |
    |<--200 OK----------------|                          |
    |  {access}               |                          |
    |  Set-Cookie: refresh    |                          |
```

### 2.2 Token Specifications

| Token | Type | Storage | Expiry | Purpose |
|-------|------|---------|--------|---------|
| Access Token | JWT (simplejwt) | Memory/Header | 15 min | API authentication |
| Refresh Token | JWT (simplejwt) | httpOnly cookie | 7 days | Token renewal |
| Verification Token | Opaque | Database | 24 hours | Email verification |
| Reset Token | Opaque | Database | 1 hour | Password reset |

### 2.3 JWT Structure (simplejwt)

```
Access Token Payload (simplejwt default + custom claims):
{
  "token_type": "access",
  "user_id": "uuid-xxx",           // User PK
  "org_id": "uuid-xxx",            // Organization PK (custom claim)
  "role": "owner",                 // Primary role (custom claim)
  "iat": 1706702400,               // Issued at
  "exp": 1706703300,               // Expiry (15 min)
  "jti": "unique-token-id"         // Token ID (for blacklisting)
}

Signing:
  Algorithm: HS256 (default simplejwt)
  Key: settings.SECRET_KEY (or SIGNING_KEY override)
  Rotation: Via ROTATE_REFRESH_TOKENS = True
  Blacklisting: via simplejwt.token_blacklist app
```

### 2.4 Password Policy

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Complexity | 1 uppercase, 1 lowercase, 1 number |
| Common password check | Yes (Django CommonPasswordValidator) |
| Hash algorithm | BCrypt |
| Hash rounds | 12 |
| Max age | None (optional reminder) |
| Django validators | UserAttributeSimilarityValidator, MinimumLengthValidator, CommonPasswordValidator, NumericPasswordValidator |

### 2.5 Brute Force Protection

```
DRF Throttle Classes:

/api/v1/auth/login:
  - AnonRateThrottle: 5/min per IP
  - Per email: 10 attempts / hour
  - Global: 1000 attempts / min

/api/v1/auth/forgot-password:
  - AnonRateThrottle: 3/hour per IP
  - Per email: 1 attempt / 5 min

Account Lockout:
  - Threshold: 10 failed attempts
  - Duration: 30 minutes
  - Unlock: Email verification or support
```

---

## 3. AUTHORIZATION (RBAC + ABAC)

### 3.1 Role Hierarchy

```
PLATFORM ROLES (System-wide):

                    super_admin
                         |
          +--------------+--------------+
          |              |              |
        admin          sales        support

  Scope: All organizations, system settings
  Protected by: @superadmin_required decorator, HasPlatformPermission

ORGANIZATION ROLES (Tenant-scoped):

                      owner
                        |
                    manager
                        |
          +-------------+-------------+
          |                           |
        staff                      viewer

  Scope: Single organization resources only
  Protected by: HasOrganizationPermission, OrganizationScopedPermission

PUBLIC ROLES (Unauthenticated):

    customer (optional auth)    |    anonymous (no auth)

  Scope: Public endpoints only
  Protected by: AllowPublicRead, IsAuthenticatedOrReadOnly
```

### 3.2 Permission Matrix

#### Platform Permissions

| Permission | super_admin | admin | sales | support |
|------------|:-----------:|:-----:|:-----:|:-------:|
| `platform.manage` | Y | - | - | - |
| `organizations.view` | Y | Y | Y | Y |
| `organizations.create` | Y | Y | - | - |
| `organizations.update` | Y | Y | - | - |
| `organizations.delete` | Y | - | - | - |
| `users.impersonate` | Y | - | - | - |
| `plans.manage` | Y | Y | - | - |
| `features.manage` | Y | Y | - | - |
| `crm.view` | Y | Y | Y | - |
| `crm.manage` | Y | Y | Y | - |
| `support.view` | Y | Y | - | Y |
| `support.manage` | Y | Y | - | Y |
| `audit.view` | Y | Y | - | - |

#### Organization Permissions

| Permission | owner | manager | staff | viewer |
|------------|:-----:|:-------:|:-----:|:------:|
| `organization.view` | Y | Y | Y | Y |
| `organization.update` | Y | Y | - | - |
| `organization.billing` | Y | - | - | - |
| `users.view` | Y | Y | - | - |
| `users.manage` | Y | Y | - | - |
| `menu.view` | Y | Y | Y | Y |
| `menu.create` | Y | Y | Y | - |
| `menu.update` | Y | Y | Y | - |
| `menu.delete` | Y | Y | - | - |
| `menu.publish` | Y | Y | - | - |
| `orders.view` | Y | Y | Y | Y |
| `orders.create` | Y | Y | Y | - |
| `orders.update` | Y | Y | Y | - |
| `orders.cancel` | Y | Y | - | - |
| `tables.view` | Y | Y | Y | Y |
| `tables.manage` | Y | Y | Y | - |
| `qr.view` | Y | Y | Y | Y |
| `qr.manage` | Y | Y | - | - |
| `analytics.view` | Y | Y | - | Y |
| `analytics.export` | Y | Y | - | - |
| `ai.content` | Y | Y | Y | - |
| `ai.image` | Y | Y | - | - |
| `settings.view` | Y | Y | - | - |
| `settings.update` | Y | Y | - | - |
| `media.view` | Y | Y | Y | Y |
| `media.create` | Y | Y | Y | - |

### 3.3 ABAC Rules (Attribute-Based)

```
TENANT ISOLATION (Always applied via TenantMiddleware):
  Rule: request.organization is resolved from user FK, header, or cookie
  Enforcement: TenantMiddleware injects request.organization
  All tenant-scoped views filter by request.organization
  Effect: DENY (403 TENANT_CONTEXT_REQUIRED) if missing on protected paths

PLAN-BASED RESTRICTIONS (PlanEnforcementService):
  Rule: feature.flag enabled on organization's active Plan
  Enforcement: RequiresPlanFeature DRF permission class
  Example: AI features require Plan.feature_flags['ai_content_generation'] = True
  Effect: DENY + FeatureNotAvailable exception with upgrade prompt

RESOURCE LIMITS (PlanEnforcementService):
  Rule: organization.resource_count < plan.limits[key]
  Enforcement: CheckPlanLimit DRF permission + PlanEnforcementMixin
  Examples:
    - Free: max 3 categories, 15 products (plan.limits['max_products'])
    - Starter: max 1 menu (plan.limits['max_menus'])
  Effect: DENY + PlanLimitExceeded exception with current/limit counts

FEATURE FLAGS:
  Rule: Plan.feature_flags[feature_code] == True
  Enforcement: PlanEnforcementService.check_feature()
  Use cases: Beta features, gradual rollout, A/B testing
  Effect: DENY + FeatureNotAvailable message

ADMIN OVERRIDES:
  Rule: Organization-level overrides for specific features
  Use cases: Grant feature to specific org, trial extensions, partner access
  Effect: ALLOW despite plan restrictions
```

### 3.4 Ability System (CASL-like)

The custom permission system in `shared/permissions/abilities.py` implements a
CASL-inspired ability builder for Django:

```python
# Core classes:
# - Rule: dataclass with action, resource, inverted, conditions
# - Ability: holds rules list, provides can()/cannot() methods
# - build_ability_for_user(user, organization) -> Ability

# Build ability from user's roles and permissions
ability = build_ability_for_user(user, organization)

# Simple permission check
if ability.can('create', 'menu'):
    ...

# Object-level check with ABAC conditions
if ability.can('update', 'menu', menu_instance):
    ...

# Conditions support variable substitution:
# {'organization_id': '${user.organization_id}'}
# {'organization_id': '${organization.id}'}
```

Rule evaluation: last matching rule wins, enabling deny-override patterns.
Plan-gated features add inverted (deny) rules that override role-based grants.

### 3.5 DRF Permission Classes

Ten permission classes in `shared/permissions/`:

| Class | Module | Purpose |
|-------|--------|---------|
| `HasOrganizationPermission` | abilities.py | Check org-scoped permission code |
| `HasPlatformPermission` | abilities.py | Check platform-level permission code |
| `IsTenantMember` | abilities.py | Verify user belongs to current tenant |
| `IsOwnerOrReadOnly` | abilities.py | Object ownership for write ops |
| `IsAuthenticatedOrReadOnly` | abilities.py | Read=public, write=authenticated |
| `AllowPublicRead` | abilities.py | Public read access (menu display) |
| `OrganizationScopedPermission` | drf_permissions.py | Action-based permission mapping |
| `ActionBasedPermission` | drf_permissions.py | Multi-permission per action (ALL/ANY) |
| `RequiresPlanFeature` | plan_enforcement.py | Feature gate by subscription plan |
| `CheckPlanLimit` | plan_enforcement.py | Resource limit on create actions |

Factory functions:

| Function | Purpose |
|----------|---------|
| `make_organization_permission(code)` | Create org-scoped permission class |
| `make_platform_permission(code)` | Create platform permission class |
| `make_composite_permission(classes, op)` | Combine classes with AND/OR logic |

### 3.6 Admin Panel Protection

The Django admin panel uses `EMenumPermissionMixin` from
`shared/permissions/admin_permission_mixin.py` to bridge Django admin's
built-in permission checks with the custom RBAC/ABAC ability system:

```python
@admin.register(Menu)
class MenuAdmin(EMenumPermissionMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    emenum_resource = 'menu'  # Maps to ability resource name
```

The mixin overrides `has_module_permission`, `has_view_permission`,
`has_add_permission`, `has_change_permission`, and `has_delete_permission` to
use `build_ability_for_user()` instead of Django's auth_permission table.

Platform-level admin views (dashboard, settings, reports) are protected by the
`@superadmin_required` decorator from `shared/decorators.py`, which restricts
access to `is_superuser=True` users only.

---

## 4. MULTI-TENANCY

### 4.1 TenantMiddleware

Located at `shared/middleware/tenant.py`, the `TenantMiddleware` runs after
`AuthenticationMiddleware` and injects organization context into every request.

```
Resolution Order:
1. Authenticated user's organization FK (user.organization)
2. X-Organization-ID header (for admin/multi-org users)
3. emenum_org_id cookie (for session persistence)
4. None for anonymous/public endpoints

Request Attributes Injected:
  request.organization      -> Organization instance or None
  request.organization_id   -> UUID or None
  request.is_tenant_aware   -> bool

Public URL Prefixes (no tenant required):
  /admin/, /health/, /api/v1/auth/, /api/v1/public/, /static/, /media/, /m/

Tenant Required Prefixes (403 if missing):
  /api/v1/menus/, /api/v1/categories/, /api/v1/products/,
  /api/v1/orders/, /api/v1/tables/, /api/v1/qr-codes/,
  /api/v1/customers/, /api/v1/analytics/
```

### 4.2 TenantContextMixin

`TenantContextMixin` provides helper methods for ViewSets:

```python
class MenuViewSet(TenantContextMixin, viewsets.ModelViewSet):
    def get_queryset(self):
        return Menu.objects.filter(
            organization=self.get_organization(),
            deleted_at__isnull=True
        )
```

---

## 5. DATA PROTECTION

### 5.1 Encryption

```
IN TRANSIT:
  Protocol:     TLS 1.3
  Cipher:       AES-256-GCM
  Certificate:  Let's Encrypt (auto-renewed)
  HSTS:         max-age=31536000; includeSubDomains; preload

AT REST:
  Database:     PostgreSQL TDE (Transparent Data Encryption)
  Backups:      AES-256 encrypted
  File storage: Server-side encryption

PII FIELDS (Application-level):
  Algorithm:    AES-256-GCM
  Key:          Per-organization (derived from master)
  Fields:       phone, address, paymentInfo
  Searchable:   Blind index for encrypted fields
```

### 5.2 PII Classification

| Field | Classification | Encryption | Retention |
|-------|----------------|------------|-----------|
| Email | PII | No (needed for login) | Account lifetime |
| Phone | PII | Yes | Account lifetime |
| Password | Secret | Hash (BCrypt 12 rounds) | N/A (hashed) |
| Address | PII | Yes | Account lifetime |
| Payment info | PCI | External (Iyzico) | Not stored |
| IP address | PII | No | 90 days |
| Order history | Business | No | 3 years |

### 5.3 Data Masking

```
API Response Masking:
  Email:      u***@example.com
  Phone:      +90 5** *** ** 89
  Card:       **** **** **** 1234

Logs Masking:
  Passwords: [REDACTED]
  Tokens: tok_xxx...xxx (truncated)
  PII: Hashed or masked
  Request body: Sensitive fields removed
```

---

## 6. AUDIT LOGGING

### 6.1 AuditLog Model

The `AuditLog` model in `apps/core/models.py` captures all significant actions.
AuditLog records are NEVER deleted (no soft delete). Retention: 2 years, then
archive to cold storage.

```
AuditLog fields:
  id                UUID PK
  organization      FK to Organization (nullable for platform-level)
  user              FK to User (nullable for system actions)
  action            CharField with AuditAction choices (CREATE, UPDATE, DELETE, etc.)
  resource          CharField - resource type (e.g., 'menu', 'order', 'user')
  resource_id       CharField - affected resource UUID
  description       TextField - human-readable description
  old_values        JSONField - snapshot before change
  new_values        JSONField - snapshot after change
  ip_address        GenericIPAddressField
  user_agent        CharField
  metadata          JSONField - additional context
  created_at        DateTimeField (auto_now_add)

Indexes:
  (organization, created_at)
  (user, created_at)
  (resource, resource_id)
  (action, created_at)
```

### 6.2 Audit Events

```
AUTHENTICATION EVENTS:
  auth.login.success
  auth.login.failure
  auth.logout
  auth.token.refresh
  auth.password.reset.request
  auth.password.reset.complete
  auth.password.change

AUTHORIZATION EVENTS:
  authz.permission.denied
  authz.role.assigned
  authz.role.removed
  authz.impersonation.start/end

DATA EVENTS:
  data.{resource}.created
  data.{resource}.updated
  data.{resource}.deleted
  data.export.requested
  data.bulk.operation

ADMIN EVENTS:
  admin.user.created
  admin.user.suspended
  admin.organization.created
  admin.plan.changed
  admin.feature.toggled
  admin.override.granted

SECURITY EVENTS:
  security.rate.limited
  security.suspicious.activity
  security.token.revoked
  security.breach.detected
```

### 6.3 Audit Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Security events | 2 years | Hot (database) |
| Auth events | 1 year | Hot to Cold |
| Data events | 1 year | Hot to Cold |
| Admin events | 2 years | Hot |
| Access logs | 90 days | Cold |

---

## 7. THREAT MODEL

### 7.1 OWASP Top 10 Mitigations

| Threat | Mitigation |
|--------|------------|
| **A01: Broken Access Control** | Custom RBAC + ABAC, TenantMiddleware isolation, django-guardian object perms |
| **A02: Cryptographic Failures** | TLS 1.3, AES-256, BCrypt 12 rounds, secure key management |
| **A03: Injection** | Django ORM (parameterized queries), DRF serializer validation |
| **A04: Insecure Design** | Threat modeling, security reviews |
| **A05: Security Misconfiguration** | Django SecurityMiddleware, secure defaults, env validation |
| **A06: Vulnerable Components** | Dependabot, pip-audit, safety scanning |
| **A07: Auth Failures** | simplejwt best practices, DRF throttling, account lockout |
| **A08: Data Integrity** | DRF serializer validation, Django CSRF middleware, SRI |
| **A09: Logging Failures** | AuditLog model, comprehensive monitoring, alerting |
| **A10: SSRF** | URL validation, allowlist, network isolation |

### 7.2 Attack Surface

```
EXTERNAL ENTRY POINTS:
  1. Public API endpoints (/api/v1/public/*)
     Risk: Abuse, scraping, DDoS
     Mitigation: DRF throttling, CAPTCHA, CDN

  2. Authentication endpoints (/api/v1/auth/*)
     Risk: Brute force, credential stuffing
     Mitigation: DRF AnonRateThrottle, lockout, breach detection

  3. File uploads (images via apps/media/)
     Risk: Malware, path traversal
     Mitigation: Type validation, scanning, isolated storage

  4. Webhook endpoints
     Risk: Spoofing, replay attacks
     Mitigation: Signature verification, idempotency

INTERNAL RISKS:
  1. Cross-tenant access
     Risk: Data leakage between organizations
     Mitigation: TenantMiddleware, mandatory organization filter, code review

  2. Privilege escalation
     Risk: User gains higher permissions
     Mitigation: Server-side role checks via Ability system, no client trust

  3. Insider threat
     Risk: Malicious admin action
     Mitigation: AuditLog, @superadmin_required, separation of duties
```

### 7.3 Security Headers

```
Django SecurityMiddleware + django-cors-headers:

Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' cdn.jsdelivr.net;
  style-src 'self' 'unsafe-inline' cdn.jsdelivr.net;
  img-src 'self' data: https:;
  font-src 'self' cdn.jsdelivr.net;
  connect-src 'self' api.e-menum.net;
  frame-ancestors 'none';

X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0 (disabled, CSP preferred)
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()

CSRF: Django CsrfViewMiddleware enabled on all form submissions
CORS: django-cors-headers with explicit CORS_ALLOWED_ORIGINS
```

---

## 8. INCIDENT RESPONSE

### 8.1 Incident Classification

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| P1 - Critical | Data breach, service down | 15 min | Immediate |
| P2 - High | Security vulnerability exploited | 1 hour | Same day |
| P3 - Medium | Suspicious activity, failed attacks | 4 hours | Next day |
| P4 - Low | Policy violation, minor issue | 24 hours | Weekly review |

### 8.2 Response Playbook

```
1. DETECTION
   - Automated alerts (DRF throttle triggers, auth failures in AuditLog)
   - User reports
   - AuditLog analysis

2. CONTAINMENT
   - Isolate affected systems
   - Blacklist compromised tokens via simplejwt token_blacklist
   - Block malicious IPs
   - Disable affected features

3. INVESTIGATION
   - Query AuditLog by organization, user, timeframe
   - Analyze attack vector
   - Identify scope of impact
   - Document timeline

4. REMEDIATION
   - Patch vulnerability
   - Reset affected credentials
   - Restore from clean backup (if needed)
   - Verify fix effectiveness

5. RECOVERY
   - Restore services gradually
   - Monitor for recurrence
   - Communicate with affected users

6. POST-INCIDENT
   - Write incident report
   - Update threat model
   - Improve detection/prevention
   - Conduct lessons learned
```

---

## 9. COMPLIANCE

### 9.1 KVKK (Turkish GDPR) Requirements

| Requirement | Implementation |
|-------------|----------------|
| Lawful basis | Consent at registration, legitimate interest |
| Data minimization | Only essential data collected |
| Purpose limitation | Defined in privacy policy |
| Storage limitation | Retention policies enforced |
| Right to access | Data export endpoint |
| Right to erasure | Account deletion flow (soft delete + GDPR hard delete procedure) |
| Right to portability | JSON/CSV export |
| Breach notification | 72-hour disclosure procedure |
| DPO designation | Designated contact |

### 9.2 Security Certifications (Future)

| Certification | Status | Target |
|---------------|--------|--------|
| SOC 2 Type I | Planned | Y2 |
| SOC 2 Type II | Planned | Y3 |
| ISO 27001 | Planned | Y3 |
| PCI DSS | Via Iyzico | N/A |

---

*Bu dokuman, E-Menum guvenlik modelini tanimlar. Tum implementasyonlar bu guvenlik gereksinimlerini karsilamalidir.*
