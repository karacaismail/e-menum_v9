# E-Menum Business Rules

> **Auto-Claude Business Rules Document**  
> Domain logic, pricing rules, plan restrictions, validation, workflows.  
> Son Güncelleme: 2026-01-31

---

## 1. DOMAIN MODEL RULES

### 1.1 Core Entity Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ORGANIZATION (TENANT) RULES                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CREATION:                                                                  │
│  ├── Organization slug must be unique globally                             │
│  ├── Slug format: lowercase alphanumeric + hyphens, 3-50 chars            │
│  ├── Reserved slugs: admin, api, www, app, help, support, billing          │
│  ├── Default plan: Free (auto-assigned)                                    │
│  └── Must have at least one owner                                          │
│                                                                             │
│  OWNERSHIP:                                                                 │
│  ├── Organization must always have exactly ONE owner                       │
│  ├── Owner can transfer ownership to another user                          │
│  ├── Owner transfer requires confirmation from both parties                │
│  └── Cannot delete owner without transferring first                        │
│                                                                             │
│  DELETION:                                                                  │
│  ├── Soft delete only (set deletedAt)                                     │
│  ├── 30-day grace period for recovery                                      │
│  ├── After 30 days: anonymize PII, keep aggregated data                   │
│  ├── Active subscription must be cancelled first                           │
│  └── All users notified via email                                          │
│                                                                             │
│  STATUS TRANSITIONS:                                                        │
│  ├── ACTIVE → SUSPENDED (manual or payment failure)                       │
│  ├── SUSPENDED → ACTIVE (payment resolved)                                │
│  ├── ACTIVE → DELETED (owner request)                                     │
│  └── DELETED → ACTIVE (within 30 days, admin only)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER RULES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REGISTRATION:                                                              │
│  ├── Email must be unique across entire platform                           │
│  ├── Password minimum: 8 chars, 1 upper, 1 lower, 1 number                │
│  ├── Email verification required within 7 days                             │
│  └── Unverified accounts auto-deleted after 7 days                         │
│                                                                             │
│  ORGANIZATION MEMBERSHIP:                                                   │
│  ├── User can belong to multiple organizations                             │
│  ├── User has exactly one role per organization                            │
│  ├── Platform users (super_admin, admin, etc.) have no org                │
│  └── User context (current org) set at login/switch                        │
│                                                                             │
│  INVITATION:                                                                │
│  ├── Invitation expires in 7 days                                          │
│  ├── Max 3 resends per invitation                                          │
│  ├── Invited email cannot be changed after send                            │
│  └── Pending invitations count towards user limit                          │
│                                                                             │
│  DEACTIVATION:                                                              │
│  ├── Owner cannot deactivate themselves                                    │
│  ├── Deactivated users lose access immediately                             │
│  ├── Deactivated users can be reactivated                                  │
│  └── Data created by user retained                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MENU RULES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CREATION:                                                                  │
│  ├── Menu slug unique within organization                                  │
│  ├── At least one menu required to use QR codes                            │
│  ├── Default menu auto-created with organization                           │
│  └── Menu must have at least one category to publish                       │
│                                                                             │
│  PUBLISHING:                                                                │
│  ├── Menu must have at least 1 category with 1 product                    │
│  ├── All products must have valid prices > 0                               │
│  ├── Publishing sets publishedAt timestamp                                 │
│  ├── Unpublishing removes from public view instantly                       │
│  └── QR codes remain valid but show "menu unavailable"                     │
│                                                                             │
│  DEFAULT MENU:                                                              │
│  ├── Exactly one menu can be default per organization                      │
│  ├── Default menu shown when QR has no specific menu                       │
│  ├── Setting new default unsets previous default                           │
│  └── Cannot delete default menu (must reassign first)                      │
│                                                                             │
│  DELETION:                                                                  │
│  ├── Soft delete only                                                      │
│  ├── Cannot delete if only remaining menu                                  │
│  ├── Cannot delete default menu                                            │
│  ├── Linked QR codes become orphaned (show generic message)               │
│  └── Orders retain menu info snapshot                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRODUCT RULES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRICING:                                                                   │
│  ├── Base price must be > 0                                                │
│  ├── Price precision: 2 decimal places                                     │
│  ├── Currency: per-organization setting (default: TRY)                     │
│  └── Price can be 0 only for "on request" items (special flag)            │
│                                                                             │
│  AVAILABILITY:                                                              │
│  ├── isActive: Product exists in menu (admin toggle)                      │
│  ├── isAvailable: Product in stock (operational toggle)                   │
│  ├── Unavailable products shown grayed with "Tükendi"                     │
│  └── Inactive products not shown to customers                              │
│                                                                             │
│  VARIANTS:                                                                  │
│  ├── Variants have independent prices                                      │
│  ├── At least one variant must be available if variants exist             │
│  ├── Default variant shown first in selection                              │
│  └── Variant names unique within product                                   │
│                                                                             │
│  MODIFIERS:                                                                 │
│  ├── Modifiers add to base/variant price                                  │
│  ├── Required modifiers must be selected before add-to-cart              │
│  ├── Max quantity per modifier type configurable                          │
│  └── Modifier groups can be exclusive (radio) or multiple (checkbox)      │
│                                                                             │
│  ALLERGENS:                                                                 │
│  ├── Standard allergen list (EU 14 allergens)                             │
│  ├── Custom allergens can be added                                         │
│  ├── Allergen display mandatory if any exist                              │
│  └── "May contain" vs "Contains" distinction                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORDER RULES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CREATION:                                                                  │
│  ├── Order number: ORD-{YYYYMMDD}-{sequential}                            │
│  ├── Sequential counter resets daily per organization                      │
│  ├── Minimum order amount: configurable per org (default: none)           │
│  └── Cart must have at least 1 item                                        │
│                                                                             │
│  PRICING AT ORDER TIME:                                                     │
│  ├── Prices SNAPSHOT at order creation (stored in OrderItem)              │
│  ├── Menu price changes don't affect existing orders                       │
│  ├── Discounts calculated and stored at order time                        │
│  └── Tax calculated based on org settings                                  │
│                                                                             │
│  STATUS WORKFLOW:                                                           │
│                                                                             │
│     PENDING → CONFIRMED → PREPARING → READY → DELIVERED → COMPLETED        │
│        │          │           │         │          │                       │
│        └──────────┴───────────┴─────────┴──────────┴──→ CANCELLED         │
│                                                                             │
│  Status Rules:                                                              │
│  ├── PENDING: Awaiting restaurant confirmation                            │
│  ├── CONFIRMED: Restaurant accepted, payment confirmed (if applicable)    │
│  ├── PREPARING: Kitchen started preparation                               │
│  ├── READY: Ready for pickup/delivery                                     │
│  ├── DELIVERED: Handed to customer                                        │
│  ├── COMPLETED: Transaction complete                                      │
│  └── CANCELLED: Only from PENDING/CONFIRMED states                        │
│                                                                             │
│  CANCELLATION:                                                              │
│  ├── Customer can cancel: PENDING only                                    │
│  ├── Staff can cancel: PENDING, CONFIRMED                                 │
│  ├── Manager can cancel: up to PREPARING (with reason)                    │
│  ├── Cancellation reason required                                          │
│  └── Cancelled orders excluded from reports (optional filter)             │
│                                                                             │
│  MODIFICATION:                                                              │
│  ├── Items can be added: PENDING, CONFIRMED only                          │
│  ├── Items can be removed: PENDING only                                   │
│  ├── All modifications logged                                              │
│  └── Price recalculated on modification                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. PRICING & BILLING RULES

