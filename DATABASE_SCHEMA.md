# E-Menum Database Schema Design

> **Auto-Claude Database Document**  
> Entity relationships, multi-tenancy model, indexing strategy, migration policy.  
> Son Güncelleme: 2026-01-31

---

## 1. DATABASE OVERVIEW

### 1.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| RDBMS | PostgreSQL | 15+ |
| ORM | Prisma | 6.x |
| Schema | Multi-file (merged) | - |
| Migrations | Prisma Migrate | - |

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| Multi-tenancy | Shared schema, `organizationId` column |
| Soft delete | `deletedAt` timestamp on all tables |
| Audit trail | `createdAt`, `updatedAt`, `createdBy`, `updatedBy` |
| UUID primary keys | CUID2 format (collision-resistant) |
| Normalized | 3NF with strategic denormalization |

---

## 2. ENTITY RELATIONSHIP MODEL

### 2.1 Core Domain Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CORE DOMAIN MODEL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PLATFORM LEVEL (Tenant-Independent)                                        │
│  ═══════════════════════════════════                                        │
│                                                                             │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐           │
│  │    Plan     │────────►│  Feature    │◄────────│FeatureFlag │           │
│  │             │   M:N   │             │         │             │           │
│  └─────────────┘         └─────────────┘         └─────────────┘           │
│        │                                                                    │
│        │ 1:N                                                                │
│        ▼                                                                    │
│  ┌─────────────┐                                                            │
│  │Subscription │                                                            │
│  └──────┬──────┘                                                            │
│         │                                                                   │
│         │ 1:1                                                               │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       ORGANIZATION (TENANT)                         │   │
│  │  • id (PK)                                                         │   │
│  │  • name, slug                                                      │   │
│  │  • settings (JSON)                                                 │   │
│  └─────────────────────────────────────┬───────────────────────────────┘   │
│                                        │                                    │
│  ORGANIZATION LEVEL (Tenant-Scoped)    │                                    │
│  ══════════════════════════════════    │                                    │
│                                        │                                    │
│         ┌──────────────────────────────┼──────────────────────────────┐    │
│         │                              │                              │    │
│         ▼                              ▼                              ▼    │
│  ┌─────────────┐              ┌─────────────┐              ┌─────────────┐ │
│  │    User     │              │    Menu     │              │   Table     │ │
│  │             │              │             │              │             │ │
│  └──────┬──────┘              └──────┬──────┘              └──────┬──────┘ │
│         │                            │                            │        │
│         │                            │ 1:N                        │        │
│         │                            ▼                            │        │
│         │                     ┌─────────────┐                     │        │
│         │                     │  Category   │                     │        │
│         │                     │             │                     │        │
│         │                     └──────┬──────┘                     │        │
│         │                            │                            │        │
│         │                            │ 1:N                        │        │
│         │                            ▼                            │        │
│         │                     ┌─────────────┐                     │        │
│         │                     │   Product   │◄────────────────────┤        │
│         │                     │             │     (orders)        │        │
│         │                     └──────┬──────┘                     │        │
│         │                            │                            │        │
│         │              ┌─────────────┼─────────────┐              │        │
│         │              │             │             │              │        │
│         │              ▼             ▼             ▼              │        │
│         │       ┌─────────┐   ┌─────────┐   ┌─────────┐          │        │
│         │       │ Variant │   │Modifier │   │Allergen │          │        │
│         │       └─────────┘   └─────────┘   └─────────┘          │        │
│         │                                                         │        │
│         │                     ┌─────────────┐                     │        │
│         └────────────────────►│   Order     │◄────────────────────┘        │
│              (staff)          │             │      (table)                 │
│                               └──────┬──────┘                              │
│                                      │                                     │
│                                      │ 1:N                                 │
│                                      ▼                                     │
│                               ┌─────────────┐                              │
│                               │ OrderItem   │                              │
│                               └─────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Entity Catalog

#### Platform Entities (No Tenant)

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `Plan` | Subscription plans | → Features (M:N) |
| `Feature` | Platform features | ← Plans (M:N) |
| `FeatureFlag` | Feature toggles | → Feature (1:1) |
| `SystemSetting` | Global configs | - |
| `AuditLog` | System-wide audit | → User |

