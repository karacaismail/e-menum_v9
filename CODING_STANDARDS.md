# E-Menum Coding Standards

> **Auto-Claude Coding Standards Document**  
> TypeScript conventions, naming, patterns, Git workflow.  
> Son Güncelleme: 2026-01-31

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

### 1.2 Vibecoding Optimization

```
LLM-Friendly Code Patterns:

✅ DO:
├── Use established patterns (BaseService, BaseController)
├── Explicit type annotations
├── JSDoc comments on public methods
├── Consistent file structure
├── Descriptive variable names
└── Small, focused functions (<30 lines)

❌ DON'T:
├── Custom abstractions without examples
├── Magic strings or numbers
├── Implicit type inference for complex types
├── Circular dependencies
├── Deep nesting (>3 levels)
└── Side effects in unexpected places
```

---

## 2. TYPESCRIPT CONVENTIONS

### 2.1 Type Annotations

```typescript
// ✅ GOOD: Explicit return types on public methods
async function getMenuById(id: string): Promise<Menu | null> {
  return prisma.menu.findUnique({ where: { id } });
}

// ✅ GOOD: Interface for complex objects
interface CreateMenuInput {
  name: string;
  description?: string;
  themeId?: string;
}

// ❌ BAD: Implicit any
function processData(data) {  // Missing type!
  return data.map(x => x.value);
}

// ❌ BAD: Over-reliance on inference for public API
const getUser = async (id) => {  // Missing types!
  return await prisma.user.findUnique({ where: { id } });
};
```

### 2.2 Type vs Interface

```typescript
// Use INTERFACE for:
// - Object shapes (data structures)
// - Extendable contracts
// - Class implementations

interface User {
  id: string;
  email: string;
  name: string;
}

interface UserWithRoles extends User {
  roles: Role[];
}

// Use TYPE for:
// - Unions and intersections
// - Computed types
// - Function signatures

type Status = 'active' | 'inactive' | 'pending';
type Nullable<T> = T | null;
type AsyncHandler<T> = () => Promise<T>;

// ❌ AVOID: Mixing without reason
type User = {  // Should be interface
  id: string;
};
```

### 2.3 Enums vs Union Types

```typescript
// Use STRING ENUMS for:
// - Database values
// - API contracts
// - Values that need runtime existence

enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PREPARING = 'preparing',
  READY = 'ready',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

// Use UNION TYPES for:
// - Internal type narrowing
// - Simple string literals

type ButtonVariant = 'primary' | 'secondary' | 'ghost';
type Size = 'sm' | 'md' | 'lg';

// ❌ AVOID: Numeric enums (unclear values)
enum Status {
  Active,   // = 0, unclear!
  Inactive, // = 1
}
```

### 2.4 Generics

```typescript
// ✅ GOOD: Descriptive generic names
interface Repository<TEntity, TCreateInput, TUpdateInput> {
  findById(id: string): Promise<TEntity | null>;
  create(data: TCreateInput): Promise<TEntity>;
  update(id: string, data: TUpdateInput): Promise<TEntity>;
}

// ✅ GOOD: Constrained generics
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// ❌ BAD: Single letter without context
function process<T, U, V>(a: T, b: U): V {  // What are T, U, V?
  // ...
}
```

### 2.5 Null Handling

```typescript
// ✅ GOOD: Explicit null checks
async function getMenu(id: string): Promise<Menu> {
  const menu = await prisma.menu.findUnique({ where: { id } });
  
  if (!menu) {
    throw new AppException('MENU_NOT_FOUND', 404);
  }
  
  return menu;
}

// ✅ GOOD: Optional chaining with nullish coalescing
const userName = user?.profile?.name ?? 'Anonymous';

// ❌ BAD: Non-null assertion without validation
const menu = await prisma.menu.findUnique({ where: { id } });
return menu!.name;  // Dangerous!

// ❌ BAD: Truthy check for potentially 0 or ''
const count = data.count || 10;  // Fails if count is 0!
const count = data.count ?? 10;  // ✅ Correct
```

---

## 3. NAMING CONVENTIONS

### 3.1 Files & Folders