### 2.1 Subscription Plans

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUBSCRIPTION PLANS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLAN HIERARCHY:                                                            │
│                                                                             │
│  Plan          │ Price/Mo │ Position │ Can Upgrade To      │ Can Downgrade │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Free          │ ₺0       │ 0        │ All                 │ -             │
│  Starter       │ ₺2,000   │ 1        │ Pro, Biz, Ent       │ Free          │
│  Professional  │ ₺4,000   │ 2        │ Biz, Ent            │ Starter, Free │
│  Business      │ ₺6,000   │ 3        │ Ent                 │ Pro, Starter  │
│  Enterprise    │ ₺8,000+  │ 4        │ -                   │ All           │
│                                                                             │
│  UPGRADE RULES:                                                             │
│  ├── Immediate access to new features                                      │
│  ├── Prorated billing for current period                                   │
│  ├── Limits increased immediately                                          │
│  └── No refund for unused portion of lower plan                           │
│                                                                             │
│  DOWNGRADE RULES:                                                           │
│  ├── Takes effect at end of current billing period                        │
│  ├── Must be within new plan limits before downgrade                       │
│  ├── Warning if over limits (must reduce first)                            │
│  ├── Feature access retained until period end                             │
│  └── Data retained but features locked                                     │
│                                                                             │
│  CANCELLATION RULES:                                                        │
│  ├── Can cancel anytime                                                    │
│  ├── Access continues until period end                                     │
│  ├── Downgrades to Free at period end                                     │
│  ├── No prorated refunds                                                   │
│  └── Data retained (subject to Free limits)                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Plan Limits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PLAN LIMITS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RESOURCE LIMITS:                                                           │
│                                                                             │
│  Resource        │ Free  │ Starter │ Pro    │ Business │ Enterprise       │
│  ────────────────────────────────────────────────────────────────────────  │
│  Menus           │ 1     │ 3       │ 10     │ 50       │ Unlimited        │
│  Categories/Menu │ 3     │ 10      │ 25     │ 50       │ Unlimited        │
│  Products        │ 15    │ 100     │ 500    │ 2,000    │ Unlimited        │
│  QR Codes        │ 1     │ 10      │ 50     │ 200      │ Unlimited        │
│  Users           │ 1     │ 3       │ 10     │ 25       │ Unlimited        │
│  Branches        │ 0     │ 0       │ 1      │ 3        │ Unlimited        │
│  Storage (MB)    │ 50    │ 500     │ 2,000  │ 10,000   │ Unlimited        │
│                                                                             │
│  MONTHLY LIMITS:                                                            │
│                                                                             │
│  Metric          │ Free  │ Starter │ Pro    │ Business │ Enterprise       │
│  ────────────────────────────────────────────────────────────────────────  │
│  QR Scans        │ 100   │ 5,000   │ 25,000 │ 100,000  │ Unlimited        │
│  Orders          │ 0     │ 500     │ 2,500  │ 10,000   │ Unlimited        │
│  AI Credits      │ 0     │ 500     │ 2,000  │ 5,000    │ 10,000+          │
│  API Requests    │ 0     │ 0       │ 10,000 │ 50,000   │ Unlimited        │
│  Export/Reports  │ 0     │ 5       │ 20     │ 100      │ Unlimited        │
│                                                                             │
│  LIMIT ENFORCEMENT:                                                         │
│  ├── Soft limit: Warning at 80%                                           │
│  ├── Hard limit: Block new creation at 100%                               │
│  ├── Existing data never deleted for limit violation                      │
│  ├── Monthly limits reset on billing date                                 │
│  └── Overage charges: Enterprise only (configurable)                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Feature Gating

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FEATURE AVAILABILITY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE FEATURES:                                                             │
│                                                                             │
│  Feature              │ Free │ Starter │ Pro │ Business │ Enterprise       │
│  ──────────────────────────────────────────────────────────────────────────│
│  Digital Menu         │ ✓    │ ✓       │ ✓   │ ✓        │ ✓               │
│  QR Code Generation   │ ✓    │ ✓       │ ✓   │ ✓        │ ✓               │
│  Basic Analytics      │ -    │ ✓       │ ✓   │ ✓        │ ✓               │
│  E-Menum Watermark    │ ✓    │ -       │ -   │ -        │ -               │
│  Custom Domain        │ -    │ -       │ -   │ ✓        │ ✓               │
│  White Label          │ -    │ -       │ -   │ -        │ ✓               │
│                                                                             │
│  ORDER FEATURES:                                                            │
│                                                                             │
│  Feature              │ Free │ Starter │ Pro │ Business │ Enterprise       │
│  ──────────────────────────────────────────────────────────────────────────│
│  Order Receiving      │ -    │ ✓       │ ✓   │ ✓        │ ✓               │
│  Kitchen Display      │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Waiter App           │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Table Management     │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Service Requests     │ -    │ ✓       │ ✓   │ ✓        │ ✓               │
│                                                                             │
│  AI FEATURES:                                                               │
│                                                                             │
│  Feature              │ Free │ Starter │ Pro │ Business │ Enterprise       │
│  ──────────────────────────────────────────────────────────────────────────│
│  AI Content Gen       │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  AI Image Gen         │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  AI Translation       │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  AI Insights          │ -    │ -       │ -   │ ✓        │ ✓               │
│  AI Forecasting       │ -    │ -       │ -   │ ✓        │ ✓               │
│  AI Natural Query     │ -    │ -       │ -   │ ✓        │ ✓               │
│                                                                             │
│  ADVANCED FEATURES:                                                         │
│                                                                             │
│  Feature              │ Free │ Starter │ Pro │ Business │ Enterprise       │
│  ──────────────────────────────────────────────────────────────────────────│
│  Multi-Branch         │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Central Menu Mgmt    │ -    │ -       │ -   │ ✓        │ ✓               │
│  Campaigns            │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Loyalty Program      │ -    │ -       │ -   │ ✓        │ ✓               │
│  API Access           │ -    │ -       │ ✓   │ ✓        │ ✓               │
│  Webhooks             │ -    │ -       │ -   │ ✓        │ ✓               │
│  Custom Integrations  │ -    │ -       │ -   │ -        │ ✓               │
│  Priority Support     │ -    │ -       │ -   │ ✓        │ ✓               │
│  Dedicated Account    │ -    │ -       │ -   │ -        │ ✓               │
│  SLA Guarantee        │ -    │ -       │ -   │ -        │ ✓               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.4 AI Credit Consumption

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI CREDIT SYSTEM                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CREDIT COSTS:                                                              │
│                                                                             │
│  Operation                    │ Credits │ Model Used                       │
│  ────────────────────────────────────────────────────────────────────────  │
│  Product Description (short)  │ 1       │ Claude Haiku                     │
│  Product Description (long)   │ 2       │ Claude Haiku                     │
│  Menu Translation (per item)  │ 1       │ Claude Haiku                     │
│  Content Improvement          │ 2       │ Claude Sonnet                    │
│  SEO Optimization             │ 3       │ Claude Sonnet                    │
│  Stock Photo Search           │ 0       │ Unsplash API                     │
│  AI Image Generation (basic)  │ 10      │ DALL-E 3                         │
│  AI Image Generation (HD)     │ 15      │ DALL-E 3 HD                      │
│  Natural Language Query       │ 2       │ Claude Haiku                     │
│  Analytics Insight            │ 3       │ Claude Sonnet                    │
│  Demand Forecast              │ 5       │ Prophet + Claude                 │
│  Anomaly Detection            │ 3       │ ML Model                         │
│  Chatbot Response             │ 1       │ Claude Haiku                     │
│                                                                             │
│  CREDIT MANAGEMENT:                                                         │
│  ├── Credits reset monthly on billing date                                 │
│  ├── Unused credits do NOT roll over                                       │
│  ├── Real-time balance check before operation                              │
│  ├── Operation fails gracefully if insufficient                            │
│  ├── Credit purchase: Enterprise can buy additional                        │
│  └── Fair use policy: Automated abuse detection                           │
│                                                                             │
│  CACHING & OPTIMIZATION:                                                    │
│  ├── Identical requests cached (24h TTL)                                   │
│  ├── Cached responses don't consume credits                                │
│  ├── Cache key: hash(prompt + parameters)                                  │
│  └── User notified if cached response used                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. VALIDATION RULES