#### System Entities (Tenant-Scoped)

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `Organization` | Tenant root | → Users, Menus, etc. |
| `User` | User accounts | → Organization, Roles |
| `Role` | Permission roles | → Users (M:N), Permissions (M:N) |
| `Permission` | Granular permissions | ← Roles (M:N) |
| `Subscription` | Billing subscription | → Organization, Plan |
| `Invoice` | Payment records | → Subscription |
| `Notification` | User notifications | → User |

#### Menu Entities

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `Menu` | Menu container | → Organization, Categories |
| `Category` | Product grouping | → Menu, Products |
| `Product` | Menu items | → Category, Variants, Modifiers |
| `ProductVariant` | Size/portion options | → Product |
| `ProductModifier` | Add-on options | → Product |
| `Allergen` | Allergen info | ← Products (M:N) |
| `NutritionInfo` | Nutritional data | → Product (1:1) |
| `Theme` | Menu styling | → Organization |

#### Order Entities

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `Table` | Restaurant tables | → Organization, Zone |
| `Zone` | Table groupings | → Organization |
| `QRCode` | QR code records | → Organization, Table |
| `Order` | Customer orders | → Organization, Table, Items |
| `OrderItem` | Order line items | → Order, Product |
| `ServiceRequest` | Waiter calls | → Table |

#### Customer Entities

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `Customer` | End customers | → Organization |
| `CustomerVisit` | Visit tracking | → Customer |
| `Feedback` | Customer feedback | → Customer, Order |
| `Review` | Public reviews | → Customer, Organization |
| `LoyaltyPoint` | Points ledger | → Customer |

#### Analytics Entities

| Entity | Description | Key Relations |
|--------|-------------|---------------|
| `QRScan` | Scan events | → QRCode |
| `MenuView` | View events | → Menu, Product |
| `DailySummary` | Aggregated daily | → Organization |
| `AIUsage` | AI credit usage | → Organization |

---

## 3. SCHEMA DEFINITIONS

### 3.1 Base Entity Pattern

Tüm entity'ler şu base alanları içermeli:

```
BaseEntity:
├── id              String    @id @default(cuid())
├── createdAt       DateTime  @default(now())
├── updatedAt       DateTime  @updatedAt
├── deletedAt       DateTime? (soft delete)
└── (tenant scope)  organizationId String?
```

### 3.2 Core Entities Schema

#### Organization

```
Organization:
├── id                String      PK
├── name              String      required
├── slug              String      unique, URL-safe
├── email             String      primary contact
├── phone             String?
├── logo              String?     URL
├── settings          Json        default: {}
├── status            Enum        ACTIVE | SUSPENDED | DELETED
├── planId            String?     FK → Plan
├── trialEndsAt       DateTime?
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── plan          Plan?
│   ├── subscription  Subscription?
│   ├── users         User[]
│   ├── menus         Menu[]
│   ├── tables        Table[]
│   ├── orders        Order[]
│   └── customers     Customer[]
│
└── Indexes:
    ├── slug (unique)
    └── status, deletedAt
```

#### User

```
User:
├── id                String      PK
├── email             String      unique
├── passwordHash      String
├── firstName         String
├── lastName          String
├── avatar            String?     URL
├── phone             String?
├── status            Enum        ACTIVE | INVITED | SUSPENDED
├── emailVerifiedAt   DateTime?
├── lastLoginAt       DateTime?
├── organizationId    String?     FK → Organization (null = platform user)
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── organization  Organization?
│   ├── roles         Role[]      M:N via UserRole
│   ├── sessions      Session[]
│   ├── notifications Notification[]
│   └── createdOrders Order[]     (as staff)
│
└── Indexes:
    ├── email (unique)
    ├── organizationId, status
    └── organizationId, deletedAt
```

#### Role & Permission

