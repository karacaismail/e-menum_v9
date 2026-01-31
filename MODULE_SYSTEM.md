# E-Menum Module System Architecture

> **Auto-Claude Module System Document**  
> Modül mimarisi, lifecycle, yükleme/etkinleştirme mekanizması.  
> WordPress plugin sistemi benzeri, enterprise-ready modül altyapısı.  
> Son Güncelleme: 2026-01-31

---

## 1. MODÜL SİSTEMİ GENEL BAKIŞ

### 1.1 Felsefe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODÜL SİSTEMİ FELSEFESİ                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PRENSİP: "Plugin-like Architecture with Compile-time Safety"              │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  WordPress Plugin Sistemi'nden İlham:                                │ │
│  │  ├── Modüller bağımsız olarak eklenebilir/kaldırılabilir            │ │
│  │  ├── Etkinleştirme/devre dışı bırakma runtime'da                    │ │
│  │  ├── Hook sistemi ile genişletilebilir                              │ │
│  │  └── Merkezi yönetim paneli                                         │ │
│  │                                                                       │ │
│  │  Enterprise Gereksinimler:                                           │ │
│  │  ├── Type-safety (TypeScript)                                       │ │
│  │  ├── Dependency injection                                           │ │
│  │  ├── Graceful degradation                                           │ │
│  │  ├── Hot-reload (development)                                       │ │
│  │  ├── Zero-downtime activation (production)                          │ │
│  │  └── Rollback capability                                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  MODÜL TÜRLERİ:                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  CORE MODULES (Sistem Çekirdeği):                                    │ │
│  │  ├── Her zaman aktif, devre dışı bırakılamaz                        │ │
│  │  ├── Sistemin çalışması için zorunlu                                │ │
│  │  └── auth, organization, user, media, notification, subscription    │ │
│  │                                                                       │ │
│  │  FEATURE MODULES (Özellik Modülleri):                                │ │
│  │  ├── Bağımsız olarak etkinleştirilebilir                            │ │
│  │  ├── Tier-based erişim kontrolü                                     │ │
│  │  └── menu, order, payment, analytics, ai, etc.                      │ │
│  │                                                                       │ │
│  │  THEME MODULES (Tema Modülleri):                                     │ │
│  │  ├── Sadece görsel katman                                           │ │
│  │  ├── Tek aktif tema (admin/product ayrı)                            │ │
│  │  └── admin-theme, product-theme, example-theme                      │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Modül Durumları

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODÜL STATE MACHINE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ┌────────────┐                                      │
│                        │            │                                      │
│          install       │   NOT      │                                      │
│      ┌────────────────►│ INSTALLED  │                                      │
│      │                 │            │                                      │
│      │                 └─────┬──────┘                                      │
│      │                       │ install                                     │
│      │                       ▼                                             │
│      │                 ┌────────────┐                                      │
│      │                 │            │                                      │
│      │                 │ INSTALLED  │◄─────────┐                           │
│      │                 │ (inactive) │          │                           │
│      │                 │            │          │                           │
│      │                 └─────┬──────┘          │                           │
│      │                       │ activate        │ deactivate                │
│      │                       ▼                 │                           │
│   uninstall            ┌────────────┐          │                           │
│      │                 │            │          │                           │
│      │                 │   ACTIVE   │──────────┘                           │
│      │                 │            │                                      │
│      │                 └─────┬──────┘                                      │
│      │                       │ uninstall                                   │
│      │                       ▼                                             │
│      │                 ┌────────────┐                                      │
│      └─────────────────│   NOT      │                                      │
│                        │ INSTALLED  │                                      │
│                        └────────────┘                                      │
│                                                                             │
│  DURUMLAR:                                                                  │
│  ├── NOT_INSTALLED: Modül mevcut değil                                     │
│  ├── INSTALLED: Kurulu ama aktif değil (migrations done, routes yok)      │
│  └── ACTIVE: Tam çalışır durumda (routes registered, events listening)    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MODÜL YAPISI

### 2.1 Klasör Yapısı

