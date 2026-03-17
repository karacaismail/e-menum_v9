# Security Audit Report

**Project:** E-Menum Enterprise QR Menu SaaS
**Date:** 2026-03-17
**SAFe Role:** Security Architect
**Auditor:** E-Menum Engineering Team -- Automated Audit System
**Report Version:** 1.1.0
**Classification:** CONFIDENTIAL

---

## Executive Summary

| Metric | Score |
|--------|-------|
| **Overall Security Posture** | **78 / 100** |
| Authentication & Authorization | 85 / 100 |
| Data Protection | 75 / 100 |
| Network Security | 80 / 100 |
| Application Security (OWASP) | 78 / 100 |
| Multi-Tenant Isolation | 82 / 100 |
| Dependency Security | 70 / 100 |
| Secrets Management | 72 / 100 |

The E-Menum platform implements a multi-layered security architecture with JWT authentication, RBAC/ABAC authorization, BCrypt password hashing, and comprehensive DRF permission classes. The multi-tenant isolation pattern is well-designed with fail-safe defaults (empty queryset on missing org context). Key security concerns include the non-blocking pip-audit CI step, the commented-out TenantMiddleware, the absence of Content Security Policy headers at the application level, and the need for KVKK/GDPR-specific data handling procedures.

---

## 1. Authentication & Authorization Audit

### 1.1 JWT Configuration

| Parameter | Value | Assessment |
|-----------|-------|-----------|
| Access token lifetime | 15 minutes | GREEN -- Industry standard |
| Refresh token lifetime | 7 days (10080 min) | GREEN -- Appropriate |
| Rotate refresh tokens | True | GREEN -- Prevents token reuse |
| Blacklist after rotation | True | GREEN -- Old tokens invalidated |
| Update last login | True | GREEN -- Audit trail |
| Algorithm | HS256 | YELLOW -- Consider RS256 for service-to-service |
| Signing key | SECRET_KEY | YELLOW -- Shared with Django signing |
| Issuer | "e-menum" | GREEN |
| Auth header type | Bearer | GREEN |

**Finding SEC-01 (LOW):** JWT signing uses `HS256` with the Django `SECRET_KEY`. While acceptable for a monolith, if external services need to verify tokens, consider switching to `RS256` with asymmetric keys. The shared signing key means JWT secret rotation requires Django secret rotation.

### 1.2 Password Security

| Setting | Value | Assessment |
|---------|-------|-----------|
| Primary hasher | BCryptSHA256PasswordHasher | GREEN -- Gold standard |
| Fallback hashers | PBKDF2, Argon2, Scrypt | GREEN -- Upgrade path |
| Minimum length | 12 characters | GREEN -- Enterprise grade |
| Validators | UserAttributeSimilarity, CommonPassword, NumericPassword | GREEN |
| Brute force protection | DRF throttle: anon 50/hr (prod) | YELLOW -- No account lockout |

**Finding SEC-02 (MEDIUM):** There is no account lockout mechanism after failed login attempts. The DRF throttle (50/hr for anonymous) provides basic protection, but a dedicated brute-force prevention system (e.g., django-axes) would be more robust. The throttle applies per-IP, not per-account.

### 1.3 Session Management

| Setting | Value | Assessment |
|---------|-------|-----------|
| Cookie age | 7 days | GREEN |
| Cookie secure | Configurable (False in dev, env-based in prod) | YELLOW |
| Cookie HTTPOnly | True | GREEN |
| Cookie SameSite | Lax | GREEN |
| CSRF cookie secure | Configurable | YELLOW |
| CSRF cookie HTTPOnly | True | GREEN |

**Finding SEC-03 (MEDIUM):** `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` default to `False` in production (`production.py` lines 199-200) when `SECURE_SSL_REDIRECT` is False. Behind a reverse proxy that terminates SSL, cookies are transmitted over HTTP between proxy and Django. If the network is not trusted, cookies could be intercepted. The comment explains the rationale (proxy handles SSL), but this should be explicitly documented as accepted risk.

### 1.4 Impersonation Security

