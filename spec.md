# Menu Module Specification

> **Module ID:** `001-menu-module`  
> **Version:** 1.0.0  
> **Status:** Draft  
> **Priority:** P0 (Core)  
> **Estimated Effort:** 15-20 dev days  
> **Dependencies:** Auth, Organization, Media modules

---

## 1. MODÜL GENEL BAKIŞ

### 1.1 Amaç

Menu modülü, E-Menum platformunun temel iş değerini oluşturur. Restoran ve kafelerin dijital menülerini oluşturmasını, yönetmesini ve müşterilere sunmasını sağlar.

### 1.2 Kapsam

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MENU MODULE SCOPE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IN SCOPE:                                                                  │
│  ├── Menü CRUD operasyonları                                               │
│  ├── Kategori yönetimi (hiyerarşik)                                        │
│  ├── Ürün yönetimi (variants, options, modifiers)                          │
│  ├── Fiyatlandırma (multi-currency, promotions)                            │
│  ├── Görsel yönetimi (ürün fotoğrafları)                                   │
│  ├── Çoklu dil desteği (i18n)                                              │
│  ├── QR kod entegrasyonu                                                    │
│  ├── Alerjen ve besin bilgileri                                            │
│  ├── Stok durumu (availability)                                            │
│  └── Menü versiyonlama                                                      │
│                                                                             │
│  OUT OF SCOPE (Diğer modüller):                                            │
│  ├── Sipariş alma → Order Module                                           │
│  ├── Ödeme işleme → Payment Module                                         │
│  ├── Analitik → Analytics Module                                           │
│  ├── AI içerik üretimi → AI Module                                         │
│  └── Tema/tasarım → Theme Module                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Kullanıcı Rolleri

| Rol | Yetkiler |
|-----|----------|
| `owner` | Tam erişim, menü yayınlama/geri alma |
| `manager` | CRUD, fiyat değişikliği, stok yönetimi |
| `staff` | Sadece stok durumu güncelleme |
| `viewer` | Salt okunur erişim |
| `customer` | Public menü görüntüleme |

---

## 2. DATA MODEL

### 2.1 Entity Relationship

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MENU DATA MODEL                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Organization (1) ──────< (N) Menu                                         │
│       │                      │                                              │
│       │                      ├──< (N) Category                             │
│       │                      │        │                                     │
│       │                      │        └──< (N) MenuItem                    │
│       │                      │                 │                            │
│       │                      │                 ├──< (N) MenuItemVariant    │
│       │                      │                 ├──< (N) MenuItemOption     │
│       │                      │                 ├──< (N) MenuItemAllergen   │
│       │                      │                 └──< (N) MenuItemImage      │
│       │                      │                                              │
│       │                      └──< (N) MenuVersion (audit)                  │
│       │                                                                     │
│       └──────< (N) Branch ──────< (N) BranchMenu (M:N)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Core Entities

#### Menu

```typescript
interface Menu {
  id: string;                    // UUID
  organizationId: string;        // FK → Organization
  
  // Identity
  slug: string;                  // URL-friendly identifier
  name: string;                  // Internal name
  description?: string;          // Internal description
  
  // Localization
  defaultLocale: string;         // 'tr', 'en', etc.
  supportedLocales: string[];    // ['tr', 'en', 'ar']
  
  // Settings
  currency: string;              // 'TRY', 'USD', 'EUR'
  taxIncluded: boolean;          // Fiyatlara KDV dahil mi
  taxRate?: number;              // KDV oranı (%)
  
  // Status
  status: MenuStatus;            // draft | published | archived
  publishedAt?: Date;            // Son yayınlanma
  
  // Metadata
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;             // FK → User
  version: number;               // Optimistic locking
}

type MenuStatus = 'draft' | 'published' | 'archived';
```

#### Category