```
src/modules/
├── _core/                      # Core modüller (özel prefix)
│   ├── auth/
│   ├── organization/
│   ├── branch/
│   ├── user/
│   ├── media/
│   ├── notification/
│   ├── subscription/
│   └── module-loader/          # Bu modül sistemi
│
├── menu/                       # Feature module: Menu
│   ├── module.json             # Modül manifest
│   ├── index.ts                # Public exports
│   ├── menu.module.ts          # Module definition
│   ├── menu.controller.ts
│   ├── menu.service.ts
│   ├── menu.repository.ts
│   ├── menu.schema.ts
│   ├── menu.types.ts
│   ├── menu.routes.ts
│   ├── menu.events.ts
│   ├── menu.hooks.ts           # Extension points
│   ├── migrations/             # Module-specific migrations
│   │   └── 001_create_tables.sql
│   ├── seeds/                  # Seed data
│   │   └── demo-menu.seed.ts
│   └── __tests__/
│
├── order/                      # Feature module: Order
│   └── ... (same structure)
│
├── _examples/                  # Örnek modüller
│   └── advanced-example/
│       └── ... (reference implementation)
│
└── _stubs/                     # Gelecek modüller için stub
    ├── payment/
    │   ├── module.json
    │   ├── index.ts            # Sadece interface export
    │   └── payment.types.ts    # Sadece type tanımları
    ├── analytics/
    ├── ai/
    └── ...
```

### 2.2 Module Manifest (module.json)

```json
{
  "$schema": "https://e-menum.net/schemas/module-v1.json",
  "id": "menu",
  "name": "Menu Module",
  "version": "1.0.0",
  "description": "Dijital menü oluşturma ve yönetimi",
  
  "type": "feature",
  "category": "core-feature",
  
  "author": {
    "name": "E-Menum Team",
    "email": "dev@e-menum.net"
  },
  
  "compatibility": {
    "platform": ">=1.0.0",
    "node": ">=20.0.0"
  },
  
  "dependencies": {
    "modules": ["auth", "organization", "media"],
    "optional": ["ai"]
  },
  
  "provides": {
    "routes": true,
    "events": ["menu.created", "menu.published", "item.updated"],
    "hooks": ["beforeMenuPublish", "afterItemCreate"],
    "permissions": ["menu:read", "menu:write", "menu:publish"]
  },
  
  "requires": {
    "permissions": ["auth:verify", "organization:read", "media:upload"],
    "events": ["organization.created"]
  },
  
  "tier": {
    "minimum": "free",
    "features": {
      "free": ["basic_menu", "categories", "items"],
      "starter": ["variants", "options", "multi_language"],
      "professional": ["scheduled_visibility", "nutrition"],
      "business": ["versioning", "bulk_import"],
      "enterprise": ["custom_fields", "api_access"]
    }
  },
  
  "lifecycle": {
    "install": "migrations/install.ts",
    "uninstall": "migrations/uninstall.ts",
    "activate": "lifecycle/activate.ts",
    "deactivate": "lifecycle/deactivate.ts",
    "upgrade": "migrations/upgrade.ts"
  },
  
  "admin": {
    "menu": {
      "label": "Menü Yönetimi",
      "icon": "ph-fork-knife",
      "route": "/admin/menus",
      "order": 10
    }
  },
  
  "settings": {
    "schema": "settings.schema.json",
    "defaults": {
      "defaultLocale": "tr",
      "maxCategories": 50,
      "maxItemsPerCategory": 100
    }
  }
}
```

### 2.3 Module Definition (menu.module.ts)

