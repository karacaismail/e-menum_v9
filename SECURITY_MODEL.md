# E-Menum Security Model

> **Auto-Claude Security Document**  
> Authentication, authorization, data protection, audit logging, threat model.  
> Son Güncelleme: 2026-01-31

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

### 1.2 Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY LAYERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: NETWORK                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Cloudflare DDoS protection                                        │ │
│  │  • TLS 1.3 encryption                                                │ │
│  │  • HSTS enforcement                                                  │ │
│  │  • IP reputation filtering                                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 2: APPLICATION                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Rate limiting                                                     │ │
│  │  • Input validation (Zod)                                            │ │
│  │  • CORS policy                                                       │ │
│  │  • Security headers (Helmet)                                         │ │
│  │  • CSRF protection                                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 3: AUTHENTICATION                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • JWT access tokens (short-lived)                                   │ │
│  │  • Refresh tokens (httpOnly cookie)                                  │ │
│  │  • Password hashing (bcrypt)                                         │ │
│  │  • Session management                                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 4: AUTHORIZATION                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • RBAC (Role-Based Access Control)                                  │ │
│  │  • ABAC (Attribute-Based Access Control)                             │ │
│  │  • Tenant isolation                                                  │ │
│  │  • Resource ownership                                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Layer 5: DATA                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  • Encryption at rest (PostgreSQL TDE)                               │ │
│  │  • Encryption in transit (TLS)                                       │ │
│  │  • PII field encryption                                              │ │
│  │  • Secure key management                                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AUTHENTICATION

### 2.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AUTHENTICATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REGISTRATION:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Client                    Server                    Database       │   │
│  │    │                         │                          │          │   │
│  │    │──POST /auth/register───►│                          │          │   │
│  │    │  {email, password}      │                          │          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Validate input──────────┤          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Check email exists──────►│          │   │
│  │    │                         │◄─────────────────────────│          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Hash password (bcrypt)──┤          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Create user─────────────►│          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Send verification email─┤          │   │
│  │    │                         │                          │          │   │
│  │    │◄──201 Created───────────│                          │          │   │
│  │    │  {userId, message}      │                          │          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOGIN:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Client                    Server                    Redis          │   │
│  │    │                         │                          │          │   │
│  │    │──POST /auth/login──────►│                          │          │   │
│  │    │  {email, password}      │                          │          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Validate credentials────┤          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Check rate limit────────►│          │   │
│  │    │                         │◄─────────────────────────│          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Generate tokens─────────┤          │   │
│  │    │                         │  • accessToken (15min)   │          │   │
│  │    │                         │  • refreshToken (7d)     │          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Store refresh token─────►│          │   │
│  │    │                         │                          │          │   │
│  │    │◄──200 OK────────────────│                          │          │   │
│  │    │  {accessToken}          │                          │          │   │
│  │    │  Set-Cookie: refresh    │                          │          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOKEN REFRESH:                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  Client                    Server                    Redis          │   │
│  │    │                         │                          │          │   │
│  │    │──POST /auth/refresh────►│                          │          │   │
│  │    │  Cookie: refreshToken   │                          │          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Validate token──────────┤          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Check whitelist─────────►│          │   │
│  │    │                         │◄─────────────────────────│          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Rotate tokens───────────┤          │   │
│  │    │                         │  • Revoke old refresh    │          │   │
│  │    │                         │  • Issue new pair        │          │   │
│  │    │                         │                          │          │   │
│  │    │                         │──Update whitelist────────►│          │   │
│  │    │                         │                          │          │   │
│  │    │◄──200 OK────────────────│                          │          │   │
│  │    │  {accessToken}          │                          │          │   │
│  │    │  Set-Cookie: refresh    │                          │          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Token Specifications

| Token | Type | Storage | Expiry | Purpose |
|-------|------|---------|--------|---------|
| Access Token | JWT | Memory/Header | 15 min | API authentication |
| Refresh Token | Opaque | httpOnly cookie | 7 days | Token renewal |
| Verification Token | Opaque | Database | 24 hours | Email verification |
| Reset Token | Opaque | Database | 1 hour | Password reset |

### 2.3 JWT Structure

```
Access Token Payload:
{
  "sub": "usr_xxx",              // User ID
  "org": "org_xxx",              // Organization ID
  "role": "owner",               // Primary role
  "permissions": ["menu.view"],  // Cached permissions
  "iat": 1706702400,             // Issued at
  "exp": 1706703300,             // Expiry (15 min)
  "jti": "tok_xxx"               // Token ID (for revocation)
}

Signing:
├── Algorithm: RS256 (RSA + SHA-256)
├── Key rotation: Monthly
└── Key storage: Environment variable / Secret manager
```

