# E-Menum Testing Strategy

> **Auto-Claude Testing Document**  
> Test pyramid, coverage targets, mocking strategy, test patterns.  
> Son Güncelleme: 2026-01-31

---

## 1. TESTING PHILOSOPHY

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Test Behavior, Not Implementation** | Test what code does, not how |
| **Fast Feedback Loop** | Unit tests < 10ms, suite < 60s |
| **Deterministic** | Same input = same result, always |
| **Isolated** | Tests don't affect each other |
| **Maintainable** | Tests are code, treat them well |

### 1.2 Test Pyramid

```
                    ┌───────────┐
                    │    E2E    │  ~10%  (Critical paths only)
                    │   Tests   │  Slow, expensive, high confidence
                   ┌┴───────────┴┐
                   │ Integration │  ~30%  (API, DB interactions)
                   │    Tests    │  Medium speed, real dependencies
                  ┌┴─────────────┴┐
                  │     Unit      │  ~60%  (Business logic)
                  │     Tests     │  Fast, isolated, comprehensive
                  └───────────────┘

Execution Time Budget:
├── Unit tests:        < 30 seconds total
├── Integration tests: < 2 minutes total
└── E2E tests:         < 5 minutes total
```

---

## 2. COVERAGE TARGETS

### 2.1 Module Coverage Requirements

| Module Type | Unit | Integration | E2E | Overall |
|-------------|:----:|:-----------:|:---:|:-------:|
| Core (kernel, base) | 90% | 80% | - | 85% |
| System (auth, users) | 85% | 75% | Critical | 80% |
| Feature (menu, orders) | 80% | 60% | Critical | 75% |
| AI modules | 70% | 50% | - | 60% |
| Utilities | 90% | - | - | 90% |

### 2.2 Coverage Metrics

```
Coverage Types:

├── Line Coverage      # Minimum 80%
├── Branch Coverage    # Minimum 75%
├── Function Coverage  # Minimum 85%
└── Statement Coverage # Minimum 80%

Exclusions (from coverage):
├── Type definitions (.d.ts)
├── Configuration files
├── Migration files
├── Mock/fixture files
└── Index barrel files
```

### 2.3 Critical Path Coverage

```
Must Have E2E Tests:

Authentication:
├── User registration
├── User login
├── Token refresh
├── Password reset
└── Logout

Core Flows:
├── Create organization → Create menu → Add products → Publish
├── QR code generation → Public menu view
├── Order creation → Status updates → Completion
├── Subscription upgrade/downgrade
└── AI content generation (mocked provider)
```

---

## 3. TEST STRUCTURE

### 3.1 File Organization

```
src/
├── modules/
│   └── menu/
│       ├── menu.service.ts
│       ├── menu.service.spec.ts      # Unit tests (co-located)
│       ├── menu.controller.spec.ts   # Unit tests
│       └── __tests__/
│           ├── menu.integration.spec.ts
│           └── menu.e2e.spec.ts
│
├── core/
│   └── services/
│       ├── auth.service.ts
│       └── auth.service.spec.ts
│
└── __tests__/                        # Global test utilities
    ├── setup.ts                      # Global setup
    ├── teardown.ts                   # Global teardown
    ├── helpers/
    │   ├── test-db.ts               # Database utilities
    │   ├── test-auth.ts             # Auth helpers
    │   └── factories/               # Test data factories
    │       ├── user.factory.ts
    │       ├── menu.factory.ts
    │       └── index.ts
    └── mocks/
        ├── prisma.mock.ts
        ├── redis.mock.ts
        └── ai-provider.mock.ts
```

### 3.2 Test File Naming

```
Naming Convention:

Unit tests:       {name}.spec.ts
Integration:      {name}.integration.spec.ts
E2E tests:        {name}.e2e.spec.ts

Examples:
├── menu.service.spec.ts
├── menu.integration.spec.ts
├── menu.e2e.spec.ts
├── auth.controller.spec.ts
└── order-flow.e2e.spec.ts
```

---

## 4. UNIT TESTING