```
Naming Patterns:

Files:
├── kebab-case.ts           # General files
├── PascalCase.ts           # Classes, React components (N/A for now)
├── kebab-case.spec.ts      # Test files
├── kebab-case.dto.ts       # DTOs
├── kebab-case.schema.prisma # Prisma schemas
└── UPPER_CASE.md           # Documentation

Folders:
├── kebab-case/             # Feature modules
├── __tests__/              # Test directories
└── _system/                # System modules (prefix)

Examples:
├── menu.controller.ts
├── menu.service.ts
├── menu.service.spec.ts
├── create-menu.dto.ts
├── menu.schema.prisma
└── menu/
    ├── manifest.json
    ├── menu.controller.ts
    └── dto/
        └── create-menu.dto.ts
```

### 3.2 Variables & Functions

```typescript
// Variables: camelCase
const menuItems = [];
const isActive = true;
const hasPermission = false;
let currentPage = 1;

// Constants: SCREAMING_SNAKE_CASE (module-level)
const MAX_ITEMS_PER_PAGE = 100;
const DEFAULT_CURRENCY = 'TRY';
const API_VERSION = 'v1';

// Functions: camelCase, verb prefix
function getMenuById(id: string) {}
function createOrder(data: CreateOrderInput) {}
function validateEmail(email: string) {}
function isValidPrice(price: number) {}
function hasPermission(user: User, action: string) {}

// Boolean variables: is/has/can/should prefix
const isLoading = true;
const hasError = false;
const canEdit = user.role === 'owner';
const shouldRefresh = lastUpdate < threshold;

// Event handlers: handle prefix (for UI)
function handleSubmit() {}
function handleClick() {}
function handleChange() {}
```

### 3.3 Classes & Interfaces

```typescript
// Classes: PascalCase, noun
class MenuService {}
class OrderController {}
class AuthMiddleware {}

// Interfaces: PascalCase, noun (no I prefix)
interface User {}
interface CreateMenuInput {}
interface PaginationParams {}

// ❌ AVOID: Hungarian notation
interface IUser {}      // No I prefix
interface UserInterface {} // No Interface suffix

// Abstract classes: Abstract prefix or Base prefix
abstract class BaseService<T> {}
abstract class BaseController {}

// Type aliases: PascalCase
type MenuWithCategories = Menu & { categories: Category[] };
type Nullable<T> = T | null;
```

### 3.4 Database & API

```typescript
// Database tables: PascalCase singular (Prisma convention)
model Menu {}
model Category {}
model OrderItem {}

// Database columns: camelCase
model Product {
  id          String
  categoryId  String   // FK
  basePrice   Decimal
  isActive    Boolean
  createdAt   DateTime
}

// API endpoints: kebab-case plural
GET  /api/v1/menus
GET  /api/v1/menu-items
POST /api/v1/qr-codes

// Query params: camelCase
GET /api/v1/products?categoryId=xxx&isActive=true&sortBy=name

// JSON keys: camelCase
{
  "menuId": "xxx",
  "categoryName": "Drinks",
  "isPublished": true
}
```

---

## 4. FILE STRUCTURE PATTERNS

### 4.1 Module Structure

```
modules/menu/
├── manifest.json           # Module metadata
├── menu.controller.ts      # HTTP handlers
├── menu.service.ts         # Business logic
├── menu.repository.ts      # Data access (optional)
├── menu.routes.ts          # Route definitions (optional)
├── menu.schema.prisma      # Database schema
├── dto/
│   ├── create-menu.dto.ts
│   ├── update-menu.dto.ts
│   └── menu-response.dto.ts
├── types/
│   └── menu.types.ts       # Module-specific types
├── hooks/
│   ├── on-enable.ts
│   └── on-disable.ts
├── events/
│   └── menu.events.ts      # Event definitions
├── __tests__/
│   ├── menu.service.spec.ts
│   └── menu.e2e.spec.ts
└── views/                  # EJS templates (if needed)
    ├── index.ejs
    └── partials/
```

### 4.2 File Organization Rules