### 2.4 Password Policy

| Requirement | Value |
|-------------|-------|
| Minimum length | 8 characters |
| Complexity | 1 uppercase, 1 lowercase, 1 number |
| Common password check | Yes (top 10K list) |
| Hash algorithm | bcrypt |
| Hash rounds | 12 |
| Max age | None (optional reminder) |

### 2.5 Brute Force Protection

```
Rate Limiting per Endpoint:

/auth/login:
├── Per IP: 5 attempts / 15 min
├── Per email: 10 attempts / hour
└── Global: 1000 attempts / min

/auth/forgot-password:
├── Per IP: 3 attempts / hour
└── Per email: 1 attempt / 5 min

Account Lockout:
├── Threshold: 10 failed attempts
├── Duration: 30 minutes
└── Unlock: Email verification or support
```

---

## 3. AUTHORIZATION (RBAC + ABAC)

### 3.1 Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROLE HIERARCHY                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLATFORM ROLES (System-wide):                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │                        super_admin                                    │ │
│  │                             │                                         │ │
│  │              ┌──────────────┼──────────────┐                         │ │
│  │              │              │              │                         │ │
│  │           admin          sales        support                        │ │
│  │                                                                       │ │
│  │  Scope: All organizations, system settings                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ORGANIZATION ROLES (Tenant-scoped):                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │                          owner                                        │ │
│  │                            │                                          │ │
│  │                        manager                                        │ │
│  │                            │                                          │ │
│  │              ┌─────────────┼─────────────┐                           │ │
│  │              │             │             │                           │ │
│  │           staff        cashier       viewer                          │ │
│  │                                                                       │ │
│  │  Scope: Single organization resources only                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PUBLIC ROLES (Unauthenticated):                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │    customer (optional auth)    │    anonymous (no auth)              │ │
│  │                                                                       │ │
│  │  Scope: Public endpoints only                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Permission Matrix

#### Platform Permissions

| Permission | super_admin | admin | sales | support |
|------------|:-----------:|:-----:|:-----:|:-------:|
| `platform.manage` | ✓ | - | - | - |
| `organizations.view` | ✓ | ✓ | ✓ | ✓ |
| `organizations.create` | ✓ | ✓ | - | - |
| `organizations.update` | ✓ | ✓ | - | - |
| `organizations.delete` | ✓ | - | - | - |
| `users.impersonate` | ✓ | - | - | - |
| `plans.manage` | ✓ | ✓ | - | - |
| `features.manage` | ✓ | ✓ | - | - |
| `crm.view` | ✓ | ✓ | ✓ | - |
| `crm.manage` | ✓ | ✓ | ✓ | - |
| `support.view` | ✓ | ✓ | - | ✓ |
| `support.manage` | ✓ | ✓ | - | ✓ |
| `audit.view` | ✓ | ✓ | - | - |

#### Organization Permissions