### 4.1 Unit Test Structure

```typescript
// menu.service.spec.ts

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MenuService } from './menu.service';
import { createMockPrisma } from '@/__tests__/mocks/prisma.mock';
import { menuFactory } from '@/__tests__/helpers/factories';

describe('MenuService', () => {
  let service: MenuService;
  let mockPrisma: ReturnType<typeof createMockPrisma>;
  
  beforeEach(() => {
    mockPrisma = createMockPrisma();
    service = new MenuService(mockPrisma);
  });
  
  describe('findAll', () => {
    it('should return menus for organization', async () => {
      // Arrange
      const orgId = 'org_123';
      const menus = [menuFactory.build(), menuFactory.build()];
      mockPrisma.menu.findMany.mockResolvedValue(menus);
      
      // Act
      const result = await service.findAll(orgId);
      
      // Assert
      expect(result).toHaveLength(2);
      expect(mockPrisma.menu.findMany).toHaveBeenCalledWith({
        where: { organizationId: orgId, deletedAt: null },
        orderBy: { sortOrder: 'asc' },
      });
    });
    
    it('should apply filters when provided', async () => {
      // Arrange
      const orgId = 'org_123';
      const filters = { isPublished: true };
      mockPrisma.menu.findMany.mockResolvedValue([]);
      
      // Act
      await service.findAll(orgId, filters);
      
      // Assert
      expect(mockPrisma.menu.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({ isPublished: true }),
        })
      );
    });
  });
  
  describe('create', () => {
    it('should create menu with generated slug', async () => {
      // Arrange
      const orgId = 'org_123';
      const input = { name: 'Test Menu' };
      const created = menuFactory.build({ ...input, organizationId: orgId });
      mockPrisma.menu.create.mockResolvedValue(created);
      
      // Act
      const result = await service.create(orgId, input);
      
      // Assert
      expect(result.name).toBe('Test Menu');
      expect(mockPrisma.menu.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          name: 'Test Menu',
          slug: 'test-menu',
          organizationId: orgId,
        }),
      });
    });
    
    it('should throw if slug already exists', async () => {
      // Arrange
      const orgId = 'org_123';
      const input = { name: 'Test', slug: 'existing-slug' };
      mockPrisma.menu.findFirst.mockResolvedValue(menuFactory.build());
      
      // Act & Assert
      await expect(service.create(orgId, input))
        .rejects
        .toThrow('MENU_ALREADY_EXISTS');
    });
  });
  
  describe('publish', () => {
    it('should publish unpublished menu', async () => {
      // Arrange
      const menu = menuFactory.build({ isPublished: false });
      mockPrisma.menu.findFirst.mockResolvedValue(menu);
      mockPrisma.menu.update.mockResolvedValue({ ...menu, isPublished: true });
      
      // Act
      const result = await service.publish(menu.id, menu.organizationId);
      
      // Assert
      expect(result.isPublished).toBe(true);
    });
    
    it('should throw if menu not found', async () => {
      // Arrange
      mockPrisma.menu.findFirst.mockResolvedValue(null);
      
      // Act & Assert
      await expect(service.publish('invalid', 'org_123'))
        .rejects
        .toThrow('MENU_NOT_FOUND');
    });
  });
});
```

### 4.2 Unit Test Patterns