```typescript
// File order within a file:

// 1. Imports (grouped)
import { injectable, inject } from 'tsyringe';           // External
import { PrismaClient } from '@prisma/client';           // External

import { BaseService } from '@/core/base/base.service'; // Internal (alias)
import { AppException } from '@/core/exceptions';        // Internal

import { CreateMenuDto } from './dto/create-menu.dto';   // Local
import { Menu } from './types/menu.types';               // Local

// 2. Constants
const MAX_CATEGORIES = 50;

// 3. Types/Interfaces (if not in separate file)
interface MenuFilters {
  isPublished?: boolean;
}

// 4. Class/Function definition
@injectable()
export class MenuService extends BaseService<Menu> {
  // 4a. Properties
  private readonly cacheKey = 'menu';
  
  // 4b. Constructor
  constructor(
    @inject('PrismaClient') private prisma: PrismaClient,
  ) {
    super();
  }
  
  // 4c. Public methods
  async findAll(orgId: string): Promise<Menu[]> {}
  
  async create(data: CreateMenuDto): Promise<Menu> {}
  
  // 4d. Private methods
  private validateMenu(menu: Menu): void {}
}

// 5. Exports (if not inline)
export { MenuService };
```

### 4.3 Import Conventions

```typescript
// ✅ GOOD: Use path aliases
import { BaseService } from '@/core/base/base.service';
import { MenuService } from '@/modules/menu/menu.service';

// ❌ BAD: Relative paths climbing up
import { BaseService } from '../../../core/base/base.service';

// ✅ GOOD: Grouped and ordered imports
// 1. Node built-ins
import { join } from 'path';

// 2. External packages
import { injectable } from 'tsyringe';
import { z } from 'zod';

// 3. Internal aliases
import { BaseService } from '@/core/base';
import { AppException } from '@/core/exceptions';

// 4. Relative imports
import { CreateMenuDto } from './dto';

// ✅ GOOD: Named exports
import { MenuService, MenuController } from '@/modules/menu';

// ❌ AVOID: Default exports (except for classes)
export default { /* ... */ };  // Hard to refactor
```

---

## 5. ASYNC PATTERNS

### 5.1 Async/Await Best Practices

```typescript
// ✅ GOOD: Always use async/await (not raw promises)
async function getMenu(id: string): Promise<Menu> {
  const menu = await prisma.menu.findUnique({ where: { id } });
  return menu;
}

// ❌ BAD: Mixing promise chains
function getMenu(id: string): Promise<Menu> {
  return prisma.menu.findUnique({ where: { id } })
    .then(menu => menu)
    .catch(err => { throw err; });
}

// ✅ GOOD: Parallel execution when independent
async function getDashboardData(orgId: string) {
  const [menus, orders, stats] = await Promise.all([
    menuService.findAll(orgId),
    orderService.findRecent(orgId),
    analyticsService.getStats(orgId),
  ]);
  
  return { menus, orders, stats };
}

// ❌ BAD: Sequential when could be parallel
async function getDashboardData(orgId: string) {
  const menus = await menuService.findAll(orgId);     // Waits...
  const orders = await orderService.findRecent(orgId); // Then waits...
  const stats = await analyticsService.getStats(orgId); // Then waits...
  return { menus, orders, stats };
}

// ✅ GOOD: Error handling with Promise.allSettled
async function batchProcess(items: Item[]) {
  const results = await Promise.allSettled(
    items.map(item => processItem(item))
  );
  
  const succeeded = results.filter(r => r.status === 'fulfilled');
  const failed = results.filter(r => r.status === 'rejected');
  
  return { succeeded, failed };
}
```

### 5.2 Error Handling in Async

```typescript
// ✅ GOOD: Centralized error handling via middleware
async function createMenu(data: CreateMenuDto): Promise<Menu> {
  // Just throw, middleware catches
  const existing = await prisma.menu.findFirst({
    where: { organizationId: data.orgId, slug: data.slug }
  });
  
  if (existing) {
    throw new AppException('MENU_ALREADY_EXISTS', 409);
  }
  
  return prisma.menu.create({ data });
}

// ✅ GOOD: Specific error handling when needed
async function syncWithExternalApi(orgId: string): Promise<void> {
  try {
    await externalApi.sync(orgId);
  } catch (error) {
    if (error instanceof ExternalApiError) {
      // Log but don't fail the main operation
      logger.warn('External sync failed', { orgId, error });
      return;
    }
    throw error; // Re-throw unexpected errors
  }
}

// ❌ BAD: Swallowing errors
async function riskyOperation() {
  try {
    await doSomething();
  } catch (error) {
    // Silent failure! BAD!
  }
}

// ❌ BAD: Generic catch without discrimination
async function process() {
  try {
    await doSomething();
  } catch (error) {
    throw new Error('Something went wrong'); // Lost context!
  }
}
```