| Permission | owner | manager | staff | cashier | viewer |
|------------|:-----:|:-------:|:-----:|:-------:|:------:|
| `organization.view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `organization.update` | ✓ | ✓ | - | - | - |
| `organization.billing` | ✓ | - | - | - | - |
| `users.view` | ✓ | ✓ | - | - | - |
| `users.manage` | ✓ | ✓ | - | - | - |
| `menu.view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `menu.create` | ✓ | ✓ | ✓ | - | - |
| `menu.update` | ✓ | ✓ | ✓ | - | - |
| `menu.delete` | ✓ | ✓ | - | - | - |
| `menu.publish` | ✓ | ✓ | - | - | - |
| `orders.view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `orders.create` | ✓ | ✓ | ✓ | ✓ | - |
| `orders.update` | ✓ | ✓ | ✓ | ✓ | - |
| `orders.cancel` | ✓ | ✓ | - | - | - |
| `tables.view` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `tables.manage` | ✓ | ✓ | ✓ | - | - |
| `qr.view` | ✓ | ✓ | ✓ | - | ✓ |
| `qr.manage` | ✓ | ✓ | - | - | - |
| `analytics.view` | ✓ | ✓ | - | - | ✓ |
| `analytics.export` | ✓ | ✓ | - | - | - |
| `ai.content` | ✓ | ✓ | ✓ | - | - |
| `ai.image` | ✓ | ✓ | - | - | - |
| `ai.query` | ✓ | ✓ | - | - | - |
| `settings.view` | ✓ | ✓ | - | - | - |
| `settings.update` | ✓ | ✓ | - | - | - |

### 3.3 ABAC Rules (Attribute-Based)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ABAC RULES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TENANT ISOLATION (Always applied):                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: resource.organizationId === user.organizationId                │ │
│  │  Effect: DENY if mismatch                                             │ │
│  │  Priority: Highest                                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PLAN-BASED RESTRICTIONS:                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: feature.minPlan <= organization.plan                           │ │
│  │  Example: AI features require "professional" plan                     │ │
│  │  Effect: DENY + upgrade prompt                                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  RESOURCE LIMITS:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: organization.usage < plan.limits                               │ │
│  │  Examples:                                                            │ │
│  │  • Free: max 3 categories, 15 products                               │ │
│  │  • Starter: max 1 menu, 5000 QR scans/month                          │ │
│  │  Effect: DENY + limit message                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FEATURE FLAGS:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: feature.flag.enabled === true                                  │ │
│  │  Use cases:                                                           │ │
│  │  • Beta features for select orgs                                     │ │
│  │  • Gradual rollout                                                   │ │
│  │  • A/B testing                                                        │ │
│  │  Effect: DENY + not available message                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ADMIN OVERRIDES:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: organization.overrides[feature] === true                       │ │
│  │  Use cases:                                                           │ │
│  │  • Grant feature to specific org                                     │ │
│  │  • Trial extensions                                                  │ │
│  │  • Partner special access                                            │ │
│  │  Effect: ALLOW despite plan restrictions                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TIME-BASED RULES:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Rule: currentTime within allowed window                              │ │
│  │  Examples:                                                            │ │
│  │  • Staff can only access during shift hours                          │ │
│  │  • Trial access expires at trialEndsAt                               │ │
│  │  Effect: DENY + time restriction message                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 CASL Ability Definition

```
Ability Builder Pattern:

defineAbilitiesFor(user, organization, plan):

  // Platform admins
  if (user.isPlatformAdmin):
    can('manage', 'all')
    return

  // Tenant isolation (CRITICAL)
  cannot('manage', 'all')
  can('read', 'Organization', { id: organization.id })
  
  // Role-based permissions
  switch (user.role):
    case 'owner':
      can('manage', 'Organization', { id: organization.id })
      can('manage', 'User', { organizationId: organization.id })
      can('manage', 'Menu', { organizationId: organization.id })
      can('manage', 'Order', { organizationId: organization.id })
      can('view', 'Analytics', { organizationId: organization.id })
      can('use', 'AI', { organizationId: organization.id })
      break
      
    case 'manager':
      can('read', 'Organization', { id: organization.id })
      can('manage', 'User', { organizationId: organization.id, role: { $ne: 'owner' } })
      can('manage', 'Menu', { organizationId: organization.id })
      can('manage', 'Order', { organizationId: organization.id })
      can('view', 'Analytics', { organizationId: organization.id })
      break
      
    case 'staff':
      can('read', 'Menu', { organizationId: organization.id })
      can('update', 'Menu', { organizationId: organization.id })
      can('manage', 'Order', { organizationId: organization.id })
      break
      
    case 'viewer':
      can('read', 'Menu', { organizationId: organization.id })
      can('read', 'Order', { organizationId: organization.id })
      can('read', 'Analytics', { organizationId: organization.id })
      break

  // Plan-based restrictions (ABAC layer)
  if (plan.tier < 'professional'):
    cannot('use', 'AI')
    
  if (plan.tier < 'business'):
    cannot('access', 'API')
    cannot('manage', 'Branch')
    
  // Feature flags
  for (flag in organization.disabledFeatures):
    cannot('use', flag.resource, flag.conditions)
    
  // Overrides (admin granted)
  for (override in organization.overrides):
    can(override.action, override.resource, override.conditions)