### 3.1 Input Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INPUT VALIDATION RULES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STRING FIELDS:                                                             │
│                                                                             │
│  Field              │ Min │ Max  │ Pattern           │ Trim │ Required     │
│  ──────────────────────────────────────────────────────────────────────────│
│  name (menu)        │ 1   │ 100  │ -                 │ Yes  │ Yes          │
│  name (product)     │ 1   │ 150  │ -                 │ Yes  │ Yes          │
│  slug               │ 3   │ 50   │ ^[a-z0-9-]+$      │ Yes  │ Auto-gen     │
│  description        │ 0   │ 2000 │ -                 │ Yes  │ No           │
│  shortDescription   │ 0   │ 100  │ -                 │ Yes  │ No           │
│  email              │ 5   │ 255  │ RFC 5322          │ Yes  │ Contextual   │
│  phone              │ 10  │ 15   │ ^\\+?[0-9]+$      │ Yes  │ No           │
│  password           │ 8   │ 128  │ Complexity rules  │ No   │ Yes          │
│                                                                             │
│  NUMERIC FIELDS:                                                            │
│                                                                             │
│  Field              │ Min   │ Max        │ Precision │ Required            │
│  ──────────────────────────────────────────────────────────────────────────│
│  price              │ 0.01  │ 999,999.99 │ 2         │ Yes                 │
│  quantity           │ 1     │ 999        │ 0         │ Yes                 │
│  sortOrder          │ 0     │ 9999       │ 0         │ No (default: 0)     │
│  calories           │ 0     │ 99999      │ 0         │ No                  │
│  preparationTime    │ 1     │ 180        │ 0         │ No                  │
│  spicyLevel         │ 0     │ 5          │ 0         │ No                  │
│  capacity (table)   │ 1     │ 50         │ 0         │ Yes                 │
│                                                                             │
│  ARRAY FIELDS:                                                              │
│                                                                             │
│  Field              │ Min Items │ Max Items │ Item Validation              │
│  ──────────────────────────────────────────────────────────────────────────│
│  tags               │ 0         │ 10        │ String, 1-30 chars           │
│  gallery            │ 0         │ 10        │ Valid URL                    │
│  allergens          │ 0         │ 14        │ Valid allergen ID            │
│                                                                             │
│  FILE UPLOADS:                                                              │
│                                                                             │
│  Type               │ Max Size │ Allowed Formats    │ Dimensions           │
│  ──────────────────────────────────────────────────────────────────────────│
│  Product image      │ 5 MB     │ jpg, png, webp     │ Min 400x400          │
│  Logo               │ 2 MB     │ jpg, png, svg      │ Recommended 200x200  │
│  Menu background    │ 10 MB    │ jpg, png           │ Min 1920x1080        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Business Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BUSINESS VALIDATION RULES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MENU PUBLISHING VALIDATION:                                                │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Can only publish if:                                                │ │
│  │  ├── At least 1 active category exists                              │ │
│  │  ├── At least 1 active product in at least 1 category               │ │
│  │  ├── All products have valid prices (> 0)                           │ │
│  │  ├── All required product fields filled                             │ │
│  │  └── Organization subscription is active                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ORDER VALIDATION:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Can only create order if:                                           │ │
│  │  ├── All products are available (isAvailable = true)                │ │
│  │  ├── All selected variants exist and available                       │ │
│  │  ├── All required modifiers selected                                │ │
│  │  ├── Quantities are positive integers                               │ │
│  │  ├── Table number valid (if dine-in)                                │ │
│  │  └── Organization has order feature (plan check)                    │ │
│  │                                                                       │ │
│  │  Recalculate on submission:                                          │ │
│  │  ├── Fetch current prices from database                             │ │
│  │  ├── Validate availability again                                     │ │
│  │  └── Reject if discrepancy > 5% (price changed significantly)       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CAMPAIGN VALIDATION:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Campaign rules:                                                     │ │
│  │  ├── Start date must be in future or now                            │ │
│  │  ├── End date must be after start date                              │ │
│  │  ├── Discount percentage: 1-100%                                    │ │
│  │  ├── Fixed discount: must be less than min order amount             │ │
│  │  ├── Cannot overlap with same-type campaign                         │ │
│  │  └── Product-specific campaigns: product must exist                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  USER ROLE VALIDATION:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Role assignment rules:                                              │ │
│  │  ├── Cannot assign role higher than own role                        │ │
│  │  ├── Only owner can assign manager role                             │ │
│  │  ├── Cannot remove own owner role                                   │ │
│  │  ├── Platform roles only assignable by super_admin                  │ │
│  │  └── User limit check before assignment                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. WORKFLOW RULES