---

## 6. ERROR HANDLING

### 6.1 AppException Pattern

```typescript
// core/exceptions/app.exception.ts

export class AppException extends Error {
  constructor(
    public readonly code: string,
    public readonly statusCode: number = 400,
    public readonly details?: Record<string, unknown>,
  ) {
    super(code);
    this.name = 'AppException';
  }
  
  static notFound(resource: string, id?: string): AppException {
    return new AppException(
      `${resource.toUpperCase()}_NOT_FOUND`,
      404,
      { resource, id }
    );
  }
  
  static forbidden(action: string): AppException {
    return new AppException('FORBIDDEN', 403, { action });
  }
  
  static validation(errors: ValidationError[]): AppException {
    return new AppException('VALIDATION_ERROR', 400, { errors });
  }
}

// Usage:
throw new AppException('MENU_NOT_FOUND', 404);
throw AppException.notFound('Menu', menuId);
throw AppException.forbidden('menu.delete');
```

### 6.2 Error Codes Catalog

```typescript
// core/exceptions/error-codes.ts

export const ErrorCodes = {
  // Authentication (1xxx)
  UNAUTHORIZED: { code: 'UNAUTHORIZED', status: 401 },
  TOKEN_EXPIRED: { code: 'TOKEN_EXPIRED', status: 401 },
  INVALID_CREDENTIALS: { code: 'INVALID_CREDENTIALS', status: 401 },
  
  // Authorization (2xxx)
  FORBIDDEN: { code: 'FORBIDDEN', status: 403 },
  INSUFFICIENT_PLAN: { code: 'INSUFFICIENT_PLAN', status: 403 },
  FEATURE_DISABLED: { code: 'FEATURE_DISABLED', status: 403 },
  
  // Validation (3xxx)
  VALIDATION_ERROR: { code: 'VALIDATION_ERROR', status: 400 },
  INVALID_INPUT: { code: 'INVALID_INPUT', status: 400 },
  
  // Resources (4xxx)
  NOT_FOUND: { code: 'NOT_FOUND', status: 404 },
  ALREADY_EXISTS: { code: 'ALREADY_EXISTS', status: 409 },
  CONFLICT: { code: 'CONFLICT', status: 409 },
  
  // Rate Limiting (5xxx)
  RATE_LIMITED: { code: 'RATE_LIMITED', status: 429 },
  QUOTA_EXCEEDED: { code: 'QUOTA_EXCEEDED', status: 429 },
  
  // Server (9xxx)
  INTERNAL_ERROR: { code: 'INTERNAL_ERROR', status: 500 },
  SERVICE_UNAVAILABLE: { code: 'SERVICE_UNAVAILABLE', status: 503 },
} as const;
```

### 6.3 Validation with Zod

```typescript
// dto/create-menu.dto.ts
import { z } from 'zod';

export const CreateMenuSchema = z.object({
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name too long'),
  
  slug: z.string()
    .regex(/^[a-z0-9-]+$/, 'Invalid slug format')
    .optional(),
  
  description: z.string()
    .max(500)
    .optional(),
  
  themeId: z.string()
    .cuid()
    .optional(),
  
  settings: z.object({
    showPrices: z.boolean().default(true),
    currency: z.enum(['TRY', 'USD', 'EUR']).default('TRY'),
  }).optional(),
});

export type CreateMenuDto = z.infer<typeof CreateMenuSchema>;

// Usage in controller:
@Post('/')
async create(@Body() body: unknown) {
  const data = CreateMenuSchema.parse(body); // Throws ZodError
  return this.menuService.create(data);
}
```

---

## 7. CODE PATTERNS

### 7.1 Service Pattern