```

---

## 4. DATA PROTECTION

### 4.1 Encryption

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA ENCRYPTION                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IN TRANSIT:                                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Protocol:     TLS 1.3                                                │ │
│  │  Cipher:       AES-256-GCM                                            │ │
│  │  Certificate:  Let's Encrypt (auto-renewed)                           │ │
│  │  HSTS:         max-age=31536000; includeSubDomains; preload          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  AT REST:                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Database:     PostgreSQL TDE (Transparent Data Encryption)           │ │
│  │  Backups:      AES-256 encrypted                                      │ │
│  │  File storage: Server-side encryption                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PII FIELDS (Application-level):                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Algorithm:    AES-256-GCM                                            │ │
│  │  Key:          Per-organization (derived from master)                 │ │
│  │  Fields:       phone, address, paymentInfo                            │ │
│  │  Searchable:   Blind index for encrypted fields                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 PII Classification

| Field | Classification | Encryption | Retention |
|-------|----------------|------------|-----------|
| Email | PII | No (needed for login) | Account lifetime |
| Phone | PII | Yes | Account lifetime |
| Password | Secret | Hash (bcrypt) | N/A (hashed) |
| Address | PII | Yes | Account lifetime |
| Payment info | PCI | External (Iyzico) | Not stored |
| IP address | PII | No | 90 days |
| Order history | Business | No | 3 years |

### 4.3 Data Masking

```
API Response Masking:

Email:      u***@example.com
Phone:      +90 5** *** ** 89
Card:       **** **** **** 1234

Logs Masking:
├── Passwords: [REDACTED]
├── Tokens: tok_xxx...xxx (truncated)
├── PII: Hashed or masked
└── Request body: Sensitive fields removed
```

---

## 5. AUDIT LOGGING

### 5.1 Audit Events

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUDIT EVENTS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AUTHENTICATION EVENTS:                                                     │
│  ├── auth.login.success                                                    │
│  ├── auth.login.failure                                                    │
│  ├── auth.logout                                                           │
│  ├── auth.token.refresh                                                    │
│  ├── auth.password.reset.request                                           │
│  ├── auth.password.reset.complete                                          │
│  ├── auth.password.change                                                  │
│  └── auth.mfa.enable/disable                                               │
│                                                                             │
│  AUTHORIZATION EVENTS:                                                      │
│  ├── authz.permission.denied                                               │
│  ├── authz.role.assigned                                                   │
│  ├── authz.role.removed                                                    │
│  └── authz.impersonation.start/end                                         │
│                                                                             │
│  DATA EVENTS:                                                               │
│  ├── data.{resource}.created                                               │
│  ├── data.{resource}.updated                                               │
│  ├── data.{resource}.deleted                                               │
│  ├── data.export.requested                                                 │
│  └── data.bulk.operation                                                   │
│                                                                             │
│  ADMIN EVENTS:                                                              │
│  ├── admin.user.created                                                    │
│  ├── admin.user.suspended                                                  │
│  ├── admin.organization.created                                            │
│  ├── admin.plan.changed                                                    │
│  ├── admin.feature.toggled                                                 │
│  └── admin.override.granted                                                │
│                                                                             │
│  SECURITY EVENTS:                                                           │
│  ├── security.rate.limited                                                 │
│  ├── security.suspicious.activity                                          │
│  ├── security.token.revoked                                                │
│  └── security.breach.detected                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Audit Log Schema

```
AuditLog:
├── id              String      PK
├── timestamp       DateTime    Event time
├── eventType       String      Event category.action
├── actorId         String?     User who performed action
├── actorType       Enum        USER | SYSTEM | API_KEY
├── actorIp         String?     IP address
├── actorUserAgent  String?     Browser/client info
├── organizationId  String?     Tenant context
├── resourceType    String?     Affected resource type
├── resourceId      String?     Affected resource ID
├── action          String      CRUD action
├── changes         Json?       Before/after diff
├── metadata        Json?       Additional context
├── status          Enum        SUCCESS | FAILURE
├── errorCode       String?     If failed
│
└── Indexes:
    ├── (organizationId, timestamp)
    ├── (actorId, timestamp)
    ├── (resourceType, resourceId)
    └── (eventType, timestamp)