```
Role:
├── id                String      PK
├── name              String      unique per scope
├── displayName       String
├── description       String?
├── scope             Enum        PLATFORM | ORGANIZATION
├── isSystem          Boolean     default: false (can't delete)
├── organizationId    String?     FK (null = platform role)
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   ├── organization  Organization?
│   ├── users         User[]      M:N via UserRole
│   └── permissions   Permission[] M:N via RolePermission
│
└── Indexes:
    ├── name, scope, organizationId (unique compound)
    └── scope

Permission:
├── id                String      PK
├── resource          String      e.g., "menu", "order"
├── action            String      e.g., "view", "create"
├── scope             Enum        PLATFORM | ORGANIZATION
├── description       String?
│
├── Relations:
│   └── roles         Role[]      M:N via RolePermission
│
└── Indexes:
    └── resource, action, scope (unique compound)

UserRole (Junction):
├── userId            String      FK
├── roleId            String      FK
├── assignedAt        DateTime    @default(now())
├── assignedBy        String?     FK → User
│
└── Primary Key: (userId, roleId)

RolePermission (Junction):
├── roleId            String      FK
├── permissionId      String      FK
│
└── Primary Key: (roleId, permissionId)
```

### 3.3 Menu Entities Schema

#### Menu

```
Menu:
├── id                String      PK
├── organizationId    String      FK (required)
├── name              String
├── slug              String      unique per org
├── description       String?
├── isPublished       Boolean     default: false
├── publishedAt       DateTime?
├── isDefault         Boolean     default: false
├── themeId           String?     FK → Theme
├── settings          Json        default: {}
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── organization  Organization
│   ├── theme         Theme?
│   ├── categories    Category[]
│   └── qrCodes       QRCode[]
│
└── Indexes:
    ├── organizationId, slug (unique compound)
    ├── organizationId, isPublished
    └── organizationId, deletedAt
```

#### Category

```
Category:
├── id                String      PK
├── organizationId    String      FK
├── menuId            String      FK
├── parentId          String?     FK → Category (self-ref)
├── name              String
├── slug              String
├── description       String?
├── image             String?     URL
├── isActive          Boolean     default: true
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── organization  Organization
│   ├── menu          Menu
│   ├── parent        Category?
│   ├── children      Category[]
│   └── products      Product[]
│
└── Indexes:
    ├── menuId, slug (unique compound)
    ├── menuId, sortOrder
    ├── organizationId, deletedAt
    └── parentId
```

#### Product

```
Product:
├── id                String      PK
├── organizationId    String      FK
├── categoryId        String      FK
├── name              String
├── slug              String
├── description       String?
├── shortDescription  String?     max 100 chars
├── basePrice         Decimal     precision: 10, scale: 2
├── currency          String      default: "TRY"
├── image             String?     URL
├── gallery           String[]    array of URLs
├── isActive          Boolean     default: true
├── isAvailable       Boolean     default: true (stock)
├── isFeatured        Boolean     default: false
├── isChefRecommended Boolean     default: false
├── preparationTime   Int?        minutes
├── calories          Int?
├── spicyLevel        Int?        0-5
├── tags              String[]
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── organization  Organization
│   ├── category      Category
│   ├── variants      ProductVariant[]
│   ├── modifiers     ProductModifier[]
│   ├── allergens     Allergen[]  M:N
│   ├── nutritionInfo NutritionInfo?
│   └── orderItems    OrderItem[]
│
└── Indexes:
    ├── categoryId, slug (unique compound)
    ├── organizationId, isActive, isAvailable
    ├── organizationId, deletedAt
    └── name (full-text search)
```

#### ProductVariant

```
ProductVariant:
├── id                String      PK
├── productId         String      FK
├── name              String      e.g., "Küçük", "Büyük"
├── price             Decimal     can be different from base
├── isDefault         Boolean     default: false
├── isAvailable       Boolean     default: true
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   └── product       Product
│
└── Indexes:
    └── productId, sortOrder
```

#### ProductModifier

```
ProductModifier:
├── id                String      PK
├── productId         String      FK
├── name              String      e.g., "Ekstra Peynir"
├── price             Decimal     additional cost
├── isDefault         Boolean     default: false (pre-selected)
├── isRequired        Boolean     default: false
├── maxQuantity       Int         default: 1
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   └── product       Product
│
└── Indexes:
    └── productId, sortOrder
```

#### Allergen