| Setting | Value | Assessment |
|---------|-------|-----------|
| Require superuser | False (custom function) | GREEN -- `can_impersonate()` |
| Max duration | 3600s (1 hour) | GREEN |
| Allow superuser impersonation | False | GREEN -- Cannot impersonate superusers |
| Admin read-only | True | GREEN -- Impersonated sees read-only admin |
| Custom allow function | `shared.utils.impersonate.can_impersonate` | GREEN |

### 1.5 Authentication Backends

```python
AUTHENTICATION_BACKENDS = [
    "apps.core.backends.EmailOrUsernameBackend",  # Custom: email OR username
    "django.contrib.auth.backends.ModelBackend",   # Django default
    "guardian.backends.ObjectPermissionBackend",    # django-guardian
]
```

**Assessment:** The custom `EmailOrUsernameBackend` enables flexible login. The backend chain is correctly ordered.

---

## 2. Data Protection Audit

### 2.1 Encryption

| Layer | Status | Details |
|-------|--------|---------|
| Transit (TLS) | CONFIGURED | SECURE_PROXY_SSL_HEADER set, HSTS configurable |
| At rest (database) | NOT CONFIGURED | PostgreSQL without TDE |
| At rest (media) | NOT CONFIGURED | Local filesystem, no encryption |
| At rest (Redis) | NOT CONFIGURED | Plain Redis, no TLS |
| At rest (backups) | UNKNOWN | No backup encryption documented |

**Finding SEC-04 (MEDIUM):** No encryption at rest for database, media, or cache. For KVKK (Turkish GDPR equivalent) compliance, PII should be encrypted at rest. Consider PostgreSQL pgcrypto for sensitive columns and Redis TLS.

### 2.2 PII Handling (GDPR/KVKK)

| PII Field | Model | Storage | Protection |
|-----------|-------|---------|-----------|
| Email | core.User | Database | Unique constraint, no encryption |
| Phone | core.User, core.Organization | Database | No encryption |
| Name | core.User | Database | No encryption |
| Address | core.Organization, core.Branch | Database | No encryption |
| Tax ID | core.Organization | Database | No encryption |
| IP addresses | seo_shield.IPRiskScore, seo_shield.BlockLog | Database | No encryption |
| Customer data | customers.Customer | Database | Org-scoped, no encryption |

**Finding SEC-05 (HIGH):** PII fields are stored in plaintext. For KVKK compliance:
- Tax IDs and phone numbers should be encrypted at rest
- A data processing inventory should be maintained
- Data retention policies need to be implemented
- Right to erasure (beyond soft delete) procedures are needed

### 2.3 Soft Delete & Data Retention

| Aspect | Status |
|--------|--------|
| Soft delete implementation | IMPLEMENTED -- `SoftDeleteMixin` on all business models |
| Hard delete procedure | NOT IMPLEMENTED -- No GDPR erasure command |
| Data retention policy | NOT DEFINED -- No automatic cleanup of old soft-deleted records |
| Audit trail | IMPLEMENTED -- `AuditLog` model in core app |

**Finding SEC-06 (MEDIUM):** While soft delete prevents accidental data loss, there is no mechanism for true data erasure (GDPR Article 17 / KVKK right to erasure). A management command for permanent PII removal is needed.

### 2.4 Backup & Recovery

| Aspect | Status |
|--------|--------|
| Database backups | NOT CONFIGURED in application layer |
| Media backups | NOT CONFIGURED -- local filesystem only |
| Backup encryption | UNKNOWN |
| Recovery testing | NOT DOCUMENTED |

**Finding SEC-07 (HIGH):** No backup strategy is configured at the application level. PostgreSQL volume is a named Docker volume (`postgres_data`), but there is no automated backup schedule, offsite storage, or recovery testing procedure.

---

## 3. Network Security

### 3.1 CORS Configuration

| Setting | Dev Value | Prod Value | Assessment |
|---------|-----------|-----------|-----------|
| CORS_ALLOWED_ORIGINS | env-based | `https://{SITE_DOMAIN}` + variants | GREEN |
| CORS_ALLOW_ALL_ORIGINS | Not set | False (explicit) | GREEN |
| CORS_ALLOW_CREDENTIALS | True | True | GREEN |
| CORS_ALLOW_METHODS | Full REST set | Inherited | GREEN |
| Custom headers | x-organization-id, x-csrftoken | Inherited | GREEN |

### 3.2 Security Headers