```

### 5.3 Audit Retention

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Security events | 2 years | Hot (database) |
| Auth events | 1 year | Hot → Cold |
| Data events | 1 year | Hot → Cold |
| Admin events | 2 years | Hot |
| Access logs | 90 days | Cold |

---

## 6. THREAT MODEL

### 6.1 OWASP Top 10 Mitigations

| Threat | Mitigation |
|--------|------------|
| **A01: Broken Access Control** | RBAC + ABAC, tenant isolation, ownership checks |
| **A02: Cryptographic Failures** | TLS 1.3, AES-256, bcrypt, secure key management |
| **A03: Injection** | Prisma ORM (parameterized), Zod validation |
| **A04: Insecure Design** | Threat modeling, security reviews |
| **A05: Security Misconfiguration** | Helmet.js, secure defaults, env validation |
| **A06: Vulnerable Components** | Dependabot, npm audit, Snyk scanning |
| **A07: Auth Failures** | JWT best practices, rate limiting, MFA |
| **A08: Data Integrity** | Input validation, CSRF tokens, SRI |
| **A09: Logging Failures** | Comprehensive audit, monitoring, alerting |
| **A10: SSRF** | URL validation, allowlist, network isolation |

### 6.2 Attack Surface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ATTACK SURFACE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  EXTERNAL ENTRY POINTS:                                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Public API endpoints (/v1/public/*)                               │ │
│  │     Risk: Abuse, scraping, DDoS                                       │ │
│  │     Mitigation: Rate limiting, CAPTCHA, CDN                          │ │
│  │                                                                       │ │
│  │  2. Authentication endpoints (/v1/auth/*)                             │ │
│  │     Risk: Brute force, credential stuffing                           │ │
│  │     Mitigation: Rate limit, lockout, breach detection                │ │
│  │                                                                       │ │
│  │  3. File uploads (images)                                             │ │
│  │     Risk: Malware, path traversal                                     │ │
│  │     Mitigation: Type validation, scanning, isolated storage          │ │
│  │                                                                       │ │
│  │  4. Webhook endpoints                                                 │ │
│  │     Risk: Spoofing, replay attacks                                   │ │
│  │     Mitigation: Signature verification, idempotency                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  INTERNAL RISKS:                                                            │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Cross-tenant access                                               │ │
│  │     Risk: Data leakage between organizations                         │ │
│  │     Mitigation: Mandatory tenant filter, code review                 │ │
│  │                                                                       │ │
│  │  2. Privilege escalation                                              │ │
│  │     Risk: User gains higher permissions                              │ │
│  │     Mitigation: Server-side role checks, no client trust             │ │
│  │                                                                       │ │
│  │  3. Insider threat                                                    │ │
│  │     Risk: Malicious admin action                                     │ │
│  │     Mitigation: Audit logging, separation of duties                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Security Headers

```
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
```

---

## 7. INCIDENT RESPONSE

### 7.1 Incident Classification

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| P1 - Critical | Data breach, service down | 15 min | Immediate |
| P2 - High | Security vulnerability exploited | 1 hour | Same day |
| P3 - Medium | Suspicious activity, failed attacks | 4 hours | Next day |
| P4 - Low | Policy violation, minor issue | 24 hours | Weekly review |

### 7.2 Response Playbook

```
SECURITY INCIDENT PLAYBOOK:

1. DETECTION
   ├── Automated alerts (rate limit, auth failures)
   ├── User reports
   └── Log analysis

2. CONTAINMENT
   ├── Isolate affected systems
   ├── Revoke compromised tokens
   ├── Block malicious IPs
   └── Disable affected features

3. INVESTIGATION
   ├── Collect audit logs
   ├── Analyze attack vector
   ├── Identify scope of impact
   └── Document timeline

4. REMEDIATION
   ├── Patch vulnerability
   ├── Reset affected credentials
   ├── Restore from clean backup (if needed)
   └── Verify fix effectiveness

5. RECOVERY
   ├── Restore services gradually
   ├── Monitor for recurrence
   └── Communicate with affected users

6. POST-INCIDENT
   ├── Write incident report
   ├── Update threat model
   ├── Improve detection/prevention
   └── Conduct lessons learned
```

---

## 8. COMPLIANCE

### 8.1 KVKK (Turkish GDPR) Requirements

| Requirement | Implementation |
|-------------|----------------|
| Lawful basis | Consent at registration, legitimate interest |
| Data minimization | Only essential data collected |
| Purpose limitation | Defined in privacy policy |
| Storage limitation | Retention policies enforced |
| Right to access | Data export endpoint |
| Right to erasure | Account deletion flow |
| Right to portability | JSON/CSV export |
| Breach notification | 72-hour disclosure procedure |
| DPO designation | Designated contact |

### 8.2 Security Certifications (Future)

| Certification | Status | Target |
|---------------|--------|--------|
| SOC 2 Type I | Planned | Y2 |
| SOC 2 Type II | Planned | Y3 |
| ISO 27001 | Planned | Y3 |
| PCI DSS | Via Iyzico | N/A |

---

*Bu döküman, E-Menum güvenlik modelini tanımlar. Tüm implementasyonlar bu güvenlik gereksinimlerini karşılamalıdır.*