```typescript
import { Module, ModuleMetadata } from '@/core/module-loader';
import { MenuController } from './menu.controller';
import { MenuService } from './menu.service';
import { MenuRepository } from './menu.repository';
import { MenuEventHandlers } from './menu.events';
import { menuRoutes } from './menu.routes';
import manifest from './module.json';

@Module({
  id: 'menu',
  manifest,
})
export class MenuModule {
  
  // Dependency Injection
  static providers = [
    MenuService,
    MenuRepository,
    MenuEventHandlers,
  ];
  
  static controllers = [
    MenuController,
  ];
  
  // Routes registration
  static routes = menuRoutes;
  
  // Lifecycle hooks
  static async onInstall(context: ModuleContext): Promise<void> {
    // Run migrations
    await context.runMigrations(__dirname + '/migrations');
    
    // Seed initial data
    if (context.env === 'development') {
      await context.runSeeds(__dirname + '/seeds');
    }
    
    context.logger.info('Menu module installed');
  }
  
  static async onActivate(context: ModuleContext): Promise<void> {
    // Register routes
    context.registerRoutes(this.routes);
    
    // Subscribe to events
    context.events.on('organization.created', MenuEventHandlers.onOrgCreated);
    
    // Register hooks
    context.hooks.register('menu', this.getHooks());
    
    context.logger.info('Menu module activated');
  }
  
  static async onDeactivate(context: ModuleContext): Promise<void> {
    // Unregister routes
    context.unregisterRoutes(this.routes);
    
    // Unsubscribe from events
    context.events.off('organization.created', MenuEventHandlers.onOrgCreated);
    
    context.logger.info('Menu module deactivated');
  }
  
  static async onUninstall(context: ModuleContext): Promise<void> {
    // Confirm data deletion
    if (!context.options.force) {
      throw new ModuleError('Use --force to delete module data');
    }
    
    // Run down migrations
    await context.rollbackMigrations(__dirname + '/migrations');
    
    context.logger.info('Menu module uninstalled');
  }
  
  // Extension hooks
  static getHooks() {
    return {
      beforeMenuPublish: async (menu: Menu) => menu,
      afterItemCreate: async (item: MenuItem) => item,
      filterMenuItems: async (items: MenuItem[]) => items,
    };
  }
}
```

---

## 3. MODULE LOADER (Core)

### 3.1 Module Loader Service