```typescript
// Pattern: Arrange-Act-Assert (AAA)
it('should do something', async () => {
  // Arrange - Setup test data and mocks
  const input = createTestInput();
  mockService.method.mockResolvedValue(expected);
  
  // Act - Execute the code under test
  const result = await service.doSomething(input);
  
  // Assert - Verify the outcome
  expect(result).toEqual(expected);
});

// Pattern: Given-When-Then (BDD style)
describe('when user is not authenticated', () => {
  it('then should return 401', async () => {
    // Given
    const request = createRequest({ token: null });
    
    // When
    const response = await controller.handle(request);
    
    // Then
    expect(response.status).toBe(401);
  });
});

// Pattern: Table-driven tests
describe('validatePrice', () => {
  const cases = [
    { input: 100, expected: true },
    { input: 0, expected: false },
    { input: -10, expected: false },
    { input: 0.01, expected: true },
  ];
  
  it.each(cases)('should return $expected for $input', ({ input, expected }) => {
    expect(validatePrice(input)).toBe(expected);
  });
});

// Pattern: Test edge cases explicitly
describe('edge cases', () => {
  it('should handle empty array', async () => {
    const result = await service.process([]);
    expect(result).toEqual([]);
  });
  
  it('should handle null input', async () => {
    await expect(service.process(null)).rejects.toThrow();
  });
  
  it('should handle maximum length', async () => {
    const input = 'a'.repeat(1000);
    const result = await service.process(input);
    expect(result.length).toBeLessThanOrEqual(1000);
  });
});
```

---

## 5. INTEGRATION TESTING

### 5.1 Integration Test Structure

```typescript
// menu.integration.spec.ts

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { createTestApp, TestApp } from '@/__tests__/helpers/test-app';
import { createTestDb, TestDb } from '@/__tests__/helpers/test-db';
import { userFactory, orgFactory, menuFactory } from '@/__tests__/helpers/factories';

describe('Menu API Integration', () => {
  let app: TestApp;
  let db: TestDb;
  let authToken: string;
  let org: Organization;
  
  beforeAll(async () => {
    db = await createTestDb();
    app = await createTestApp(db);
  });
  
  afterAll(async () => {
    await db.cleanup();
    await app.close();
  });
  
  beforeEach(async () => {
    await db.reset(); // Truncate tables
    
    // Setup test data
    org = await db.create(orgFactory.build());
    const user = await db.create(userFactory.build({ organizationId: org.id }));
    authToken = await app.getAuthToken(user);
  });
  
  describe('GET /api/v1/menus', () => {
    it('should return organization menus', async () => {
      // Setup
      await db.create(menuFactory.build({ organizationId: org.id }));
      await db.create(menuFactory.build({ organizationId: org.id }));
      
      // Execute
      const response = await app.request()
        .get('/api/v1/menus')
        .set('Authorization', `Bearer ${authToken}`);
      
      // Verify
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveLength(2);
    });
    
    it('should not return other organization menus', async () => {
      // Setup - Create menu for different org
      const otherOrg = await db.create(orgFactory.build());
      await db.create(menuFactory.build({ organizationId: otherOrg.id }));
      
      // Execute
      const response = await app.request()
        .get('/api/v1/menus')
        .set('Authorization', `Bearer ${authToken}`);
      
      // Verify - Should be empty (tenant isolation)
      expect(response.body.data).toHaveLength(0);
    });
    
    it('should require authentication', async () => {
      const response = await app.request()
        .get('/api/v1/menus');
      
      expect(response.status).toBe(401);
    });
  });
  
  describe('POST /api/v1/menus', () => {
    it('should create menu with valid data', async () => {
      const input = { name: 'New Menu', description: 'Test' };
      
      const response = await app.request()
        .post('/api/v1/menus')
        .set('Authorization', `Bearer ${authToken}`)
        .send(input);
      
      expect(response.status).toBe(201);
      expect(response.body.data.name).toBe('New Menu');
      expect(response.body.data.slug).toBe('new-menu');
      
      // Verify in database
      const menu = await db.findOne('menu', { id: response.body.data.id });
      expect(menu).toBeTruthy();
      expect(menu.organizationId).toBe(org.id);
    });
    
    it('should reject invalid data', async () => {
      const input = { name: '' }; // Empty name
      
      const response = await app.request()
        .post('/api/v1/menus')
        .set('Authorization', `Bearer ${authToken}`)
        .send(input);
      
      expect(response.status).toBe(400);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });
    
    it('should require menu.create permission', async () => {
      // Create user without permission
      const viewer = await db.create(userFactory.build({ 
        organizationId: org.id,
        role: 'viewer',
      }));
      const viewerToken = await app.getAuthToken(viewer);
      
      const response = await app.request()
        .post('/api/v1/menus')
        .set('Authorization', `Bearer ${viewerToken}`)
        .send({ name: 'Test' });
      
      expect(response.status).toBe(403);
    });
  });
});
```