```typescript
// ✅ GOOD: BaseService extension
@injectable()
export class MenuService extends BaseService<Menu> {
  constructor(
    @inject('PrismaClient') private prisma: PrismaClient,
    @inject(EventService) private events: EventService,
  ) {
    super();
  }
  
  // Standard CRUD
  async findAll(orgId: string, filters?: MenuFilters): Promise<Menu[]> {
    return this.prisma.menu.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        ...this.buildFilters(filters),
      },
      orderBy: { sortOrder: 'asc' },
    });
  }
  
  async findById(id: string, orgId: string): Promise<Menu> {
    const menu = await this.prisma.menu.findFirst({
      where: { id, organizationId: orgId, deletedAt: null },
    });
    
    if (!menu) {
      throw AppException.notFound('Menu', id);
    }
    
    return menu;
  }
  
  async create(orgId: string, data: CreateMenuDto): Promise<Menu> {
    const menu = await this.prisma.menu.create({
      data: {
        ...data,
        organizationId: orgId,
        slug: data.slug || this.generateSlug(data.name),
      },
    });
    
    await this.events.emit('menu.created', { menuId: menu.id, orgId });
    
    return menu;
  }
  
  // Custom methods
  async publish(id: string, orgId: string): Promise<Menu> {
    const menu = await this.findById(id, orgId);
    
    const updated = await this.prisma.menu.update({
      where: { id },
      data: { isPublished: true, publishedAt: new Date() },
    });
    
    await this.events.emit('menu.published', { menuId: id, orgId });
    
    return updated;
  }
  
  // Private helpers
  private buildFilters(filters?: MenuFilters) {
    if (!filters) return {};
    
    return {
      ...(filters.isPublished !== undefined && { isPublished: filters.isPublished }),
    };
  }
  
  private generateSlug(name: string): string {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');
  }
}
```

### 7.2 Controller Pattern

```typescript
// ✅ GOOD: BaseController extension with decorators
@JsonController('/menus')
@injectable()
export class MenuController extends BaseController {
  constructor(
    @inject(MenuService) private menuService: MenuService,
  ) {
    super();
  }
  
  @Get('/')
  @Authorized(['menu.view'])
  async list(
    @CurrentOrg() org: Organization,
    @QueryParams() query: ListMenusQuery,
  ): Promise<ApiResponse<Menu[]>> {
    const menus = await this.menuService.findAll(org.id, query);
    return this.success(menus);
  }
  
  @Get('/:id')
  @Authorized(['menu.view'])
  async get(
    @Param('id') id: string,
    @CurrentOrg() org: Organization,
  ): Promise<ApiResponse<Menu>> {
    const menu = await this.menuService.findById(id, org.id);
    return this.success(menu);
  }
  
  @Post('/')
  @Authorized(['menu.create'])
  async create(
    @Body() body: unknown,
    @CurrentOrg() org: Organization,
  ): Promise<ApiResponse<Menu>> {
    const data = CreateMenuSchema.parse(body);
    const menu = await this.menuService.create(org.id, data);
    return this.created(menu);
  }
  
  @Post('/:id/publish')
  @Authorized(['menu.publish'])
  async publish(
    @Param('id') id: string,
    @CurrentOrg() org: Organization,
  ): Promise<ApiResponse<Menu>> {
    const menu = await this.menuService.publish(id, org.id);
    return this.success(menu);
  }
}
```

### 7.3 Repository Pattern (Optional)

```typescript
// Use when data access logic is complex
@injectable()
export class MenuRepository {
  constructor(
    @inject('PrismaClient') private prisma: PrismaClient,
  ) {}
  
  async findWithCategories(id: string, orgId: string): Promise<MenuWithCategories | null> {
    return this.prisma.menu.findFirst({
      where: { id, organizationId: orgId, deletedAt: null },
      include: {
        categories: {
          where: { deletedAt: null },
          orderBy: { sortOrder: 'asc' },
          include: {
            products: {
              where: { deletedAt: null, isActive: true },
              orderBy: { sortOrder: 'asc' },
            },
          },
        },
      },
    });
  }
  
  async findPublished(orgId: string): Promise<Menu[]> {
    return this.prisma.menu.findMany({
      where: {
        organizationId: orgId,
        isPublished: true,
        deletedAt: null,
      },
    });
  }
}
```

---

## 8. GIT WORKFLOW

### 8.1 Branch Strategy