| Header | Config Location | Value | Status |
|--------|----------------|-------|--------|
| X-Frame-Options | base.py:113 | DENY | GREEN |
| X-Content-Type-Options | base.py:114 | nosniff | GREEN |
| X-XSS-Protection | base.py:112 | True | GREEN |
| Strict-Transport-Security | production.py:193 | Configurable (default 0) | YELLOW |
| Referrer-Policy | production.py:211 | strict-origin-when-cross-origin | GREEN |
| Content-Security-Policy | Not configured | Delegated to proxy | YELLOW |
| Permissions-Policy | Not configured | Missing | RED |

**Finding SEC-08 (MEDIUM):** `Content-Security-Policy` and `Permissions-Policy` headers are not configured at the Django level. While CSP can be handled by the reverse proxy, defense-in-depth recommends also configuring it in Django via `django-csp` or middleware.

### 3.3 Rate Limiting

| Layer | Config | Rates |
|-------|--------|-------|
| DRF Throttling | base.py:362-369 | anon: 100/hr (dev), 50/hr (prod); user: 1000/hr |
| SEO Shield | base.py:910-922 | 120 req/60s window, challenge at 120, block at 160 |
| Shield IP whitelist | base.py:922 | 127.0.0.1, ::1 |

### 3.4 Bot Protection (SEO Shield)

| Feature | Status | Location |
|---------|--------|----------|
| Rate limiter | IMPLEMENTED | seo_shield/middleware.py |
| Bot verifier | IMPLEMENTED | Tested (25 tests) |
| Risk engine | IMPLEMENTED | Tested (24 tests) |
| IP risk scoring | IMPLEMENTED | seo_shield/models.py:95 |
| Rule-based blocking | IMPLEMENTED | seo_shield/models.py:189 |
| Block logging | IMPLEMENTED | seo_shield/models.py:264 |
| Whitelist management | IMPLEMENTED | seo_shield/models.py:20 |

---

## 4. Application Security (OWASP Top 10)

### A01: Broken Access Control

| Check | Status | Details |
|-------|--------|---------|
| Permission classes on all ViewSets | GREEN | BaseTenantViewSet enforces 3 permission classes |
| Object-level permissions | GREEN | django-guardian configured |
| Tenant isolation | GREEN | TenantFilterMixin with empty queryset fallback |
| Horizontal privilege escalation | YELLOW | No cross-tenant test suite |
| Vertical privilege escalation | GREEN | Role-based checks in place |
| Impersonation controls | GREEN | 1hr max, superuser-only, read-only admin |

**Finding SEC-09 (HIGH):** While the architecture is sound, the absence of dedicated cross-tenant penetration tests means there is no verified assurance that tenant isolation cannot be bypassed through edge cases (e.g., nested serializer includes, filter parameter manipulation).

### A02: Cryptographic Failures

| Check | Status | Details |
|-------|--------|---------|
| Password hashing | GREEN | BCryptSHA256, 12-char minimum |
| JWT token security | GREEN | HS256, short-lived access tokens |
| Secrets in code | GREEN | All secrets via env vars in production |
| PII encryption at rest | RED | Plaintext storage (see SEC-04/05) |

### A03: Injection

| Check | Status | Details |
|-------|--------|---------|
| SQL injection | GREEN | Django ORM exclusively, parameterized queries |
| NoSQL injection | N/A | No NoSQL databases |
| Command injection | GREEN | No shell command execution found |
| LDAP injection | N/A | No LDAP |
| Template injection | GREEN | Django auto-escaping enabled |

### A04: Insecure Design

| Check | Status | Details |
|-------|--------|---------|
| Rate limiting | GREEN | DRF throttle + SEO Shield |
| Plan enforcement | GREEN | PlanEnforcementService with limit checking |
| Input validation | GREEN | DRF Serializers + Django validators |
| Error information leakage | GREEN | Custom exception handler, no stack traces |

### A05: Security Misconfiguration

| Check | Status | Details |
|-------|--------|---------|
| Debug mode in prod | GREEN | DEBUG=False enforced |
| Secret key management | GREEN | Required via env var in production.py |
| Default credentials | YELLOW | docker-compose.prod.yml has default superuser password |
| Unnecessary features | GREEN | Browsable API disabled in production |
| Security headers | YELLOW | CSP and Permissions-Policy missing |