```typescript
interface Category {
  id: string;
  menuId: string;                // FK → Menu
  parentId?: string;             // FK → Category (self-reference)
  
  // Content (localized)
  translations: CategoryTranslation[];
  
  // Display
  icon?: string;                 // Phosphor icon name
  image?: string;                // URL
  color?: string;                // Hex color
  
  // Ordering
  sortOrder: number;             // Display sırası
  
  // Settings
  isActive: boolean;             // Görünür/gizli
  scheduledVisibility?: {        // Zamanlı görünürlük
    startTime?: string;          // "11:00"
    endTime?: string;            // "14:00"
    days?: number[];             // [1,2,3,4,5] (Mon-Fri)
  };
  
  createdAt: Date;
  updatedAt: Date;
}

interface CategoryTranslation {
  locale: string;                // 'tr', 'en'
  name: string;                  // Kategori adı
  description?: string;          // Açıklama
}
```

#### MenuItem

```typescript
interface MenuItem {
  id: string;
  menuId: string;                // FK → Menu
  categoryId: string;            // FK → Category
  
  // Identity
  sku?: string;                  // Stock Keeping Unit
  
  // Content (localized)
  translations: MenuItemTranslation[];
  
  // Pricing
  basePrice: number;             // Temel fiyat (kuruş/cent)
  compareAtPrice?: number;       // İndirimli gösterim için eski fiyat
  costPrice?: number;            // Maliyet (internal)
  
  // Variants & Options
  hasVariants: boolean;          // Varyant var mı (S/M/L)
  variants?: MenuItemVariant[];
  optionGroups?: OptionGroup[];  // Ekstra seçenekler
  
  // Dietary & Allergens
  allergens: AllergenType[];     // ['gluten', 'dairy', 'nuts']
  dietaryFlags: DietaryFlag[];   // ['vegetarian', 'vegan', 'halal']
  
  // Nutrition (optional)
  nutrition?: NutritionInfo;
  
  // Display
  images: MenuItemImage[];
  sortOrder: number;
  isFeatured: boolean;           // Öne çıkan
  isNew: boolean;                // Yeni ürün badge
  
  // Availability
  isActive: boolean;
  stockStatus: StockStatus;      // in_stock | low_stock | out_of_stock
  availableFrom?: Date;          // Lansman tarihi
  availableUntil?: Date;         // Bitiş tarihi
  
  // Preparation
  preparationTime?: number;      // Dakika
  
  createdAt: Date;
  updatedAt: Date;
}

interface MenuItemTranslation {
  locale: string;
  name: string;                  // Ürün adı
  description?: string;          // Açıklama
  shortDescription?: string;     // Kısa açıklama (liste için)
}

type AllergenType = 
  | 'gluten' | 'dairy' | 'eggs' | 'fish' | 'shellfish'
  | 'nuts' | 'peanuts' | 'soy' | 'sesame' | 'celery'
  | 'mustard' | 'sulphites' | 'lupin' | 'molluscs';

type DietaryFlag = 
  | 'vegetarian' | 'vegan' | 'halal' | 'kosher'
  | 'gluten_free' | 'dairy_free' | 'organic' | 'spicy';

type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock';
```

#### MenuItemVariant

```typescript
interface MenuItemVariant {
  id: string;
  menuItemId: string;            // FK → MenuItem
  
  // Identity
  sku?: string;
  
  // Content
  translations: VariantTranslation[];
  
  // Pricing
  price: number;                 // Bu varyantın fiyatı
  compareAtPrice?: number;
  
  // Attributes
  attributes: Record<string, string>;  // { size: 'large', type: 'iced' }
  
  // Availability
  isActive: boolean;
  stockStatus: StockStatus;
  
  sortOrder: number;
}

interface VariantTranslation {
  locale: string;
  name: string;                  // "Büyük Boy", "Large"
}
```

#### OptionGroup & Option

```typescript
interface OptionGroup {
  id: string;
  menuItemId: string;            // FK → MenuItem
  
  // Content
  translations: OptionGroupTranslation[];
  
  // Rules
  type: 'single' | 'multiple';   // Radio vs checkbox
  isRequired: boolean;           // Zorunlu seçim
  minSelections?: number;        // Min seçim (multiple)
  maxSelections?: number;        // Max seçim (multiple)
  
  // Display
  sortOrder: number;
  
  options: Option[];
}

interface Option {
  id: string;
  optionGroupId: string;         // FK → OptionGroup
  
  // Content
  translations: OptionTranslation[];
  
  // Pricing
  priceModifier: number;         // Ek fiyat (+500 = +5.00 TL)
  
  // Availability
  isActive: boolean;
  isDefault: boolean;            // Varsayılan seçili
  
  sortOrder: number;
}
```