```typescript
// src/modules/_core/module-loader/module-loader.service.ts

import { Injectable } from '@/core/di';
import { EventBus } from '@/core/events';
import { Logger } from '@/core/logger';
import { PrismaService } from '@/core/database';
import { CacheService } from '@/core/cache';

interface ModuleState {
  id: string;
  status: 'not_installed' | 'installed' | 'active';
  version: string;
  installedAt?: Date;
  activatedAt?: Date;
  config?: Record<string, unknown>;
}

@Injectable()
export class ModuleLoaderService {
  private modules: Map<string, Module> = new Map();
  private states: Map<string, ModuleState> = new Map();
  
  constructor(
    private prisma: PrismaService,
    private events: EventBus,
    private cache: CacheService,
    private logger: Logger,
  ) {}
  
  /**
   * Uygulama başlangıcında çağrılır
   * Tüm aktif modülleri yükler
   */
  async bootstrap(): Promise<void> {
    this.logger.info('Module loader bootstrapping...');
    
    // 1. Core modülleri yükle (her zaman)
    await this.loadCoreModules();
    
    // 2. Veritabanından modül durumlarını al
    await this.loadModuleStates();
    
    // 3. Aktif feature modüllerini yükle
    await this.loadActiveModules();
    
    // 4. Tema modüllerini yükle
    await this.loadThemeModules();
    
    this.logger.info(`Loaded ${this.modules.size} modules`);
  }
  
  /**
   * Modül kurulumu
   */
  async install(moduleId: string): Promise<void> {
    this.logger.info(`Installing module: ${moduleId}`);
    
    const module = await this.discoverModule(moduleId);
    
    // Dependency check
    await this.checkDependencies(module);
    
    // Run install lifecycle
    const context = this.createContext(module);
    await module.onInstall?.(context);
    
    // Update state
    await this.updateState(moduleId, {
      status: 'installed',
      version: module.manifest.version,
      installedAt: new Date(),
    });
    
    this.events.emit('module.installed', { moduleId });
    this.logger.info(`Module installed: ${moduleId}`);
  }
  
  /**
   * Modül etkinleştirme
   */
  async activate(moduleId: string): Promise<void> {
    this.logger.info(`Activating module: ${moduleId}`);
    
    const state = this.states.get(moduleId);
    if (!state || state.status === 'not_installed') {
      throw new ModuleError(`Module not installed: ${moduleId}`);
    }
    
    if (state.status === 'active') {
      this.logger.warn(`Module already active: ${moduleId}`);
      return;
    }
    
    const module = this.modules.get(moduleId);
    const context = this.createContext(module);
    
    // Run activate lifecycle
    await module.onActivate?.(context);
    
    // Update state
    await this.updateState(moduleId, {
      status: 'active',
      activatedAt: new Date(),
    });
    
    // Clear relevant caches
    await this.cache.invalidatePattern(`module:${moduleId}:*`);
    
    this.events.emit('module.activated', { moduleId });
    this.logger.info(`Module activated: ${moduleId}`);
  }
  
  /**
   * Modül devre dışı bırakma
   */
  async deactivate(moduleId: string): Promise<void> {
    this.logger.info(`Deactivating module: ${moduleId}`);
    
    // Core modüller devre dışı bırakılamaz
    if (this.isCoreModule(moduleId)) {
      throw new ModuleError(`Cannot deactivate core module: ${moduleId}`);
    }
    
    const module = this.modules.get(moduleId);
    const context = this.createContext(module);
    
    // Check dependents
    await this.checkDependents(moduleId);
    
    // Run deactivate lifecycle
    await module.onDeactivate?.(context);
    
    // Update state
    await this.updateState(moduleId, {
      status: 'installed',
      activatedAt: null,
    });
    
    this.events.emit('module.deactivated', { moduleId });
    this.logger.info(`Module deactivated: ${moduleId}`);
  }
  
  /**
   * Modül kaldırma
   */
  async uninstall(moduleId: string, options?: { force?: boolean }): Promise<void> {
    this.logger.info(`Uninstalling module: ${moduleId}`);
    
    if (this.isCoreModule(moduleId)) {
      throw new ModuleError(`Cannot uninstall core module: ${moduleId}`);
    }
    
    // Önce devre dışı bırak
    const state = this.states.get(moduleId);
    if (state?.status === 'active') {
      await this.deactivate(moduleId);
    }
    
    const module = this.modules.get(moduleId);
    const context = this.createContext(module, options);
    
    // Run uninstall lifecycle
    await module.onUninstall?.(context);
    
    // Remove from registry
    this.modules.delete(moduleId);
    this.states.delete(moduleId);
    
    // Update database
    await this.prisma.moduleState.delete({
      where: { moduleId },
    });
    
    this.events.emit('module.uninstalled', { moduleId });
    this.logger.info(`Module uninstalled: ${moduleId}`);
  }
  
  /**
   * Modül güncelleme
   */
  async upgrade(moduleId: string, targetVersion: string): Promise<void> {
    this.logger.info(`Upgrading module: ${moduleId} to ${targetVersion}`);
    
    const module = this.modules.get(moduleId);
    const currentVersion = this.states.get(moduleId)?.version;
    
    if (!currentVersion) {
      throw new ModuleError(`Module not installed: ${moduleId}`);
    }
    
    const context = this.createContext(module, {
      fromVersion: currentVersion,
      toVersion: targetVersion,
    });
    
    // Run upgrade lifecycle
    await module.onUpgrade?.(context);
    
    // Update state
    await this.updateState(moduleId, {
      version: targetVersion,
    });
    
    this.events.emit('module.upgraded', { moduleId, from: currentVersion, to: targetVersion });
    this.logger.info(`Module upgraded: ${moduleId}`);
  }
  
  /**
   * Modül durumunu al
   */
  getState(moduleId: string): ModuleState | undefined {
    return this.states.get(moduleId);
  }
  
  /**
   * Tüm modül durumlarını al
   */
  getAllStates(): ModuleState[] {
    return Array.from(this.states.values());
  }
  
  /**
   * Modül aktif mi kontrol et
   */
  isActive(moduleId: string): boolean {
    return this.states.get(moduleId)?.status === 'active';
  }
  
  /**
   * Modül hook'unu çağır
   */
  async callHook<T>(moduleId: string, hookName: string, payload: T): Promise<T> {
    if (!this.isActive(moduleId)) {
      return payload;
    }
    
    const module = this.modules.get(moduleId);
    const hooks = module?.getHooks?.();
    const hook = hooks?.[hookName];
    
    if (typeof hook === 'function') {
      return await hook(payload);
    }
    
    return payload;
  }
  
  // Private methods
  private async loadCoreModules(): Promise<void> {
    const coreModules = [
      'auth', 'organization', 'branch', 'user',
      'media', 'notification', 'subscription', 'module-loader'
    ];
    
    for (const id of coreModules) {
      const module = await this.loadModule(`_core/${id}`);
      this.modules.set(id, module);
      this.states.set(id, { id, status: 'active', version: module.manifest.version });
    }
  }
  
  private async loadModuleStates(): Promise<void> {
    const states = await this.prisma.moduleState.findMany();
    for (const state of states) {
      this.states.set(state.moduleId, state);
    }
  }
  
  private async loadActiveModules(): Promise<void> {
    for (const [id, state] of this.states) {
      if (state.status === 'active' && !this.isCoreModule(id)) {
        const module = await this.loadModule(id);
        this.modules.set(id, module);
        
        const context = this.createContext(module);
        await module.onActivate?.(context);
      }
    }
  }
  
  private isCoreModule(moduleId: string): boolean {
    return moduleId.startsWith('_core/') || 
           ['auth', 'organization', 'branch', 'user', 'media', 'notification', 'subscription', 'module-loader'].includes(moduleId);
  }
}
```