```
Allergen:
├── id                String      PK
├── code              String      unique, e.g., "GLUTEN"
├── name              String
├── icon              String?
├── description       String?
│
├── Relations:
│   └── products      Product[]   M:N via ProductAllergen
│
└── Indexes:
    └── code (unique)

ProductAllergen (Junction):
├── productId         String      FK
├── allergenId        String      FK
│
└── Primary Key: (productId, allergenId)
```

### 3.4 Order Entities Schema

#### Table & Zone

```
Zone:
├── id                String      PK
├── organizationId    String      FK
├── name              String      e.g., "Bahçe", "İç Mekan"
├── color             String?     for UI
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   ├── organization  Organization
│   └── tables        Table[]
│
└── Indexes:
    └── organizationId

Table:
├── id                String      PK
├── organizationId    String      FK
├── zoneId            String?     FK
├── number            String      e.g., "A1", "Bahçe-3"
├── capacity          Int         seats
├── status            Enum        AVAILABLE | OCCUPIED | RESERVED
├── currentOrderId    String?     FK → Order
├── sortOrder         Int         default: 0
├── createdAt         DateTime
├── updatedAt         DateTime
├── deletedAt         DateTime?
│
├── Relations:
│   ├── organization  Organization
│   ├── zone          Zone?
│   ├── qrCode        QRCode?
│   ├── currentOrder  Order?
│   └── orders        Order[]
│
└── Indexes:
    ├── organizationId, number (unique compound)
    └── organizationId, status
```

#### QRCode

```
QRCode:
├── id                String      PK
├── organizationId    String      FK
├── menuId            String      FK
├── tableId           String?     FK
├── code              String      unique, short code
├── type              Enum        MENU | TABLE | CAMPAIGN
├── url               String      full URL
├── imageUrl          String?     generated QR image
├── scansCount        Int         default: 0
├── isActive          Boolean     default: true
├── expiresAt         DateTime?
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   ├── organization  Organization
│   ├── menu          Menu
│   ├── table         Table?
│   └── scans         QRScan[]
│
└── Indexes:
    ├── code (unique)
    ├── organizationId
    └── tableId
```

#### Order

```
Order:
├── id                String      PK
├── organizationId    String      FK
├── orderNumber       String      unique per org, sequential
├── tableId           String?     FK
├── customerId        String?     FK
├── staffId           String?     FK → User (who took order)
├── status            Enum        PENDING | CONFIRMED | PREPARING | 
│                                 READY | DELIVERED | COMPLETED | CANCELLED
├── type              Enum        DINE_IN | TAKEAWAY | DELIVERY
├── subtotal          Decimal
├── taxAmount         Decimal
├── discountAmount    Decimal     default: 0
├── totalAmount       Decimal
├── currency          String      default: "TRY"
├── notes             String?
├── confirmedAt       DateTime?
├── preparedAt        DateTime?
├── deliveredAt       DateTime?
├── completedAt       DateTime?
├── cancelledAt       DateTime?
├── cancelReason      String?
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   ├── organization  Organization
│   ├── table         Table?
│   ├── customer      Customer?
│   ├── staff         User?
│   ├── items         OrderItem[]
│   └── feedback      Feedback?
│
└── Indexes:
    ├── organizationId, orderNumber (unique compound)
    ├── organizationId, status
    ├── organizationId, createdAt
    ├── tableId, status
    └── customerId
```

#### OrderItem

```
OrderItem:
├── id                String      PK
├── orderId           String      FK
├── productId         String      FK
├── variantId         String?     FK
├── productName       String      snapshot at order time
├── variantName       String?     snapshot
├── quantity          Int
├── unitPrice         Decimal     snapshot
├── totalPrice        Decimal     computed
├── modifiers         Json        selected modifiers snapshot
├── notes             String?     special instructions
├── status            Enum        PENDING | PREPARING | READY | SERVED
├── createdAt         DateTime
├── updatedAt         DateTime
│
├── Relations:
│   ├── order         Order
│   ├── product       Product
│   └── variant       ProductVariant?
│
└── Indexes:
    ├── orderId
    └── productId
```

---

## 4. MULTI-TENANCY MODEL