### 4.1 Order Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ORDER STATE MACHINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATE TRANSITIONS:                                                         │
│                                                                             │
│  From State   │ To State    │ Trigger            │ Permissions             │
│  ──────────────────────────────────────────────────────────────────────────│
│  (new)        │ PENDING     │ Customer submits   │ Public                  │
│  PENDING      │ CONFIRMED   │ Staff confirms     │ orders.update           │
│  PENDING      │ CANCELLED   │ Customer/Staff     │ orders.update           │
│  CONFIRMED    │ PREPARING   │ Kitchen starts     │ orders.update           │
│  CONFIRMED    │ CANCELLED   │ Manager            │ orders.cancel           │
│  PREPARING    │ READY       │ Kitchen completes  │ orders.update           │
│  PREPARING    │ CANCELLED   │ Manager (refund)   │ orders.cancel           │
│  READY        │ DELIVERED   │ Staff serves       │ orders.update           │
│  DELIVERED    │ COMPLETED   │ Auto (30 min)      │ System                  │
│  DELIVERED    │ COMPLETED   │ Staff confirms     │ orders.update           │
│                                                                             │
│  SIDE EFFECTS:                                                              │
│                                                                             │
│  Transition        │ Side Effects                                          │
│  ──────────────────────────────────────────────────────────────────────────│
│  → PENDING         │ Emit order.created event                              │
│                    │ Notify restaurant (push/sound)                        │
│                    │ Start auto-cancel timer (configurable)                │
│  → CONFIRMED       │ Emit order.confirmed event                            │
│                    │ Notify customer (if phone provided)                   │
│                    │ Cancel auto-cancel timer                              │
│  → PREPARING       │ Emit order.preparing event                            │
│                    │ Show in Kitchen Display                               │
│                    │ Start prep timer                                      │
│  → READY           │ Emit order.ready event                                │
│                    │ Notify customer                                        │
│                    │ Play sound on waiter app                              │
│  → DELIVERED       │ Emit order.delivered event                            │
│                    │ Start auto-complete timer (30 min)                    │
│  → COMPLETED       │ Emit order.completed event                            │
│                    │ Update analytics                                       │
│                    │ Trigger feedback request (configurable)               │
│  → CANCELLED       │ Emit order.cancelled event                            │
│                    │ Log cancellation reason                               │
│                    │ Update inventory (if applicable)                      │
│                    │ Trigger refund (if paid)                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Subscription Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUBSCRIPTION STATE MACHINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATES:                                                                    │
│  ├── TRIALING: Initial trial period                                        │
│  ├── ACTIVE: Paid and active                                               │
│  ├── PAST_DUE: Payment failed, grace period                                │
│  ├── CANCELLED: User cancelled, access until period end                    │
│  ├── EXPIRED: Period ended, downgraded to Free                             │
│  └── SUSPENDED: Admin action, access blocked                               │
│                                                                             │
│  TRANSITIONS:                                                               │
│                                                                             │
│  From         │ To          │ Trigger              │ Actions               │
│  ──────────────────────────────────────────────────────────────────────────│
│  (new)        │ TRIALING    │ Org created          │ 14-day trial starts   │
│  TRIALING     │ ACTIVE      │ Payment success      │ Trial converted       │
│  TRIALING     │ EXPIRED     │ Trial ends (no pay)  │ Downgrade to Free     │
│  ACTIVE       │ ACTIVE      │ Renewal success      │ Period extended       │
│  ACTIVE       │ PAST_DUE    │ Payment failed       │ 7-day grace period    │
│  ACTIVE       │ CANCELLED   │ User cancels         │ Access until period   │
│  PAST_DUE     │ ACTIVE      │ Payment success      │ Grace period ended    │
│  PAST_DUE     │ EXPIRED     │ Grace period ends    │ Downgrade to Free     │
│  CANCELLED    │ EXPIRED     │ Period ends          │ Downgrade to Free     │
│  CANCELLED    │ ACTIVE      │ User resubscribes    │ Immediate access      │
│  EXPIRED      │ ACTIVE      │ User resubscribes    │ Immediate access      │
│  ANY          │ SUSPENDED   │ Admin action         │ Access blocked        │
│  SUSPENDED    │ ACTIVE      │ Admin resolves       │ Access restored       │
│                                                                             │
│  DUNNING PROCESS (Payment Failure):                                         │
│  ├── Day 0: Payment fails → Status: PAST_DUE                               │
│  ├── Day 0: Email: Payment failed, update card                             │
│  ├── Day 3: Email: Reminder, card update link                              │
│  ├── Day 5: Email: Final warning, service disruption notice                │
│  ├── Day 7: Status: EXPIRED, Downgrade to Free                             │
│  └── Day 7: Email: Account downgraded, resubscribe link                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Content Moderation Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTENT MODERATION RULES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AI-GENERATED CONTENT:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Content generated by AI                                          │ │
│  │  2. Automatic safety filter applied                                  │ │
│  │  3. Content shown to user for review                                 │ │
│  │  4. User edits and approves                                          │ │
│  │  5. Content saved with ai_generated flag                             │ │
│  │                                                                       │ │
│  │  Safety filters:                                                      │ │
│  │  ├── Profanity check                                                 │ │
│  │  ├── Competitor mention check                                        │ │
│  │  ├── Medical/health claim check                                      │ │
│  │  └── Pricing accuracy check (if prices mentioned)                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  USER-UPLOADED IMAGES:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  1. Image uploaded                                                   │ │
│  │  2. Virus scan                                                       │ │
│  │  3. Image type verification (magic bytes)                            │ │
│  │  4. Resize and optimize                                              │ │
│  │  5. Optional: NSFW detection (future)                                │ │
│  │  6. Store with original preserved                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  REVIEW MODERATION:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Public reviews go through:                                          │ │
│  │  1. Automatic spam filter                                            │ │
│  │  2. Profanity filter                                                 │ │
│  │  3. Published immediately (post-moderation)                          │ │
│  │  4. Restaurant can flag for review                                   │ │
│  │  5. Admin reviews flagged content                                    │ │
│  │  6. Decision: Approve / Remove / Edit                                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. INTEGRATION RULES