### 5.2 Database Testing Utilities

```typescript
// __tests__/helpers/test-db.ts

import { PrismaClient } from '@prisma/client';
import { execSync } from 'child_process';

export interface TestDb {
  prisma: PrismaClient;
  create<T>(data: T): Promise<T>;
  findOne(model: string, where: object): Promise<any>;
  reset(): Promise<void>;
  cleanup(): Promise<void>;
}

export async function createTestDb(): Promise<TestDb> {
  // Use test database
  const databaseUrl = process.env.TEST_DATABASE_URL;
  
  // Run migrations
  execSync('npx prisma migrate deploy', {
    env: { ...process.env, DATABASE_URL: databaseUrl },
  });
  
  const prisma = new PrismaClient({
    datasources: { db: { url: databaseUrl } },
  });
  
  await prisma.$connect();
  
  return {
    prisma,
    
    async create(data) {
      const model = data.constructor.name.toLowerCase();
      return prisma[model].create({ data });
    },
    
    async findOne(model, where) {
      return prisma[model].findFirst({ where });
    },
    
    async reset() {
      // Truncate all tables in correct order
      const tables = ['orderItem', 'order', 'product', 'category', 'menu', 'user', 'organization'];
      
      for (const table of tables) {
        await prisma.$executeRawUnsafe(`TRUNCATE TABLE "${table}" CASCADE`);
      }
    },
    
    async cleanup() {
      await prisma.$disconnect();
    },
  };
}
```

### 5.3 Test App Helper

```typescript
// __tests__/helpers/test-app.ts

import { Express } from 'express';
import supertest from 'supertest';
import { createApp } from '@/app';
import { generateTestToken } from './test-auth';

export interface TestApp {
  request(): supertest.SuperTest<supertest.Test>;
  getAuthToken(user: User): Promise<string>;
  close(): Promise<void>;
}

export async function createTestApp(db: TestDb): Promise<TestApp> {
  const app = await createApp({
    database: db.prisma,
    disableRateLimit: true,
    disableAuth: false,
  });
  
  return {
    request() {
      return supertest(app);
    },
    
    async getAuthToken(user) {
      return generateTestToken(user);
    },
    
    async close() {
      // Cleanup resources
    },
  };
}
```

---

## 6. E2E TESTING

### 6.1 E2E Test Structure

```typescript
// order-flow.e2e.spec.ts

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { chromium, Browser, Page } from 'playwright';

describe('Order Flow E2E', () => {
  let browser: Browser;
  let page: Page;
  
  beforeAll(async () => {
    browser = await chromium.launch();
  });
  
  afterAll(async () => {
    await browser.close();
  });
  
  beforeEach(async () => {
    page = await browser.newPage();
  });
  
  afterEach(async () => {
    await page.close();
  });
  
  it('should complete full order flow', async () => {
    // 1. Customer scans QR and views menu
    await page.goto('/m/test-restaurant/ana-menu');
    await expect(page.locator('h1')).toContainText('Ana Menü');
    
    // 2. Browse products
    await page.click('[data-testid="category-yemekler"]');
    await expect(page.locator('[data-testid="product-list"]')).toBeVisible();
    
    // 3. Add item to cart
    await page.click('[data-testid="product-kofte"]');
    await page.click('[data-testid="add-to-cart"]');
    await expect(page.locator('[data-testid="cart-count"]')).toHaveText('1');
    
    // 4. View cart
    await page.click('[data-testid="view-cart"]');
    await expect(page.locator('[data-testid="cart-total"]')).toContainText('₺');
    
    // 5. Submit order
    await page.fill('[data-testid="table-number"]', 'A5');
    await page.click('[data-testid="submit-order"]');
    
    // 6. Verify confirmation
    await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="order-number"]')).toHaveText(/ORD-\d+/);
  });
  
  it('should show order status updates', async () => {
    // Setup: Create order first
    const orderNumber = await createTestOrder();
    
    // Navigate to order status page
    await page.goto(`/order/${orderNumber}`);
    
    // Verify initial status
    await expect(page.locator('[data-testid="order-status"]')).toHaveText('Beklemede');
    
    // Simulate status change (via API)
    await updateOrderStatus(orderNumber, 'preparing');
    
    // Verify UI updates (with polling/websocket)
    await page.waitForSelector('[data-testid="order-status"]:has-text("Hazırlanıyor")');
  });
});
```