### 4.1 Isolation Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MULTI-TENANCY STRATEGY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SHARED DATABASE, SHARED SCHEMA                                             │
│  ═══════════════════════════════                                            │
│                                                                             │
│  Every tenant-scoped table has: organizationId String FK                    │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                         QUERY PATTERN                              │    │
│  │                                                                    │    │
│  │  // MIDDLEWARE sets context                                       │    │
│  │  req.organization = { id: 'org_xxx', ... }                       │    │
│  │                                                                    │    │
│  │  // ALL queries must include tenant filter                        │    │
│  │  prisma.menu.findMany({                                          │    │
│  │    where: {                                                       │    │
│  │      organizationId: req.organization.id,  // MANDATORY           │    │
│  │      deletedAt: null,                      // Soft delete        │    │
│  │      ...otherFilters                                              │    │
│  │    }                                                              │    │
│  │  })                                                               │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ENFORCEMENT LAYERS:                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  1. Middleware: Sets req.organization from JWT                    │    │
│  │  2. BaseService: Adds organizationId to all queries              │    │
│  │  3. Prisma Extension: (optional) Auto-filter                     │    │
│  │  4. Row-Level Security: PostgreSQL RLS (future)                  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  CROSS-TENANT PREVENTION:                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  ❌ NEVER: prisma.menu.findMany() // No tenant filter!           │    │
│  │  ❌ NEVER: prisma.menu.findUnique({ where: { id } }) // ID leak  │    │
│  │                                                                    │    │
│  │  ✅ ALWAYS: Include organizationId in WHERE                       │    │
│  │  ✅ ALWAYS: Verify ownership before update/delete                 │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Tenant Resolution Flow

```
Request → JWT Decode → User Load → Organization Load → Set Context

Context Available:
├── req.user         Current authenticated user
├── req.organization Current tenant (organization)
├── req.ability      CASL ability instance
└── req.plan         Current subscription plan
```

---

## 5. INDEXING STRATEGY

### 5.1 Index Categories

| Category | Purpose | Example |
|----------|---------|---------|
| Primary Key | Row identification | `id` (auto) |
| Unique | Constraint + lookup | `email`, `slug` |
| Foreign Key | Join performance | `organizationId` |
| Filter | WHERE clause optimization | `status`, `isActive` |
| Compound | Multi-column queries | `(orgId, slug)` |
| Partial | Conditional index | `WHERE deletedAt IS NULL` |
| Full-text | Search | `name`, `description` |

### 5.2 Critical Indexes

```
HIGH-PRIORITY INDEXES:
═════════════════════

Organization:
├── PK: id
├── UNIQUE: slug
└── INDEX: status, deletedAt

User:
├── PK: id
├── UNIQUE: email
└── INDEX: (organizationId, status, deletedAt)

Menu:
├── PK: id
├── UNIQUE: (organizationId, slug)
├── INDEX: (organizationId, isPublished)
└── INDEX: (organizationId, deletedAt)

Product:
├── PK: id
├── UNIQUE: (categoryId, slug)
├── INDEX: (organizationId, isActive, isAvailable)
├── INDEX: (organizationId, deletedAt)
└── GIN: name (full-text, tsvector)

Order:
├── PK: id
├── UNIQUE: (organizationId, orderNumber)
├── INDEX: (organizationId, status, createdAt)
├── INDEX: (tableId, status)
└── INDEX: (customerId, createdAt)

QRCode:
├── PK: id
├── UNIQUE: code
└── INDEX: (organizationId, isActive)

QRScan:
├── PK: id
├── INDEX: (qrCodeId, scannedAt)
└── INDEX: (organizationId, scannedAt)
```

### 5.3 Index Naming Convention

```
Format: idx_{table}_{columns}_{type?}

Examples:
├── idx_user_email_unique
├── idx_user_org_status
├── idx_product_name_gin
└── idx_order_org_status_created
```

---

## 6. MIGRATION POLICY