### 5.1 Third-Party API Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API INTEGRATION RULES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AI PROVIDER FAILOVER:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Priority chain: Claude → GPT-4 → Gemini                             │ │
│  │                                                                       │ │
│  │  Failover triggers:                                                  │ │
│  │  ├── HTTP 429 (rate limited) → immediate switch                     │ │
│  │  ├── HTTP 5xx → retry 2x, then switch                               │ │
│  │  ├── Timeout (30s) → switch                                         │ │
│  │  └── Content filter triggered → log and switch                      │ │
│  │                                                                       │ │
│  │  Circuit breaker:                                                    │ │
│  │  ├── 5 failures in 1 minute → open circuit                          │ │
│  │  ├── 30 seconds open → half-open (allow 1 request)                  │ │
│  │  └── Success in half-open → close circuit                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PAYMENT PROVIDER RULES:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Iyzico integration:                                                 │ │
│  │  ├── All prices in minor units (kuruş)                              │ │
│  │  ├── Webhook signature verification mandatory                       │ │
│  │  ├── Idempotency key for all payment requests                       │ │
│  │  ├── Store payment reference for reconciliation                     │ │
│  │  └── PCI compliance: no card data stored locally                    │ │
│  │                                                                       │ │
│  │  Retry logic:                                                        │ │
│  │  ├── Network error → retry 3x with exponential backoff              │ │
│  │  ├── Payment declined → no retry, notify user                       │ │
│  │  └── Timeout → check payment status before retry                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  WEBHOOK RULES:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Incoming webhooks:                                                  │ │
│  │  ├── Verify signature (reject if invalid)                           │ │
│  │  ├── Check timestamp (reject if > 5 min old)                        │ │
│  │  ├── Idempotency check (ignore duplicates)                          │ │
│  │  ├── Process asynchronously (queue)                                 │ │
│  │  └── Return 200 immediately (before processing)                     │ │
│  │                                                                       │ │
│  │  Outgoing webhooks:                                                  │ │
│  │  ├── Sign with organization secret                                  │ │
│  │  ├── Retry: 3 attempts (1min, 5min, 30min)                         │ │
│  │  ├── Timeout: 10 seconds                                            │ │
│  │  ├── Log all delivery attempts                                      │ │
│  │  └── Disable webhook after 10 consecutive failures                  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Data Sync Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA SYNCHRONIZATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MULTI-BRANCH SYNC:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Central Menu → Branch Menu sync:                                    │ │
│  │  ├── Sync modes: Push (instant) / Pull (on-demand)                  │ │
│  │  ├── Conflict resolution: Central wins (by default)                 │ │
│  │  ├── Branch overrides: Price, availability only                     │ │
│  │  ├── Sync log maintained for audit                                  │ │
│  │  └── Failed syncs queued for retry                                  │ │
│  │                                                                       │ │
│  │  Syncable fields:                                                    │ │
│  │  ├── Product name, description, image ✓                             │ │
│  │  ├── Category structure ✓                                           │ │
│  │  ├── Allergens, nutrition ✓                                         │ │
│  │  ├── Base price (optional override at branch)                       │ │
│  │  └── Availability (always branch-controlled)                        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  CACHE INVALIDATION:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Invalidation triggers:                                              │ │
│  │  ├── Menu update → Invalidate menu:* keys                           │ │
│  │  ├── Product update → Invalidate product, category, menu            │ │
│  │  ├── Permission change → Invalidate user:*:permissions              │ │
│  │  ├── Plan change → Invalidate org:*:plan                            │ │
│  │  └── Settings change → Invalidate org:*:settings                    │ │
│  │                                                                       │ │
│  │  Propagation:                                                        │ │
│  │  ├── Local cache: Immediate                                         │ │
│  │  ├── Redis: Pub/sub to all instances                                │ │
│  │  └── CDN: Purge via API (if applicable)                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. REPORTING RULES