---

## 3. API ENDPOINTS

### 3.1 Menu Management

```yaml
# Menu CRUD
GET    /api/v1/menus                    # List organization menus
POST   /api/v1/menus                    # Create menu
GET    /api/v1/menus/:menuId            # Get menu details
PATCH  /api/v1/menus/:menuId            # Update menu
DELETE /api/v1/menus/:menuId            # Soft delete menu

# Menu Actions
POST   /api/v1/menus/:menuId/publish    # Publish menu
POST   /api/v1/menus/:menuId/unpublish  # Unpublish menu
POST   /api/v1/menus/:menuId/duplicate  # Clone menu
GET    /api/v1/menus/:menuId/versions   # Version history

# Category Management
GET    /api/v1/menus/:menuId/categories
POST   /api/v1/menus/:menuId/categories
PATCH  /api/v1/menus/:menuId/categories/:categoryId
DELETE /api/v1/menus/:menuId/categories/:categoryId
POST   /api/v1/menus/:menuId/categories/reorder  # Bulk reorder

# Menu Item Management
GET    /api/v1/menus/:menuId/items
POST   /api/v1/menus/:menuId/items
GET    /api/v1/menus/:menuId/items/:itemId
PATCH  /api/v1/menus/:menuId/items/:itemId
DELETE /api/v1/menus/:menuId/items/:itemId
POST   /api/v1/menus/:menuId/items/reorder       # Bulk reorder
PATCH  /api/v1/menus/:menuId/items/bulk          # Bulk update

# Item Variants
GET    /api/v1/menus/:menuId/items/:itemId/variants
POST   /api/v1/menus/:menuId/items/:itemId/variants
PATCH  /api/v1/menus/:menuId/items/:itemId/variants/:variantId
DELETE /api/v1/menus/:menuId/items/:itemId/variants/:variantId

# Item Options
GET    /api/v1/menus/:menuId/items/:itemId/option-groups
POST   /api/v1/menus/:menuId/items/:itemId/option-groups
PATCH  /api/v1/menus/:menuId/items/:itemId/option-groups/:groupId
DELETE /api/v1/menus/:menuId/items/:itemId/option-groups/:groupId

# Stock Management (Quick actions)
PATCH  /api/v1/menus/:menuId/items/:itemId/stock
POST   /api/v1/menus/:menuId/items/bulk-stock    # Bulk stock update
```

### 3.2 Public Menu API

```yaml
# Public (no auth required)
GET    /api/v1/public/menus/:slug                 # Get published menu
GET    /api/v1/public/menus/:slug/categories      # Categories with items
GET    /api/v1/public/menus/:slug/items/:itemId   # Item details

# Query Parameters
# ?locale=tr           # Dil seçimi
# ?branch=branch-slug  # Şube filtresi
```

### 3.3 Request/Response Examples

#### Create Menu Item

```json
// POST /api/v1/menus/:menuId/items
// Request
{
  "categoryId": "cat_abc123",
  "sku": "BURGER-001",
  "basePrice": 15000,
  "compareAtPrice": 18000,
  "hasVariants": false,
  "translations": [
    {
      "locale": "tr",
      "name": "Klasik Burger",
      "description": "180gr dana eti, cheddar peyniri, özel sos",
      "shortDescription": "Klasik lezzet"
    },
    {
      "locale": "en",
      "name": "Classic Burger",
      "description": "180g beef patty, cheddar cheese, special sauce",
      "shortDescription": "Classic taste"
    }
  ],
  "allergens": ["gluten", "dairy"],
  "dietaryFlags": ["halal"],
  "preparationTime": 15,
  "isActive": true,
  "isFeatured": true
}

// Response 201
{
  "success": true,
  "data": {
    "id": "item_xyz789",
    "menuId": "menu_abc123",
    "categoryId": "cat_abc123",
    "sku": "BURGER-001",
    // ... full item object
  }
}
```