### 6.2 E2E Test Helpers

```typescript
// __tests__/helpers/e2e-helpers.ts

import { Page } from 'playwright';

export async function login(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', email);
  await page.fill('[data-testid="password"]', password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}

export async function createTestOrder(): Promise<string> {
  // Call API to create test order
  const response = await fetch('/api/v1/test/orders', {
    method: 'POST',
    headers: { 'X-Test-Mode': 'true' },
  });
  const data = await response.json();
  return data.orderNumber;
}

export async function seedTestData(): Promise<void> {
  await fetch('/api/v1/test/seed', {
    method: 'POST',
    headers: { 'X-Test-Mode': 'true' },
  });
}

export async function cleanupTestData(): Promise<void> {
  await fetch('/api/v1/test/cleanup', {
    method: 'POST',
    headers: { 'X-Test-Mode': 'true' },
  });
}
```

---

## 7. MOCKING STRATEGIES

### 7.1 Prisma Mock

```typescript
// __tests__/mocks/prisma.mock.ts

import { vi } from 'vitest';
import { PrismaClient } from '@prisma/client';
import { DeepMockProxy, mockDeep } from 'vitest-mock-extended';

export type MockPrisma = DeepMockProxy<PrismaClient>;

export function createMockPrisma(): MockPrisma {
  return mockDeep<PrismaClient>();
}

// Usage in tests:
const mockPrisma = createMockPrisma();
mockPrisma.menu.findMany.mockResolvedValue([/* ... */]);
mockPrisma.menu.create.mockResolvedValue(/* ... */);
```

### 7.2 External Service Mocks

```typescript
// __tests__/mocks/ai-provider.mock.ts

import { vi } from 'vitest';
import type { AIProvider } from '@/modules/ai/types';

export function createMockAIProvider(): AIProvider {
  return {
    generateContent: vi.fn().mockResolvedValue({
      content: 'Generated content',
      tokens: 100,
    }),
    
    generateImage: vi.fn().mockResolvedValue({
      url: 'https://example.com/image.png',
      credits: 10,
    }),
    
    translate: vi.fn().mockImplementation((text, targetLang) => 
      Promise.resolve({ translated: `[${targetLang}] ${text}` })
    ),
  };
}

// __tests__/mocks/redis.mock.ts

export function createMockRedis() {
  const store = new Map<string, string>();
  
  return {
    get: vi.fn((key: string) => Promise.resolve(store.get(key))),
    set: vi.fn((key: string, value: string) => {
      store.set(key, value);
      return Promise.resolve('OK');
    }),
    del: vi.fn((key: string) => {
      store.delete(key);
      return Promise.resolve(1);
    }),
    clear: () => store.clear(),
  };
}
```

### 7.3 HTTP Mocks (for integration tests)

```typescript
// __tests__/mocks/http.mock.ts

import { vi } from 'vitest';
import nock from 'nock';

export function mockExternalAPIs() {
  // Mock Anthropic API
  nock('https://api.anthropic.com')
    .post('/v1/messages')
    .reply(200, {
      content: [{ text: 'Mocked AI response' }],
      usage: { input_tokens: 10, output_tokens: 50 },
    });
  
  // Mock Unsplash API
  nock('https://api.unsplash.com')
    .get('/search/photos')
    .query(true)
    .reply(200, {
      results: [
        { urls: { regular: 'https://images.unsplash.com/test.jpg' } },
      ],
    });
  
  // Mock Iyzico
  nock('https://api.iyzico.com')
    .post('/payment')
    .reply(200, {
      status: 'success',
      paymentId: 'pay_123',
    });
}

export function clearMocks() {
  nock.cleanAll();
}
```