```
Branch Model: GitHub Flow (simplified)

main (production)
  │
  └── feature/xxx ─────────────► PR → main
  └── fix/xxx ─────────────────► PR → main
  └── hotfix/xxx ──────────────► PR → main (urgent)

Branch Naming:
├── feature/menu-variants      # New feature
├── fix/order-calculation      # Bug fix
├── hotfix/auth-bypass         # Critical fix
├── refactor/service-layer     # Code improvement
├── docs/api-contracts         # Documentation
└── chore/update-deps          # Maintenance
```

### 8.2 Commit Convention

```
Format: <type>(<scope>): <subject>

Types:
├── feat     # New feature
├── fix      # Bug fix
├── docs     # Documentation
├── style    # Formatting (no code change)
├── refactor # Code restructure
├── test     # Adding tests
├── chore    # Maintenance
└── perf     # Performance

Examples:
feat(menu): add category reordering
fix(orders): correct tax calculation
docs(api): update authentication section
refactor(auth): extract token service
test(menu): add service unit tests
chore(deps): update prisma to 6.2

Breaking Changes:
feat(api)!: change response format
  
  BREAKING CHANGE: Response now wraps data in { success, data }
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
- [ ] Other: ___

## Checklist
- [ ] Code follows style guide
- [ ] Self-reviewed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No console.log or debug code
- [ ] PR title follows commit convention

## Testing
How was this tested?

## Screenshots (if UI change)
Before | After
```

### 8.4 Code Review Guidelines

```
Reviewer Checklist:

Correctness:
├── Does it solve the problem?
├── Are edge cases handled?
└── Are there potential bugs?

Security:
├── Tenant isolation maintained?
├── Input validated?
├── No sensitive data exposed?

Performance:
├── N+1 queries avoided?
├── Unnecessary operations?
└── Caching considered?

Maintainability:
├── Clear naming?
├── Appropriate abstractions?
├── Tests included?

Style:
├── Follows conventions?
├── Consistent with codebase?
└── Well documented?
```

---

## 9. DOCUMENTATION

### 9.1 JSDoc Standards

```typescript
/**
 * Creates a new menu for the organization.
 * 
 * @param orgId - Organization ID
 * @param data - Menu creation data
 * @returns The created menu
 * @throws {AppException} MENU_ALREADY_EXISTS if slug exists
 * @throws {AppException} CATEGORY_LIMIT_EXCEEDED if plan limit reached
 * 
 * @example
 * ```typescript
 * const menu = await menuService.create('org_123', {
 *   name: 'Main Menu',
 *   description: 'Our main offerings',
 * });
 * ```
 */
async create(orgId: string, data: CreateMenuDto): Promise<Menu> {
  // ...
}

/**
 * Menu service handles all menu-related operations.
 * 
 * @remarks
 * This service enforces tenant isolation and plan-based limits.
 * All methods require a valid organization context.
 */
@injectable()
export class MenuService {
  // ...
}
```

### 9.2 Inline Comments

```typescript
// ✅ GOOD: Explain WHY, not WHAT
// Using soft delete to maintain referential integrity with orders
await prisma.menu.update({
  where: { id },
  data: { deletedAt: new Date() },
});

// ✅ GOOD: Explain complex business logic
// Price includes 18% VAT for Turkey, but displayed separately
const vatRate = 0.18;
const basePrice = totalPrice / (1 + vatRate);
const vatAmount = totalPrice - basePrice;

// ❌ BAD: Obvious comments
// Get the menu
const menu = await getMenu(id);

// ❌ BAD: Outdated comments
// TODO: Remove after Q1 2024  (It's 2026!)
```

---

## 10. LINTING & FORMATTING

### 10.1 ESLint Configuration

```javascript
// .eslintrc.js (key rules)
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  rules: {
    // TypeScript
    '@typescript-eslint/explicit-function-return-type': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    
    // General
    'no-console': ['error', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    
    // Import
    'import/order': ['error', {
      groups: ['builtin', 'external', 'internal', 'parent', 'sibling'],
      'newlines-between': 'always',
    }],
  },
};
```

### 10.2 Prettier Configuration

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

### 10.3 Editor Configuration

```ini
# .editorconfig
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```

---

*Bu döküman, E-Menum kod standartlarını tanımlar. Tüm kod bu kurallara uygun yazılmalıdır.*