### 6.1 Migration Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MIGRATION WORKFLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEVELOPMENT:                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  1. Edit schema file(s) in prisma/schema/                         │    │
│  │  2. Run: npm run schema:merge                                     │    │
│  │  3. Run: npm run prisma:migrate -- --name descriptive_name       │    │
│  │  4. Review generated SQL in migrations/                           │    │
│  │  5. Commit migration files                                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  STAGING:                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  1. Pull latest migrations                                        │    │
│  │  2. Run: npm run prisma:deploy                                    │    │
│  │  3. Verify data integrity                                         │    │
│  │  4. Test affected features                                        │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  PRODUCTION:                                                                │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  1. Backup database                                               │    │
│  │  2. Run: npm run prisma:deploy                                    │    │
│  │  3. Monitor for errors                                            │    │
│  │  4. Rollback plan ready                                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Zero-Downtime Migration Rules

| Rule | Implementation |
|------|----------------|
| Additive first | Add column → backfill → make required |
| No column rename | Add new → migrate data → deprecate old |
| No type change | Same as rename strategy |
| Index async | CREATE INDEX CONCURRENTLY |
| Small batches | Backfill in chunks (1000 rows) |

### 6.3 Migration Naming Convention

```
Format: YYYYMMDDHHMMSS_descriptive_name.sql

Examples:
├── 20260131100000_create_organization_table
├── 20260131110000_add_menu_slug_column
├── 20260131120000_create_product_name_index
└── 20260131130000_add_order_status_enum_value
```

---

## 7. DATA RETENTION & ARCHIVAL

### 7.1 Retention Policy

| Data Type | Retention | Action |
|-----------|-----------|--------|
| Active records | Indefinite | Keep |
| Soft-deleted | 90 days | Archive then purge |
| Audit logs | 2 years | Archive to cold storage |
| Analytics (raw) | 6 months | Aggregate then purge |
| Analytics (aggregated) | 3 years | Keep |
| Session data | 30 days | Purge |

### 7.2 GDPR/KVKK Compliance

```
DATA SUBJECT RIGHTS:
═══════════════════

Right to Access:
├── Export endpoint: GET /api/v1/me/data-export
└── Format: JSON archive

Right to Erasure:
├── Request endpoint: POST /api/v1/me/deletion-request
├── Verification: Email confirmation
├── Processing: 30-day window
└── Action: Anonymize PII, keep aggregated data

Data Portability:
├── Format: JSON, CSV
└── Includes: Profile, orders, preferences
```

---

## 8. PERFORMANCE GUIDELINES

### 8.1 Query Optimization Rules

| Rule | Explanation |
|------|-------------|
| Select specific columns | Avoid `SELECT *` |
| Paginate large results | Max 100 per page |
| Use indexes | Check EXPLAIN ANALYZE |
| Batch operations | Use `createMany`, `updateMany` |
| Avoid N+1 | Use `include` for relations |
| Cache hot data | Redis for frequently accessed |

### 8.2 Connection Pooling

```
Prisma Connection Pool:
├── Development: 5 connections
├── Staging: 10 connections
└── Production: 20 connections (adjust based on load)

Formula: connections = (cpu_cores * 2) + effective_spindle_count
```

---

## 9. SCHEMA FILE ORGANIZATION

### 9.1 Multi-File Structure

```
prisma/
├── schema/
│   ├── base.prisma           # Datasource, generator, enums
│   ├── core.prisma           # Organization, User, Role, Permission
│   ├── menu.prisma           # Menu, Category, Product, etc.
│   ├── order.prisma          # Table, Order, OrderItem
│   ├── customer.prisma       # Customer, Feedback, Loyalty
│   ├── billing.prisma        # Plan, Subscription, Invoice
│   ├── analytics.prisma      # QRScan, MenuView, Summary
│   └── ai.prisma             # AIUsage, AIGeneration
├── schema.prisma             # Merged output (auto-generated)
├── migrations/
└── seed.ts
```

### 9.2 Schema Merge Script

```
npm run schema:merge

Action:
1. Read all .prisma files from prisma/schema/
2. Concatenate in alphabetical order
3. Write to prisma/schema.prisma
4. Run prisma format
```

---

*Bu döküman, E-Menum veritabanı tasarımını tanımlar. Tüm entity değişiklikleri bu dökümanla tutarlı olmalıdır.*