---

## 8. TEST DATA FACTORIES

### 8.1 Factory Pattern

```typescript
// __tests__/helpers/factories/user.factory.ts

import { faker } from '@faker-js/faker';
import { User } from '@prisma/client';

interface UserFactoryOptions {
  organizationId?: string;
  role?: string;
  status?: string;
}

export const userFactory = {
  build(overrides: Partial<User> = {}): User {
    return {
      id: `usr_${faker.string.alphanumeric(20)}`,
      email: faker.internet.email(),
      passwordHash: '$2b$12$...', // Pre-hashed "password123"
      firstName: faker.person.firstName(),
      lastName: faker.person.lastName(),
      avatar: null,
      phone: null,
      status: 'active',
      emailVerifiedAt: new Date(),
      lastLoginAt: null,
      organizationId: null,
      createdAt: new Date(),
      updatedAt: new Date(),
      deletedAt: null,
      ...overrides,
    };
  },
  
  buildMany(count: number, overrides: Partial<User> = {}): User[] {
    return Array.from({ length: count }, () => this.build(overrides));
  },
  
  // Preset configurations
  owner(orgId: string): User {
    return this.build({ organizationId: orgId, role: 'owner' });
  },
  
  staff(orgId: string): User {
    return this.build({ organizationId: orgId, role: 'staff' });
  },
  
  unverified(): User {
    return this.build({ emailVerifiedAt: null, status: 'pending' });
  },
};
```

### 8.2 Related Factories

```typescript
// __tests__/helpers/factories/menu.factory.ts

import { faker } from '@faker-js/faker';
import { Menu, Category, Product } from '@prisma/client';

export const menuFactory = {
  build(overrides: Partial<Menu> = {}): Menu {
    const name = overrides.name || faker.commerce.department();
    return {
      id: `mnu_${faker.string.alphanumeric(20)}`,
      organizationId: `org_${faker.string.alphanumeric(20)}`,
      name,
      slug: name.toLowerCase().replace(/\s+/g, '-'),
      description: faker.lorem.sentence(),
      isPublished: false,
      publishedAt: null,
      isDefault: false,
      themeId: null,
      settings: {},
      sortOrder: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      deletedAt: null,
      ...overrides,
    };
  },
  
  published(overrides: Partial<Menu> = {}): Menu {
    return this.build({
      isPublished: true,
      publishedAt: new Date(),
      ...overrides,
    });
  },
};

export const categoryFactory = {
  build(overrides: Partial<Category> = {}): Category {
    return {
      id: `cat_${faker.string.alphanumeric(20)}`,
      organizationId: `org_${faker.string.alphanumeric(20)}`,
      menuId: `mnu_${faker.string.alphanumeric(20)}`,
      parentId: null,
      name: faker.commerce.department(),
      slug: faker.helpers.slugify(faker.commerce.department()),
      description: faker.lorem.sentence(),
      image: null,
      isActive: true,
      sortOrder: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      deletedAt: null,
      ...overrides,
    };
  },
};

export const productFactory = {
  build(overrides: Partial<Product> = {}): Product {
    return {
      id: `prd_${faker.string.alphanumeric(20)}`,
      organizationId: `org_${faker.string.alphanumeric(20)}`,
      categoryId: `cat_${faker.string.alphanumeric(20)}`,
      name: faker.commerce.productName(),
      slug: faker.helpers.slugify(faker.commerce.productName()),
      description: faker.commerce.productDescription(),
      shortDescription: faker.lorem.sentence(),
      basePrice: faker.number.float({ min: 10, max: 500, precision: 0.01 }),
      currency: 'TRY',
      image: null,
      gallery: [],
      isActive: true,
      isAvailable: true,
      isFeatured: false,
      isChefRecommended: false,
      preparationTime: faker.number.int({ min: 5, max: 30 }),
      calories: faker.number.int({ min: 100, max: 1000 }),
      spicyLevel: faker.number.int({ min: 0, max: 5 }),
      tags: [],
      sortOrder: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
      deletedAt: null,
      ...overrides,
    };
  },
  
  unavailable(overrides: Partial<Product> = {}): Product {
    return this.build({ isAvailable: false, ...overrides });
  },
  
  featured(overrides: Partial<Product> = {}): Product {
    return this.build({ isFeatured: true, ...overrides });
  },
};
```