### 6.1 Analytics Calculation Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS CALCULATIONS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REVENUE METRICS:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Gross Revenue = Sum(order.totalAmount) where status = COMPLETED     │ │
│  │  Net Revenue = Gross - Refunds - Discounts                           │ │
│  │  Average Order Value = Gross Revenue / Completed Order Count         │ │
│  │  Revenue per QR Scan = Gross Revenue / QR Scan Count                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ORDER METRICS:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Order Count = Count(orders) where status IN (COMPLETED, DELIVERED)  │ │
│  │  Cancellation Rate = Cancelled / (Completed + Cancelled) × 100       │ │
│  │  Avg Preparation Time = Avg(READY.timestamp - CONFIRMED.timestamp)   │ │
│  │  Avg Wait Time = Avg(DELIVERED.timestamp - PENDING.timestamp)        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  PRODUCT METRICS:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Units Sold = Sum(orderItem.quantity) for product                    │ │
│  │  Product Revenue = Sum(orderItem.totalPrice) for product             │ │
│  │  Product Rank = Order by Units Sold DESC                             │ │
│  │  View-to-Order Rate = Orders with Product / Product Views × 100      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ENGAGEMENT METRICS:                                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  QR Scan Count = Count(qr_scans)                                     │ │
│  │  Unique Visitors = Count(DISTINCT session_id from qr_scans)          │ │
│  │  Return Rate = Visitors with >1 visit / Total Visitors × 100         │ │
│  │  Avg Session Duration = Avg(last_activity - first_scan)              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TIMEZONE HANDLING:                                                         │
│  ├── All timestamps stored in UTC                                          │
│  ├── Reports generated in organization timezone                            │
│  ├── Day boundaries based on org timezone                                  │
│  └── Aggregations run at 00:00 org timezone                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Aggregation Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA AGGREGATION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AGGREGATION SCHEDULE:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Granularity   │ Aggregation Time │ Retention │ Data Kept             │ │
│  │  ────────────────────────────────────────────────────────────────────│ │
│  │  Hourly        │ Every hour       │ 7 days    │ All metrics           │ │
│  │  Daily         │ 00:05 UTC        │ 90 days   │ All metrics           │ │
│  │  Weekly        │ Monday 00:15 UTC │ 1 year    │ Summary metrics       │ │
│  │  Monthly       │ 1st 00:30 UTC    │ 3 years   │ Summary metrics       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  RAW DATA RETENTION:                                                        │
│  ├── QR Scans: 90 days raw, then aggregated                               │
│  ├── Orders: Forever (legal requirement)                                   │
│  ├── Menu Views: 30 days raw, then aggregated                             │
│  └── API Logs: 30 days                                                     │
│                                                                             │
│  AGGREGATION RULES:                                                         │
│  ├── Failed orders excluded from revenue calculations                      │
│  ├── Test orders (flagged) excluded from all reports                       │
│  ├── Outliers handled: Cap at 99th percentile for averages                │
│  └── Zero-value periods included (no data != zero)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. AUDIT & COMPLIANCE