#### Bulk Stock Update

```json
// POST /api/v1/menus/:menuId/items/bulk-stock
// Request
{
  "updates": [
    { "itemId": "item_1", "stockStatus": "out_of_stock" },
    { "itemId": "item_2", "stockStatus": "in_stock" },
    { "itemId": "item_3", "variantId": "var_1", "stockStatus": "low_stock" }
  ]
}

// Response 200
{
  "success": true,
  "data": {
    "updated": 3,
    "failed": 0
  }
}
```

---

## 4. BUSINESS RULES

### 4.1 Validation Rules

```yaml
Menu:
  - name: required, 2-100 chars
  - slug: required, unique per organization, URL-safe
  - defaultLocale: required, valid ISO locale
  - currency: required, valid ISO currency code
  - An organization can have max 10 menus (tier-based)

Category:
  - name: required, 2-50 chars per locale
  - Max 3 levels of nesting (parent > child > grandchild)
  - Max 50 categories per menu
  - sortOrder: auto-increment if not provided

MenuItem:
  - name: required, 2-100 chars per locale
  - basePrice: required if no variants, >= 0
  - At least one locale translation required
  - Max 100 items per category
  - Max 10 variants per item
  - Max 5 option groups per item
  - Max 20 options per option group
  - Images: max 5 per item, max 5MB each

Variant:
  - price: required, >= 0
  - unique attribute combination per item

OptionGroup:
  - minSelections <= maxSelections
  - If required, minSelections >= 1
  - Options: at least 1 required
```

### 4.2 State Transitions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MENU STATUS TRANSITIONS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌──────────┐                                            │
│            create  │          │  publish                                   │
│         ─────────► │  draft   │ ──────────┐                               │
│                    │          │           │                                │
│                    └────┬─────┘           ▼                                │
│                         │           ┌──────────┐                           │
│                         │           │          │                           │
│                  archive│           │published │ ◄─────┐                   │
│                         │           │          │       │ edit              │
│                         │           └────┬─────┘       │ (auto-unpublish)  │
│                         │                │             │                    │
│                         │     unpublish  │             │                    │
│                         ▼                ▼             │                    │
│                    ┌──────────┐    ┌──────────┐       │                    │
│                    │          │    │          │───────┘                    │
│                    │ archived │    │  draft   │                            │
│                    │          │    │ (again)  │                            │
│                    └──────────┘    └──────────┘                            │
│                                                                             │
│  Rules:                                                                     │
│  - Only 'published' menus are visible to customers                         │
│  - Editing a published menu creates a new draft version                    │
│  - Publishing replaces the live version                                    │
│  - Archived menus can be restored to draft                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Pricing Rules

```yaml
Price Calculation:
  1. Start with variant price (or basePrice if no variant)
  2. Add selected option price modifiers
  3. Apply quantity multiplier
  4. Apply promotions (if any, from Promotion module)
  5. Calculate tax (if not included)

Display Rules:
  - Always show prices in organization's currency
  - If compareAtPrice exists and > currentPrice, show strikethrough
  - "Başlangıç fiyatı" prefix if item has variants with different prices
  - Format: "₺150,00" for TRY, "$15.00" for USD
```

---

## 5. UI/UX SPECIFICATIONS

### 5.1 Admin Panel - Menu Builder

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MENU BUILDER UI STRUCTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layout: 3-column (responsive)                                             │
│                                                                             │
│  ┌────────────┬──────────────────────────┬─────────────────┐               │
│  │            │                          │                 │               │
│  │  SIDEBAR   │      MAIN AREA           │   PREVIEW       │               │
│  │            │                          │   PANEL         │               │
│  │  Category  │  Item List / Editor      │                 │               │
│  │  Tree      │                          │   Mobile        │               │
│  │            │                          │   Preview       │               │
│  │  - Drag    │  - Drag & drop items     │                 │               │
│  │    & drop  │  - Inline quick edit     │   - Real-time   │               │
│  │  - Add     │  - Bulk actions          │   - Theme       │               │
│  │    new     │  - Search/filter         │     applied     │               │
│  │            │                          │                 │               │
│  └────────────┴──────────────────────────┴─────────────────┘               │
│                                                                             │
│  Responsive Breakpoints:                                                   │
│  - Desktop (>1280px): 3 columns                                           │
│  - Tablet (768-1279px): 2 columns, preview as modal                       │
│  - Mobile (<768px): Single column, tab navigation                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Key UI Components