### 8.3 Factory Index

```typescript
// __tests__/helpers/factories/index.ts

export { userFactory } from './user.factory';
export { orgFactory } from './organization.factory';
export { menuFactory, categoryFactory, productFactory } from './menu.factory';
export { orderFactory, orderItemFactory } from './order.factory';

// Convenience: Create related entities
export async function createMenuWithProducts(
  db: TestDb,
  orgId: string,
  productCount: number = 5,
): Promise<{ menu: Menu; categories: Category[]; products: Product[] }> {
  const menu = await db.create(menuFactory.build({ organizationId: orgId }));
  
  const category = await db.create(categoryFactory.build({
    organizationId: orgId,
    menuId: menu.id,
  }));
  
  const products = await Promise.all(
    productFactory.buildMany(productCount, {
      organizationId: orgId,
      categoryId: category.id,
    }).map(p => db.create(p))
  );
  
  return { menu, categories: [category], products };
}
```

---

## 9. CI/CD INTEGRATION

### 9.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml

name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  NODE_VERSION: '20'
  TEST_DATABASE_URL: postgresql://test:test@localhost:5432/emenum_test

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - run: npm ci
      
      - name: Run unit tests
        run: npm run test:unit -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
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
      
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - run: npm ci
      
      - name: Run migrations
        run: npx prisma migrate deploy
      
      - name: Run integration tests
        run: npm run test:integration -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: integration
  
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-results
          path: playwright-report/
```

### 9.2 Test Scripts (package.json)

```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest run --config vitest.unit.config.ts",
    "test:integration": "vitest run --config vitest.integration.config.ts",
    "test:e2e": "playwright test",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest watch",
    "test:ci": "npm run test:unit && npm run test:integration"
  }
}
```

### 9.3 Vitest Configuration

```typescript
// vitest.config.ts

import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.spec.ts'],
    exclude: ['src/**/*.e2e.spec.ts', 'src/**/*.integration.spec.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      exclude: [
        'node_modules',
        'dist',
        '**/*.d.ts',
        '**/__tests__/**',
        '**/index.ts',
      ],
      thresholds: {
        lines: 80,
        branches: 75,
        functions: 85,
        statements: 80,
      },
    },
    setupFiles: ['./src/__tests__/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

// vitest.integration.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.integration.spec.ts'],
    setupFiles: ['./src/__tests__/setup-integration.ts'],
    testTimeout: 30000,
    hookTimeout: 30000,
  },
});
```

---

## 10. TEST DOCUMENTATION

### 10.1 Test Naming Conventions

```typescript
// ✅ GOOD: Descriptive test names
describe('MenuService', () => {
  describe('create', () => {
    it('should create menu with auto-generated slug when not provided');
    it('should throw MENU_ALREADY_EXISTS when slug is taken');
    it('should emit menu.created event after successful creation');
  });
});

// ❌ BAD: Vague test names
describe('MenuService', () => {
  it('works');
  it('test create');
  it('should work correctly');
});
```

### 10.2 Test Documentation Template

```typescript
/**
 * @group unit
 * @module menu
 * 
 * Tests for MenuService business logic.
 * 
 * Coverage:
 * - CRUD operations
 * - Slug generation
 * - Publishing workflow
 * - Event emission
 * 
 * Mocks:
 * - PrismaClient (database)
 * - EventService (events)
 * 
 * @see MenuService
 */
describe('MenuService', () => {
  // ...
});
```

---

*Bu döküman, E-Menum test stratejisini tanımlar. Tüm kod için uygun testler yazılmalıdır.*