### 3.2 Activation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODÜL ETKİNLEŞTİRME AKIŞI                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Admin Panel: "Menü Modülünü Etkinleştir" butonuna tıklandı                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. API Request                                                      │   │
│  │    POST /api/admin/modules/menu/activate                           │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. Dependency Check                                                 │   │
│  │    ├── auth modülü aktif mi? ✓                                     │   │
│  │    ├── organization modülü aktif mi? ✓                             │   │
│  │    └── media modülü aktif mi? ✓                                    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. Run onActivate Lifecycle                                         │   │
│  │    ├── Register routes (/api/v1/menus/*)                           │   │
│  │    ├── Subscribe to events                                         │   │
│  │    ├── Register hooks                                              │   │
│  │    └── Initialize services                                         │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. Update Database State                                            │   │
│  │    UPDATE module_states SET status = 'active' WHERE id = 'menu'    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 5. Invalidate Caches                                                │   │
│  │    KEYS DELETE module:menu:*                                       │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 6. Emit Event                                                       │   │
│  │    event.emit('module.activated', { moduleId: 'menu' })            │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 7. Response                                                         │   │
│  │    { success: true, message: 'Module activated' }                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ⚠️ REBUILD/RESTART GEREKMİYOR!                                            │
│  Routes dinamik olarak register edilir.                                    │
│  Hot-reload benzeri çalışır.                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Ne Zaman Rebuild/Restart Gerekir?

```yaml
REBUILD GEREKLİ (npm run build):
  - Yeni modül dosyaları eklendiğinde (ilk kez)
  - TypeScript tipleri değiştiğinde
  - Prisma schema değiştiğinde
  - Yeni dependency eklendiğinde

RESTART GEREKLİ:
  - Migration sonrası (veritabanı schema)
  - Environment variable değişikliği
  - Core modül değişikliği

RESTART GEREKMİYOR:
  ✓ Modül etkinleştirme/devre dışı bırakma
  ✓ Modül ayarları değişikliği
  ✓ Tema değişikliği
  ✓ Kullanıcı/rol değişiklikleri
```

---

## 4. MODÜL İLETİŞİMİ

### 4.1 Event-Driven Communication

```typescript
// Modüller arası iletişim SADECE event'ler üzerinden

// menu.events.ts - Event emitting
@Injectable()
export class MenuEventHandlers {
  constructor(private events: EventBus) {}
  
  async onMenuPublished(menu: Menu): Promise<void> {
    // Diğer modüllere haber ver
    this.events.emit('menu.published', {
      menuId: menu.id,
      organizationId: menu.organizationId,
      slug: menu.slug,
    });
  }
}

// order.events.ts - Event listening
@Injectable()
export class OrderEventHandlers {
  constructor(private orderService: OrderService) {}
  
  @OnEvent('menu.published')
  async handleMenuPublished(payload: MenuPublishedEvent): Promise<void> {
    // Order modülü menü yayınlandığında bir şey yapabilir
    await this.orderService.refreshMenuCache(payload.menuId);
  }
}
```

### 4.2 Shared Contracts

```typescript
// src/shared/contracts/menu.contract.ts
// Modüller arası paylaşılan interface'ler

export interface IMenuBasic {
  id: string;
  slug: string;
  name: string;
  organizationId: string;
}

export interface IMenuItemBasic {
  id: string;
  menuId: string;
  name: string;
  price: number;
}

// Order modülü bu interface'i kullanır, Menu modülüne bağımlı olmaz
```

### 4.3 Hook System

```typescript
// Diğer modüller menu işlemlerini genişletebilir

// ai.module.ts
static async onActivate(context: ModuleContext): Promise<void> {
  // Menu modülü aktifse, hook ekle
  if (context.isModuleActive('menu')) {
    context.hooks.tap('menu', 'afterItemCreate', async (item) => {
      // AI ile otomatik açıklama oluştur
      if (!item.description) {
        item.description = await this.aiService.generateDescription(item.name);
      }
      return item;
    });
  }
}
```

---

## 5. TEMA SİSTEMİ

### 5.1 Tema Yapısı

```
themes/
├── admin-theme/
│   ├── theme.json              # Tema manifest
│   ├── layouts/
│   │   ├── default.ejs         # Ana layout
│   │   ├── auth.ejs            # Login/register layout
│   │   └── minimal.ejs         # Modal/popup layout
│   ├── components/
│   │   ├── header.ejs
│   │   ├── sidebar.ejs
│   │   ├── breadcrumb.ejs
│   │   └── ...
│   ├── styles/
│   │   ├── main.css
│   │   └── variables.css
│   └── assets/
│       ├── images/
│       └── fonts/
│
├── product-theme/              # Müşteri-facing menü teması
│   ├── theme.json
│   ├── layouts/
│   │   └── menu.ejs
│   ├── components/
│   │   ├── menu-header.ejs
│   │   ├── category-nav.ejs
│   │   ├── menu-item-card.ejs
│   │   ├── item-modal.ejs
│   │   └── ...
│   ├── styles/
│   └── assets/
│
└── example-theme/              # Referans tema
    └── ... (same structure)
```

### 5.2 Theme Manifest (theme.json)

```json
{
  "$schema": "https://e-menum.net/schemas/theme-v1.json",
  "id": "product-theme",
  "name": "E-Menum Default Theme",
  "version": "1.0.0",
  "type": "product",
  "description": "Varsayılan müşteri menü teması",
  
  "compatibility": {
    "platform": ">=1.0.0"
  },
  
  "layouts": {
    "default": "layouts/menu.ejs"
  },
  
  "components": {
    "required": [
      "menu-header",
      "category-nav",
      "menu-item-card",
      "item-modal"
    ],
    "optional": [
      "cart-drawer",
      "search-modal"
    ]
  },
  
  "styles": {
    "main": "styles/main.css",
    "variables": "styles/variables.css"
  },
  
  "assets": {
    "images": "assets/images",
    "fonts": "assets/fonts"
  },
  
  "settings": {
    "colors": {
      "primary": "#FF6B35",
      "secondary": "#2E4057"
    },
    "fonts": {
      "heading": "Inter",
      "body": "Inter"
    },
    "layout": {
      "itemsPerRow": 2,
      "showPrices": true,
      "showImages": true
    }
  }
}
```

---

## 6. STUB MODULES (Gelecek Modüller)

### 6.1 Stub Yapısı

```typescript
// src/modules/_stubs/payment/index.ts
// SADECE interface export eder, implementation YOK

export interface IPaymentService {
  processPayment(orderId: string, amount: number): Promise<PaymentResult>;
  refund(paymentId: string): Promise<RefundResult>;
  getPaymentStatus(paymentId: string): Promise<PaymentStatus>;
}

export interface PaymentResult {
  success: boolean;
  transactionId?: string;
  error?: string;
}

export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

// Placeholder implementation
export class PaymentServiceStub implements IPaymentService {
  async processPayment(): Promise<PaymentResult> {
    throw new NotImplementedError('Payment module not installed');
  }
  
  async refund(): Promise<RefundResult> {
    throw new NotImplementedError('Payment module not installed');
  }
  
  async getPaymentStatus(): Promise<PaymentStatus> {
    throw new NotImplementedError('Payment module not installed');
  }
}
```

### 6.2 Stub Module Manifest

```json
{
  "$schema": "https://e-menum.net/schemas/module-v1.json",
  "id": "payment",
  "name": "Payment Module",
  "version": "0.0.0",
  "status": "stub",
  "description": "Ödeme entegrasyonu (henüz geliştirilmedi)",
  
  "type": "feature",
  
  "dependencies": {
    "modules": ["auth", "organization", "order"]
  },
  
  "provides": {
    "services": ["IPaymentService"],
    "events": ["payment.completed", "payment.failed", "payment.refunded"]
  },
  
  "plannedFeatures": [
    "Credit card payments",
    "Bank transfer",
    "iyzico integration",
    "Stripe integration"
  ],
  
  "estimatedRelease": "Q2 2026"
}
```

---

## 7. ADMIN PANEL - MODÜL YÖNETİMİ

### 7.1 Modül Yönetim Sayfası

```yaml
Route: /admin/modules

Görünüm:
  - Grid veya liste view
  - Her modül için kart:
    - İkon, isim, versiyon
    - Durum badge (active/installed/not_installed)
    - Açıklama
    - Aksiyonlar: Install/Activate/Deactivate/Uninstall

Aksiyonlar:
  - Install: Modülü kur (migrations)
  - Activate: Etkinleştir (routes register)
  - Deactivate: Devre dışı bırak
  - Uninstall: Kaldır (veri silinir!)
  - Settings: Modül ayarları

Stub Modüller:
  - "Coming Soon" badge
  - Tıklanabilir değil
  - Planlanan özellikler listesi
```

### 7.2 API Endpoints

```yaml
GET    /api/admin/modules              # Tüm modülleri listele
GET    /api/admin/modules/:id          # Modül detayı
POST   /api/admin/modules/:id/install  # Kur
POST   /api/admin/modules/:id/activate # Etkinleştir
POST   /api/admin/modules/:id/deactivate # Devre dışı
DELETE /api/admin/modules/:id          # Kaldır
PATCH  /api/admin/modules/:id/settings # Ayarları güncelle
```

---

## 8. DATABASE SCHEMA

```prisma
// prisma/schema.prisma

model ModuleState {
  id          String   @id @default(uuid())
  moduleId    String   @unique
  status      ModuleStatus @default(NOT_INSTALLED)
  version     String
  config      Json?
  installedAt DateTime?
  activatedAt DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@map("module_states")
}

enum ModuleStatus {
  NOT_INSTALLED
  INSTALLED
  ACTIVE
}

model ModuleMigration {
  id          String   @id @default(uuid())
  moduleId    String
  version     String
  name        String
  executedAt  DateTime @default(now())
  
  @@unique([moduleId, version, name])
  @@map("module_migrations")
}
```

---

*Bu döküman, E-Menum modül sisteminin mimarisini tanımlar. Yeni modül geliştirme için MODULE_DEVELOPMENT_GUIDE.md'ye bakınız.*