```yaml
CategoryTree:
  - Collapsible tree view
  - Drag & drop reordering
  - Right-click context menu
  - Inline rename
  - Item count badge
  - Active/inactive toggle

MenuItemCard:
  - Thumbnail (lazy loaded)
  - Name, price, category
  - Stock status indicator
  - Quick actions: edit, duplicate, toggle active
  - Drag handle for reordering

ItemEditor:
  - Tabbed interface: Basic | Variants | Options | Media | SEO
  - Auto-save draft
  - Validation inline errors
  - Locale switcher
  - Price calculator (with options preview)

BulkActionsBar:
  - Appears when items selected
  - Actions: Delete, Change category, Update stock, Toggle active
  - Selection count

MobilePreview:
  - iPhone/Android frame
  - Actual theme rendering
  - Interactive (scroll, tap)
  - QR code for real device preview
```

### 5.3 Public Menu Display

```yaml
MenuPage:
  Layout: Single column, mobile-first
  
  Sections:
    Header:
      - Restaurant logo
      - Menu name
      - Language selector
      - Search icon
    
    CategoryNav:
      - Horizontal scroll tabs
      - Sticky on scroll
      - Active indicator
    
    CategorySection:
      - Category header with icon
      - Item grid (2 columns mobile, 3-4 desktop)
    
    ItemCard:
      - Image (4:3 ratio, lazy load)
      - Name
      - Short description (2 lines max)
      - Price
      - Allergen icons
      - Dietary badges
      - Add to cart button (if ordering enabled)
    
    ItemModal:
      - Full item details
      - Image gallery
      - Variant selector
      - Option groups
      - Quantity selector
      - Add to cart

  Accessibility:
    - Skip to main content link
    - ARIA landmarks
    - Focus management in modal
    - Keyboard navigation for options
```

---

## 6. PERFORMANCE REQUIREMENTS

### 6.1 Response Time Targets

| Endpoint | Target (p95) | Max |
|----------|--------------|-----|
| GET /public/menus/:slug | 100ms | 300ms |
| GET /menus (list) | 150ms | 500ms |
| POST /items | 200ms | 1s |
| PATCH /items/bulk | 500ms | 2s |
| Image upload | 2s | 5s |

### 6.2 Caching Strategy

```yaml
Public Menu:
  - CDN cache: 5 minutes (stale-while-revalidate)
  - Redis cache: 1 minute
  - Cache key: menu:{slug}:{locale}:{branchId?}
  - Invalidation: On publish, item update, stock change

Admin Data:
  - No CDN cache
  - Redis cache: 30 seconds (optional)
  - Real-time updates via WebSocket (optional)

Images:
  - CDN cache: 1 year (immutable)
  - Responsive variants generated on upload
  - WebP/AVIF with fallback
```

### 6.3 Data Limits (Tier-based)

```yaml
Free:
  - 1 menu
  - 5 categories
  - 25 items
  - 2 images per item
  - Basic locales: tr, en

Starter (₺2,000):
  - 3 menus
  - 20 categories
  - 100 items
  - 3 images per item
  - 5 locales

Professional (₺4,000):
  - 5 menus
  - 50 categories
  - 300 items
  - 5 images per item
  - 10 locales

Business (₺6,000):
  - 10 menus
  - 100 categories
  - 500 items
  - 5 images per item
  - Unlimited locales

Enterprise (₺8,000):
  - Unlimited menus
  - Unlimited categories
  - Unlimited items
  - 10 images per item
  - Unlimited locales
  - Custom fields
```

---

## 7. SECURITY CONSIDERATIONS

### 7.1 Authorization Matrix