**Finding SEC-10 (MEDIUM):** `docker-compose.prod.yml` line 87 contains `DJANGO_SUPERUSER_PASSWORD: ${DJANGO_SUPERUSER_PASSWORD:-admin123}`. The default fallback password `admin123` is insecure. While it requires the env var to be unset, this default should be removed.

### A06: Vulnerable and Outdated Components

| Check | Status | Details |
|-------|--------|---------|
| pip-audit in CI | YELLOW | Configured but non-blocking (`|| true`) |
| Django version | GREEN | 5.0 (current) |
| Python version | GREEN | 3.13 (latest) |
| Node.js version | GREEN | 20 (LTS) |
| Dependency pinning | YELLOW | Range specifiers, not exact pins |

### A07: Identification and Authentication Failures

| Check | Status | Details |
|-------|--------|---------|
| Credential stuffing protection | YELLOW | Rate limiting only, no account lockout |
| Password policy | GREEN | 12-char min, common password check |
| Session fixation | GREEN | Django rotates session on login |
| Token rotation | GREEN | Refresh token rotation + blacklist |

### A08: Software and Data Integrity Failures

| Check | Status | Details |
|-------|--------|---------|
| Deserialization attacks | GREEN | DRF JSON parser, no pickle/yaml |
| CI/CD pipeline integrity | GREEN | GitHub Actions, checkout@v4 |
| Dependency integrity | YELLOW | No hash pinning in requirements.txt |

### A09: Security Logging and Monitoring Failures

| Check | Status | Details |
|-------|--------|---------|
| AuditLog model | GREEN | `apps/core/models.py:1461` |
| Authentication logging | GREEN | `UPDATE_LAST_LOGIN: True` |
| Error logging | GREEN | JSON format in production, Sentry optional |
| Security event alerting | RED | No real-time security alerts |
| Log retention policy | NOT DEFINED | Docker stdout/stderr only |

**Finding SEC-11 (MEDIUM):** While audit logging models exist, there is no security information and event management (SIEM) integration. Security events (failed logins, permission denials, rate limit hits) should trigger alerts.

### A10: Server-Side Request Forgery (SSRF)

| Check | Status | Details |
|-------|--------|---------|
| QR code logo download | YELLOW | `requests` library used for logo URLs |
| External API calls | YELLOW | AI API calls to OpenAI/Anthropic |
| URL validation | NOT VERIFIED | Need to check URL sanitization |

**Finding SEC-12 (MEDIUM):** The QR code generation feature downloads logos from user-provided URLs using the `requests` library. This is a potential SSRF vector if URLs are not validated to prevent access to internal services (e.g., `http://169.254.169.254/` for cloud metadata).

---

## 5. Multi-Tenant Isolation Audit

### 5.1 Architecture Review

| Layer | Implementation | Status |
|-------|----------------|--------|
| View layer | TenantFilterMixin in BaseTenantViewSet | GREEN |
| Queryset layer | `.filter(organization=org)` in get_queryset | GREEN |
| Create layer | Auto-inject organization in perform_create | GREEN |
| Update layer | Organization consistency check in perform_update | GREEN |
| Fail-safe | Empty queryset on missing org context | GREEN |
| Object-level | get_object() validates org ownership | GREEN |
| Middleware | TenantMiddleware (COMMENTED OUT) | YELLOW |

### 5.2 Isolation Verification

| Scenario | Verification Status |
|----------|-------------------|
| API GET returns only own org data | ARCHITECTURALLY ENFORCED, NOT TESTED |
| API POST creates in own org only | ARCHITECTURALLY ENFORCED, NOT TESTED |
| API PUT/PATCH validates org match | ARCHITECTURALLY ENFORCED, NOT TESTED |
| Nested resource isolation (Product via Category via Menu) | NEEDS VERIFICATION |
| Filter parameter injection (e.g., `?organization_id=other`) | NEEDS VERIFICATION |
| Serializer field exposure (organization_id in response) | NEEDS VERIFICATION |

**Finding SEC-13 (HIGH):** The multi-tenant isolation architecture is well-designed with defense-in-depth (view filtering + object validation + empty queryset fallback). However, there are no automated tests verifying these isolation properties. A penetration test specifically targeting cross-tenant access should be conducted before production launch.