### 7.1 Audit Trail Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUDIT REQUIREMENTS                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MANDATORY AUDIT EVENTS:                                                    │
│  ├── All authentication events (login, logout, password change)            │
│  ├── All authorization failures (permission denied)                        │
│  ├── User management (create, update, delete, role change)                 │
│  ├── Organization settings changes                                         │
│  ├── Subscription changes                                                   │
│  ├── Data export requests                                                   │
│  ├── Data deletion requests                                                 │
│  └── Admin impersonation sessions                                          │
│                                                                             │
│  AUDIT LOG IMMUTABILITY:                                                    │
│  ├── Audit logs cannot be modified or deleted                              │
│  ├── Append-only storage                                                    │
│  ├── Integrity hash for each entry                                         │
│  └── Chain hash linking entries                                            │
│                                                                             │
│  RETENTION:                                                                 │
│  ├── Security events: 2 years                                              │
│  ├── User activity: 1 year                                                 │
│  ├── System events: 90 days                                                │
│  └── Legal hold: Indefinite (if flagged)                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 KVKK/GDPR Compliance Rules

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA PROTECTION RULES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA SUBJECT RIGHTS:                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Right              │ Implementation         │ SLA                    │ │
│  │  ────────────────────────────────────────────────────────────────────│ │
│  │  Access             │ Self-service export    │ Instant                │ │
│  │  Rectification      │ Profile edit           │ Instant                │ │
│  │  Erasure            │ Account deletion       │ 30 days                │ │
│  │  Portability        │ JSON/CSV export        │ 24 hours               │ │
│  │  Objection          │ Marketing opt-out      │ Instant                │ │
│  │  Restrict Processing│ Account suspension     │ 24 hours               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  DATA MINIMIZATION:                                                         │
│  ├── Collect only necessary data                                           │
│  ├── Default: minimal data collection                                      │
│  ├── Optional fields clearly marked                                        │
│  └── Regular data inventory audits                                         │
│                                                                             │
│  CONSENT MANAGEMENT:                                                        │
│  ├── Granular consent options                                              │
│  ├── Easy withdrawal mechanism                                             │
│  ├── Consent records maintained                                            │
│  └── Re-consent on policy changes                                          │
│                                                                             │
│  BREACH NOTIFICATION:                                                       │
│  ├── Internal detection: < 24 hours                                        │
│  ├── Authority notification: < 72 hours                                    │
│  ├── User notification: Without undue delay                                │
│  └── Documentation of all breaches                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Bu döküman, E-Menum iş kurallarını tanımlar. Tüm implementasyonlar bu kurallarla tutarlı olmalıdır.*