```yaml
Endpoints by Role:

GET /menus:
  - owner: ✓ (all)
  - manager: ✓ (all)
  - staff: ✓ (all)
  - viewer: ✓ (all)

POST /menus:
  - owner: ✓
  - manager: ✗
  - staff: ✗
  - viewer: ✗

PATCH /menus/:id:
  - owner: ✓
  - manager: ✓
  - staff: ✗
  - viewer: ✗

DELETE /menus/:id:
  - owner: ✓
  - manager: ✗
  - staff: ✗
  - viewer: ✗

PATCH /items/:id/stock:
  - owner: ✓
  - manager: ✓
  - staff: ✓
  - viewer: ✗

POST /menus/:id/publish:
  - owner: ✓
  - manager: ✗ (requires owner approval)
  - staff: ✗
  - viewer: ✗
```

### 7.2 Data Validation

```yaml
Input Sanitization:
  - HTML strip from text fields
  - URL validation for links
  - Image type verification (magic bytes)
  - File size limits enforced

SQL Injection:
  - Parameterized queries (Prisma)
  - No raw SQL

XSS Prevention:
  - Output encoding in templates
  - CSP headers
  - Sanitized user content display
```

---

## 8. TESTING REQUIREMENTS

### 8.1 Unit Tests

```yaml
Coverage Target: 80%

Critical Functions:
  - Price calculation (with variants, options)
  - Stock status determination
  - Visibility rules (scheduled, active)
  - Validation logic
  - Slug generation
```

### 8.2 Integration Tests

```yaml
API Tests:
  - Full CRUD cycle for each entity
  - Authorization enforcement
  - Validation error responses
  - Pagination
  - Filtering
  - Bulk operations

Database Tests:
  - Cascade deletes
  - Unique constraints
  - Foreign key integrity
```

### 8.3 E2E Tests

```yaml
Critical Flows:
  1. Create menu → Add categories → Add items → Publish
  2. Customer views menu → Filters by category → Views item details
  3. Staff updates stock status → Customer sees update
  4. Bulk import items from CSV
  5. Duplicate menu for new branch
```

---

## 9. IMPLEMENTATION NOTES

### 9.1 Database Indexes

```sql
-- Performance critical indexes
CREATE INDEX idx_menu_org_status ON menus(organization_id, status);
CREATE INDEX idx_category_menu_sort ON categories(menu_id, sort_order);
CREATE INDEX idx_item_category_sort ON menu_items(category_id, sort_order);
CREATE INDEX idx_item_menu_active ON menu_items(menu_id, is_active);
CREATE INDEX idx_menu_slug ON menus(slug) WHERE status = 'published';
```

### 9.2 Event Emissions

```yaml
Events (for other modules):
  - menu.created
  - menu.updated
  - menu.published
  - menu.unpublished
  - menu.deleted
  - item.created
  - item.updated
  - item.deleted
  - item.stock_changed
  - category.created
  - category.deleted
```

### 9.3 Migration Path

```yaml
v1.0 → v1.1:
  - Add 'preparationTime' field
  - Add 'isNew' badge field
  - Migrate existing items (defaults)

v1.1 → v1.2:
  - Add scheduled visibility
  - Add nutrition info
  - Optional migration
```

---

## 10. ACCEPTANCE CRITERIA

### 10.1 MVP (v1.0)

- [ ] CRUD operations for Menu, Category, MenuItem
- [ ] Multi-language support (TR, EN)
- [ ] Basic variant support
- [ ] Option groups with single/multiple selection
- [ ] Image upload (max 3 per item)
- [ ] Stock status management
- [ ] Public menu display
- [ ] Mobile-responsive admin UI
- [ ] Role-based access control

### 10.2 Post-MVP

- [ ] Advanced scheduling (visibility windows)
- [ ] Bulk import/export (CSV/Excel)
- [ ] Menu versioning and rollback
- [ ] Nutrition calculator
- [ ] AI description generator integration
- [ ] Print menu export (PDF)

---

*Bu spesifikasyon, Menu modülünün eksiksiz implementasyonu için referans belgesidir.*