---

## 6. Dependency Vulnerability Scan

### 6.1 CI Configuration

```yaml
- name: pip-audit (vulnerability scan)
  run: pip-audit --strict --desc on 2>&1 || true
```

**Finding SEC-14 (MEDIUM):** The `|| true` means the CI pipeline will not fail on known vulnerabilities. This was intentionally added as a temporary measure. A timeline should be set to:
1. Run `pip-audit` manually to identify current vulnerabilities
2. Fix or suppress known issues with justification
3. Remove `|| true` to enforce vulnerability-free builds

### 6.2 Dependency Risk Assessment

| Package | Risk | Notes |
|---------|------|-------|
| xhtml2pdf | MEDIUM | Niche PDF library, processes HTML/CSS -- potential for injection |
| requests | LOW | Well-maintained, but SSRF risk in usage |
| python-magic | LOW | Calls libmagic for MIME detection |
| Pillow | LOW | Image processing, historically has had CVEs |
| django-filer | LOW | File management, MIME whitelist configured |

---

## 7. Secrets Management

### 7.1 Current Approach

| Secret | Source | Assessment |
|--------|--------|-----------|
| DJANGO_SECRET_KEY | Environment variable | GREEN |
| DATABASE_URL | Environment variable | GREEN |
| REDIS_URL | Environment variable | GREEN |
| MAILGUN_API_KEY | Environment variable | GREEN |
| AI_API_KEY | Environment variable | GREEN |
| DEPLOY_WEBHOOK_URL | GitHub Secret | GREEN |

### 7.2 Concerns

| Issue | Details | Severity |
|-------|---------|----------|
| Default secret key in base.py | `django-insecure-change-this...` | LOW (only in dev, prod raises ValueError) |
| Default superuser password | `admin123` in docker-compose.prod.yml | MEDIUM |
| No secrets rotation policy | No documented rotation schedule | MEDIUM |
| No vault integration | Secrets in env vars, not encrypted vault | LOW (appropriate for current scale) |

**Finding SEC-15 (LOW):** The production settings correctly raise `ValueError` if `DJANGO_SECRET_KEY` is not set. This is a strong safeguard. Consider implementing periodic key rotation.

**Finding SEC-16 (RESOLVED):** Media files now served in production via Django `re_path` in urls.py, eliminating the need for users to bypass security for file access.

---

## 8. Recommendations (Prioritized)

### Critical (Immediate)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| SEC-R01 | Create cross-tenant penetration test suite | 8h | CRITICAL |
| SEC-R02 | Remove default `admin123` password from docker-compose.prod.yml | 1h | HIGH |
| SEC-R03 | Implement SSRF protection for QR logo URL downloads | 4h | HIGH |

### High (Next Sprint)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| SEC-R04 | Add account lockout mechanism (django-axes) | 4h | HIGH |
| SEC-R05 | Make pip-audit a hard failure in CI | 2h | MEDIUM |
| SEC-R06 | Implement PII encryption for sensitive fields (tax_id, phone) | 16h | HIGH |
| SEC-R07 | Create data erasure management command for KVKK compliance | 8h | HIGH |

### Medium (Next PI)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| SEC-R08 | Add Content-Security-Policy headers (django-csp) | 4h | MEDIUM |
| SEC-R09 | Add Permissions-Policy header | 2h | MEDIUM |
| SEC-R10 | Configure database backup automation with encryption | 8h | HIGH |
| SEC-R11 | Set up security event alerting (failed logins, rate limits) | 8h | MEDIUM |
| SEC-R12 | Document secrets rotation policy | 2h | LOW |
| SEC-R13 | Pin dependency hashes in requirements.txt | 4h | LOW |

### Low (Backlog)

| # | Recommendation | Effort | Impact |
|---|---------------|--------|--------|
| SEC-R14 | Consider RS256 for JWT if external token verification needed | 4h | LOW |
| SEC-R15 | Add Redis TLS configuration | 4h | LOW |
| SEC-R16 | Implement data retention policy with auto-cleanup | 16h | MEDIUM |

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-17 | Automated Audit System | Initial security audit |
| 1.1.0 | 2026-03-17 | Automated Audit System | Updated with post-deploy fixes and accurate metrics |
