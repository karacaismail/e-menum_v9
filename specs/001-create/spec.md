# Specification: E-Menum Enterprise QR Menu Platform

## Overview

E-Menum is an enterprise-ready QR menu and restaurant management platform for Turkey's F&B sector. This specification covers the complete implementation of the platform from scratch, including 8 core system modules, 2 fully-implemented business modules (menu, order), 3 themes, and 12+ stub module interfaces. The architecture follows a WordPress-style plugin system with dynamic module loading, multi-tenant data isolation, and compile-time TypeScript safety. This is NOT an MVP - it's a production-grade foundation designed for scalability and future module expansion.

## Workflow Type

**Type**: feature

**Rationale**: This is a greenfield implementation of a complete platform with multiple modules, database schemas, authentication systems, and UI themes. The workflow involves creating the entire codebase structure, implementing core functionality, and establishing patterns that all future development will follow.

## Task Scope

### Services Involved
- **backend** (primary) - Node.js/Express.js API server with TypeScript
- **database** (primary) - PostgreSQL 15+ with Prisma ORM
- **cache** (integration) - Redis 7.x for caching and BullMQ queues
- **frontend** (primary) - EJS templates with Tailwind CSS and Alpine.js

### This Task Will:
- [ ] Set up project structure with proper directory organization
- [ ] Implement core kernel (bootstrap, DI container, module loader)
- [ ] Create 8 core modules: auth, organization, branch, user, media, notification, subscription, module-loader
- [ ] Implement 2 enterprise modules: menu, order
- [ ] Create 1 reference module: advanced-example
- [ ] Define 12+ stub module interfaces (payment, analytics, ai, etc.)
- [ ] Build 3 themes: admin-theme, product-theme, example-theme
- [ ] Set up multi-tenant database schema with Prisma
- [ ] Implement JWT authentication with refresh tokens
- [ ] Create RBAC/ABAC authorization with CASL
- [ ] Build RESTful API with versioning (/api/v1/*)
- [ ] Implement i18n for TR/EN languages
- [ ] Set up CI/CD pipeline with GitHub Actions
- [ ] Configure deployment for Coolify on Hetzner VPS

### Out of Scope:
- Implementation of stub modules beyond interfaces (payment, analytics, ai, etc.)
- Additional themes beyond the 3 specified
- Native mobile applications
- GraphQL API (REST only)
- MongoDB or other NoSQL (PostgreSQL only)
- React/Vue/Angular (EJS + Alpine.js only)
- Multi-currency support (TRY only for MVP)
- Real-time WebSocket features (polling only)

## Service Context

### Backend Service

**Tech Stack:**
- Language: TypeScript 5.x (strict mode)
- Runtime: Node.js 20+ LTS
- Framework: Express.js 4.x with routing-controllers
- ORM: Prisma 6.x
- DI Container: tsyringe (Microsoft)
- Validation: Zod
- Authorization: CASL (ABAC/RBAC)

**Entry Point:** `src/main.ts`

**How to Run:**
```bash
npm run dev          # Development with hot reload
npm run build        # Production build
npm start            # Production server
```

**Port:** 3000

### Database Service

**Tech Stack:**
- Database: PostgreSQL 15+
- Schema: Multi-file Prisma schemas (merged)
- Migrations: Prisma Migrate

**Entry Point:** `prisma/schema.prisma` (merged from `prisma/schema/*.prisma`)

**How to Run:**
```bash
npm run schema:merge      # Merge multi-file schemas
npm run prisma:generate   # Generate Prisma client
npm run prisma:migrate    # Run migrations
npm run prisma:studio     # Open Prisma Studio
```

**Port:** 5432

### Cache Service

**Tech Stack:**
- Cache: Redis 7.x
- Queues: BullMQ

**Entry Point:** `src/config/redis.ts`

**How to Run:**
```bash
redis-server          # Start Redis
```

**Port:** 6379

### Frontend Service

**Tech Stack:**
- Templates: EJS 3.x (SSR)
- CSS: Tailwind CSS 3.4.x
- Components: Flowbite
- Icons: Phosphor Icons (primary), FontAwesome (fallback)
- Interactivity: Alpine.js 3.x
- Charts: Chart.js / ApexCharts

**Entry Point:** `src/views/` and `themes/`

**How to Run:**
```bash
npm run dev           # Vite dev server for CSS/JS
npm run build:css     # Build production CSS
```

## Files to Modify

Since this is a greenfield project, all files will be created. Key files to create:

| File | Service | What to Create |
|------|---------|----------------|
| `src/main.ts` | backend | Application entry point |
| `src/config/env.ts` | backend | Zod-validated environment config |
| `src/config/database.ts` | backend | Prisma client singleton |
| `src/config/redis.ts` | backend | Redis client configuration |
| `src/core/kernel/bootstrap.ts` | backend | Application bootstrap sequence |
| `src/core/kernel/container.ts` | backend | DI container setup with tsyringe |
| `src/core/kernel/module-loader.ts` | backend | Module discovery and loading |
| `src/core/base/base.controller.ts` | backend | CRUD controller template |
| `src/core/base/base.service.ts` | backend | CRUD service template |
| `src/core/base/base.repository.ts` | backend | Repository pattern base |
| `src/core/middleware/auth.middleware.ts` | backend | JWT verification middleware |
| `src/core/middleware/tenant.middleware.ts` | backend | Multi-tenant context middleware |
| `src/core/middleware/permission.middleware.ts` | backend | CASL ability check |
| `src/core/middleware/rate-limit.middleware.ts` | backend | Rate limiting |
| `src/core/middleware/error.middleware.ts` | backend | Global error handler |
| `src/core/services/auth.service.ts` | backend | Authentication logic |
| `src/core/services/permission.service.ts` | backend | CASL ability builder |
| `src/core/services/event.service.ts` | backend | Domain event bus |
| `src/core/exceptions/app.exception.ts` | backend | Custom exception base |
| `src/core/exceptions/error-codes.ts` | backend | Centralized error codes |
| `src/modules/_core/auth/*` | backend | Auth module |
| `src/modules/_core/organization/*` | backend | Organization module |
| `src/modules/_core/branch/*` | backend | Branch module |
| `src/modules/_core/user/*` | backend | User module |
| `src/modules/_core/media/*` | backend | Media module |
| `src/modules/_core/notification/*` | backend | Notification module |
| `src/modules/_core/subscription/*` | backend | Subscription module |
| `src/modules/_core/module-loader/*` | backend | Module loader module |
| `src/modules/menu/*` | backend | Menu module (full) |
| `src/modules/order/*` | backend | Order module (full) |
| `src/modules/_examples/advanced-example/*` | backend | Reference module |
| `src/modules/_stubs/payment/*` | backend | Payment stub |
| `src/modules/_stubs/analytics/*` | backend | Analytics stub |
| `src/modules/_stubs/ai/*` | backend | AI stub |
| `src/modules/_stubs/campaign/*` | backend | Campaign stub |
| `src/modules/_stubs/loyalty/*` | backend | Loyalty stub |
| `src/modules/_stubs/inventory/*` | backend | Inventory stub |
| `src/modules/_stubs/reservation/*` | backend | Reservation stub |
| `src/modules/_stubs/feedback/*` | backend | Feedback stub |
| `src/modules/_stubs/integration/*` | backend | Integration stub |
| `src/modules/_stubs/pos/*` | backend | POS stub |
| `src/modules/_stubs/kitchen-display/*` | backend | Kitchen Display stub |
| `src/modules/_stubs/table-management/*` | backend | Table Management stub |
| `prisma/schema/base.prisma` | database | Datasource, generator |
| `prisma/schema/core.prisma` | database | Core entities |
| `prisma/schema/menu.prisma` | database | Menu entities |
| `prisma/schema/order.prisma` | database | Order entities |
| `themes/admin-theme/*` | frontend | Admin panel theme |
| `themes/product-theme/*` | frontend | Customer menu theme |
| `themes/example-theme/*` | frontend | Reference theme |
| `locales/tr/*.json` | i18n | Turkish translations |
| `locales/en/*.json` | i18n | English translations |

## Files to Reference

These reference documents define the implementation standards:

| File | Pattern to Copy |
|------|----------------|
| `CONSTRAINTS.md` | Critical rules and anti-patterns to avoid |
| `MVP_SCOPE.md` | Exact feature scope and tier limits |
| `MODULE_SYSTEM.md` | Module lifecycle and activation patterns |
| `DATABASE_SCHEMA.md` | Entity relationships and multi-tenancy model |
| `SYSTEM_DESIGN.md` | C4 architecture and request lifecycle |
| `API_CONTRACTS.md` | REST conventions and endpoint specifications |
| `SECURITY_MODEL.md` | 5-layer security and JWT implementation |
| `CODING_STANDARDS.md` | TypeScript conventions and naming |
| `TESTING_STRATEGY.md` | Test pyramid and coverage targets |
| `FRONTEND_ARCHITECTURE.md` | EJS/Alpine.js patterns |
| `COMPONENT_PATTERNS.md` | WCAG 2.1 and design tokens |

## Patterns to Follow

### Module Structure Pattern

From `MODULE_SYSTEM.md`:

```
src/modules/{module-name}/
├── module.json             # Module manifest
├── index.ts                # Public exports
├── {name}.module.ts        # Module definition
├── {name}.controller.ts    # HTTP handlers
├── {name}.service.ts       # Business logic
├── {name}.repository.ts    # Data access
├── {name}.schema.ts        # Zod validation
├── {name}.types.ts         # TypeScript types
├── {name}.routes.ts        # Route definitions
├── {name}.events.ts        # Event handlers
├── migrations/             # Module migrations
├── seeds/                  # Seed data
└── __tests__/              # Tests
```

**Key Points:**
- Every module must have `module.json` manifest
- Public API exported only from `index.ts`
- No direct imports between modules (event-driven communication)
- Each module self-contained with own routes/views/services

### Multi-Tenancy Pattern

From `DATABASE_SCHEMA.md`:

```typescript
// EVERY query must include organizationId
async findAll(orgId: string): Promise<Menu[]> {
  return this.prisma.menu.findMany({
    where: {
      organizationId: orgId,  // MANDATORY
      deletedAt: null,        // Soft delete
    },
  });
}
```

**Key Points:**
- `organizationId` required on all tenant-scoped queries
- Middleware sets `req.organization` from JWT
- BaseService automatically adds tenant filter
- Never use `findUnique` without org verification

### Service Pattern

From `CODING_STANDARDS.md`:

```typescript
@injectable()
export class MenuService extends BaseService<Menu> {
  constructor(
    @inject('PrismaClient') private prisma: PrismaClient,
    @inject(EventService) private events: EventService,
  ) {
    super();
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
      data: { ...data, organizationId: orgId },
    });

    await this.events.emit('menu.created', { menuId: menu.id, orgId });
    return menu;
  }
}
```

**Key Points:**
- Extend BaseService for common CRUD operations
- Use dependency injection with tsyringe
- Always throw AppException for errors
- Emit events for cross-module communication

### Controller Pattern

From `CODING_STANDARDS.md`:

```typescript
@JsonController('/api/v1/menus')
@injectable()
export class MenuController extends BaseController {
  @Get('/')
  @Authorized(['menu.view'])
  async list(
    @CurrentOrg() org: Organization,
    @QueryParams() query: ListMenusQuery,
  ): Promise<ApiResponse<Menu[]>> {
    const menus = await this.menuService.findAll(org.id, query);
    return this.success(menus);
  }
}
```

**Key Points:**
- Use `@Authorized` decorator for permission checks
- Extract org from `@CurrentOrg()` decorator
- Return consistent `ApiResponse` format
- Validate input with Zod schemas

### Error Handling Pattern

From `CODING_STANDARDS.md`:

```typescript
export class AppException extends Error {
  constructor(
    public readonly code: string,
    public readonly statusCode: number = 400,
    public readonly details?: Record<string, unknown>,
  ) {
    super(code);
  }

  static notFound(resource: string, id?: string): AppException {
    return new AppException(
      `${resource.toUpperCase()}_NOT_FOUND`,
      404,
      { resource, id }
    );
  }
}

// Usage
throw new AppException('MENU_NOT_FOUND', 404);
throw AppException.notFound('Menu', menuId);
```

**Key Points:**
- Always use AppException, never raw Error
- Include error code for i18n
- Use factory methods for common errors
- Global error middleware handles all exceptions

## Requirements

### Functional Requirements

1. **Authentication System**
   - Description: JWT-based auth with access (15min) and refresh (7day) tokens
   - Acceptance: Users can register, login, logout, reset password, verify email

2. **Multi-Tenant Organizations**
   - Description: Complete tenant isolation with organizationId on all data
   - Acceptance: Data from org A never visible to org B, verified through tests

3. **User & Role Management**
   - Description: RBAC with predefined roles (owner, manager, staff, viewer)
   - Acceptance: Users can be invited, roles assigned, permissions enforced

4. **Dynamic Module System**
   - Description: WordPress-like module loading with manifest-based configuration
   - Acceptance: Modules can be installed/activated/deactivated without restart

5. **Digital Menu Management**
   - Description: Full CRUD for menus, categories, products with variants/modifiers
   - Acceptance: Menus can be created, published, QR codes generated

6. **Order Management**
   - Description: Cart system, order placement, status workflow
   - Acceptance: Customers can place orders, staff can manage status

7. **Subscription & Plan Management**
   - Description: 5 tiers (Free, Starter, Professional, Business, Enterprise)
   - Acceptance: Feature gating works, limits enforced per plan

8. **Admin Dashboard**
   - Description: EJS-rendered admin panel with Tailwind/Alpine.js
   - Acceptance: Responsive, WCAG 2.1 AA compliant, dark mode support

9. **Public Menu Display**
   - Description: Customer-facing menu via QR code
   - Acceptance: Mobile-responsive, fast loading (<3s), works offline-ish

10. **Internationalization**
    - Description: TR/EN language support via i18next
    - Acceptance: All UI text translatable, language switchable

### Edge Cases

1. **Concurrent Modifications** - Use optimistic locking with version field
2. **Rate Limiting Exceeded** - Return 429 with retry-after header
3. **Invalid JWT** - Return 401, clear refresh token cookie
4. **Tenant Not Found** - Return 404, log potential security issue
5. **Module Dependency Missing** - Prevent activation, return clear error
6. **Plan Limit Exceeded** - Block action, show upgrade prompt
7. **File Upload Failure** - Retry with exponential backoff, cleanup partial
8. **Database Connection Lost** - Graceful degradation, health check failure

## Implementation Notes

### DO
- Follow the module structure pattern from `MODULE_SYSTEM.md`
- Use `@/` import aliases for all internal imports
- Include `organizationId` in EVERY tenant-scoped query
- Use `@Authorized` decorator on ALL protected endpoints
- Implement soft delete with `deletedAt` timestamp
- Use Zod for ALL input validation
- Emit events for cross-module communication
- Write tests alongside code (80% coverage minimum)
- Use JSDoc comments on public methods
- Follow conventional commits format

### DON'T
- Import directly from module internal files (use index.ts)
- Use `any` type (TypeScript strict mode)
- Use `console.log` (use structured logger)
- Delete data physically (soft delete only)
- Store secrets in code (use environment variables)
- Create circular dependencies between modules
- Use raw SQL except for performance-critical cases
- Skip tenant isolation even in "obvious" cases
- Implement stub modules beyond interfaces
- Add features not in MVP scope

## Development Environment

### Start Services

```bash
# Start PostgreSQL (via Docker or local)
docker run -d --name pg -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Start Redis (via Docker or local)
docker run -d --name redis -p 6379:6379 redis:7

# Install dependencies
npm install

# Setup database
npm run prisma:migrate

# Start development server
npm run dev
```

### Service URLs
- API: http://localhost:3000
- Admin: http://localhost:3000/admin
- Prisma Studio: http://localhost:5555

### Required Environment Variables
```bash
NODE_ENV=development
PORT=3000
APP_DOMAIN=e-menum.net
DATABASE_URL=postgresql://postgres:password@localhost:5432/emenum
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-256-bit-secret
JWT_REFRESH_SECRET=your-refresh-secret
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d
```

## Success Criteria

The task is complete when:

1. [ ] Project structure matches specification in MODULE_SYSTEM.md
2. [ ] All 8 core modules implemented and functional
3. [ ] Menu module fully implemented with CRUD operations
4. [ ] Order module fully implemented with status workflow
5. [ ] Advanced-example module provides complete reference
6. [ ] All 12+ stub modules have interface definitions
7. [ ] 3 themes implemented (admin, product, example)
8. [ ] Authentication works with JWT access/refresh tokens
9. [ ] Authorization enforces RBAC/ABAC permissions
10. [ ] Multi-tenancy verified (cross-tenant data isolation)
11. [ ] API follows REST conventions with versioning
12. [ ] i18n working for TR and EN languages
13. [ ] Test coverage meets 80% minimum
14. [ ] No ESLint errors or TypeScript strict mode violations
15. [ ] Database migrations run successfully
16. [ ] Development environment starts with npm run dev

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| Auth Service Tests | `src/modules/_core/auth/__tests__/auth.service.spec.ts` | Login, register, token refresh, password reset |
| Menu Service Tests | `src/modules/menu/__tests__/menu.service.spec.ts` | CRUD operations, tenant isolation |
| Order Service Tests | `src/modules/order/__tests__/order.service.spec.ts` | Cart, order creation, status transitions |
| Permission Service Tests | `src/core/services/__tests__/permission.service.spec.ts` | CASL ability building |
| Module Loader Tests | `src/modules/_core/module-loader/__tests__/module-loader.service.spec.ts` | Install, activate, deactivate |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Auth Flow | auth ↔ user ↔ organization | Complete registration → login → token refresh flow |
| Menu Operations | menu ↔ media ↔ organization | Menu CRUD with image upload |
| Order Flow | order ↔ menu ↔ notification | Cart → order → status update → notification |
| Module Activation | module-loader ↔ all modules | Module enable/disable without restart |
| Multi-tenancy | all modules | Cross-tenant data isolation |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Owner Registration | 1. Register 2. Verify email 3. Create org 4. Access dashboard | Full access to admin panel |
| Menu Creation | 1. Login 2. Create menu 3. Add categories 4. Add products 5. Publish | Menu visible via QR code |
| Customer Order | 1. Scan QR 2. Browse menu 3. Add to cart 4. Place order | Order appears in admin panel |
| Module Management | 1. Login as admin 2. View modules 3. Activate order module | Order features become available |

### Browser Verification (if frontend)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| Admin Dashboard | `http://localhost:3000/admin` | Responsive, dark mode, sidebar navigation |
| Menu Editor | `http://localhost:3000/admin/menus` | Drag-drop sorting, image upload |
| Public Menu | `http://localhost:3000/m/:slug` | Mobile responsive, category nav, cart |
| Login Page | `http://localhost:3000/auth/login` | Form validation, error messages |

### Database Verification (if applicable)
| Check | Query/Command | Expected |
|-------|---------------|----------|
| Migration Status | `npx prisma migrate status` | All migrations applied |
| Seed Data | `npx prisma db seed` | Default plans, allergens, roles created |
| Tenant Isolation | Query menus without orgId | Should return error or empty |

### QA Sign-off Requirements
- [ ] All unit tests pass (80%+ coverage)
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Browser verification complete for all pages
- [ ] Database state verified (migrations, seeds)
- [ ] No regressions in existing functionality
- [ ] Code follows established patterns (CONSTRAINTS.md)
- [ ] No security vulnerabilities (tenant isolation verified)
- [ ] Performance acceptable (API p95 < 200ms)
- [ ] i18n working for TR and EN
- [ ] WCAG 2.1 AA compliance verified
- [ ] KVKK/GDPR compliance verified (PII handling, data deletion, consent)
- [ ] Documentation updated (README, API docs)

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
1. Project setup with TypeScript, ESLint, Prettier
2. Core kernel implementation (bootstrap, DI, module loader)
3. Base classes (BaseController, BaseService, BaseRepository)
4. Middleware stack (auth, tenant, permission, error)
5. Database schema (base.prisma, core.prisma)
6. Auth module
7. Organization module
8. User module

### Phase 2: Core Modules (Week 2-3)
1. Branch module
2. Media module
3. Notification module
4. Subscription module
5. Module loader admin interface
6. Admin theme (basic)

### Phase 3: Menu Module (Week 3-5)
1. Menu CRUD
2. Category management
3. Product management with variants/modifiers
4. Image upload integration
5. QR code generation
6. Public menu display (product theme)

### Phase 4: Order Module (Week 5-7)
1. Cart system
2. Order placement
3. Order management (admin)
4. Status workflow
5. Notifications integration

### Phase 5: Polish & Testing (Week 7-9)
1. Advanced-example module
2. Example theme
3. Stub module interfaces
4. Comprehensive testing
5. Documentation
6. CI/CD pipeline
7. Deployment configuration

### Phase 6: QA & Launch (Week 9-10)
1. QA verification
2. Performance testing
3. Security audit
4. Bug fixes
5. Final deployment

---

*This specification defines the complete E-Menum platform implementation. All development must follow the patterns and constraints defined in the reference documents.*
