# E-Menum Module Development Guide

> **Auto-Claude Module Development Guide**  
> Yeni modül geliştirmek için adım adım rehber.  
> Bu dökümanı takip ederek enterprise-ready modül geliştirebilirsiniz.  
> Son Güncelleme: 2026-01-31

---

## 1. BAŞLAMADAN ÖNCE

### 1.1 Ön Koşullar

```yaml
Okumuş Olmalısınız:
  ✓ CLAUDE.md - Proje genel bakış
  ✓ CONSTRAINTS.md - Kısıtlamalar
  ✓ MODULE_SYSTEM.md - Modül mimarisi
  ✓ CODING_STANDARDS.md - Kod standartları
  ✓ API_CONTRACTS.md - API kuralları
  ✓ DATABASE_SCHEMA.md - Veritabanı kuralları

Referans Modül:
  ✓ src/modules/_examples/advanced-example/ incelemiş olmalısınız
  ✓ src/modules/menu/ production modülünü incelemiş olmalısınız
```

### 1.2 Modül Geliştirme Karar Ağacı

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MODÜL GELİŞTİRME KARAR AĞACI                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Bu özellik modül mü olmalı?                                               │
│  │                                                                          │
│  ├─► Bağımsız domain mi? ──────────────────────────────► EVET → MODÜL      │
│  │   (Örn: Ödeme, Envanter, Rezervasyon)                                   │
│  │                                                                          │
│  ├─► Toggle edilebilir mi? ────────────────────────────► EVET → MODÜL      │
│  │   (Örn: Bazı müşteriler istemeyebilir)                                  │
│  │                                                                          │
│  ├─► Tier-based mı? ───────────────────────────────────► EVET → MODÜL      │
│  │   (Örn: Free'de yok, Pro'da var)                                        │
│  │                                                                          │
│  ├─► Başlı başına value sunuyor mu? ───────────────────► EVET → MODÜL      │
│  │   (Örn: AI içerik üretimi)                                              │
│  │                                                                          │
│  └─► Yukarıdakilerin hiçbiri değilse ──────────────────► MEVCUT MODÜLE EKLE│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. MODÜL OLUŞTURMA ADIMLARI

### 2.1 Adım 1: Klasör Yapısını Oluştur

```bash
# Terminal'de çalıştır
mkdir -p src/modules/{module-name}
cd src/modules/{module-name}

# Gerekli dosyaları oluştur
touch module.json
touch index.ts
touch {name}.module.ts
touch {name}.controller.ts
touch {name}.service.ts
touch {name}.repository.ts
touch {name}.schema.ts
touch {name}.types.ts
touch {name}.routes.ts
touch {name}.events.ts
touch {name}.constants.ts
mkdir -p migrations seeds __tests__
```

**Örnek: Payment modülü için:**

```
src/modules/payment/
├── module.json
├── index.ts
├── payment.module.ts
├── payment.controller.ts
├── payment.service.ts
├── payment.repository.ts
├── payment.schema.ts
├── payment.types.ts
├── payment.routes.ts
├── payment.events.ts
├── payment.constants.ts
├── providers/                  # Ödeme sağlayıcıları
│   ├── iyzico.provider.ts
│   └── stripe.provider.ts
├── migrations/
│   └── 001_create_payments.ts
├── seeds/
│   └── demo-payment.seed.ts
└── __tests__/
    ├── payment.service.test.ts
    └── payment.controller.test.ts
```

### 2.2 Adım 2: Module Manifest (module.json)

```json
{
  "$schema": "https://e-menum.net/schemas/module-v1.json",
  "id": "payment",
  "name": "Payment Module",
  "version": "1.0.0",
  "description": "Ödeme entegrasyonu ve işleme",
  
  "type": "feature",
  "category": "commerce",
  
  "author": {
    "name": "Your Name",
    "email": "your.email@e-menum.net"
  },
  
  "compatibility": {
    "platform": ">=1.0.0",
    "node": ">=20.0.0"
  },
  
  "dependencies": {
    "modules": ["auth", "organization", "order"],
    "optional": ["notification"]
  },
  
  "provides": {
    "routes": true,
    "events": [
      "payment.initiated",
      "payment.completed", 
      "payment.failed",
      "payment.refunded"
    ],
    "hooks": [
      "beforePaymentProcess",
      "afterPaymentComplete"
    ],
    "permissions": [
      "payment:read",
      "payment:process",
      "payment:refund",
      "payment:config"
    ]
  },
  
  "requires": {
    "permissions": [
      "auth:verify",
      "organization:read",
      "order:read",
      "order:update"
    ],
    "events": [
      "order.created",
      "order.cancelled"
    ]
  },
  
  "tier": {
    "minimum": "starter",
    "features": {
      "starter": ["basic_payment"],
      "professional": ["multi_gateway", "subscriptions"],
      "business": ["split_payment", "marketplace"],
      "enterprise": ["custom_gateway", "white_label"]
    }
  },
  
  "lifecycle": {
    "install": "migrations/install.ts",
    "activate": "lifecycle/activate.ts",
    "deactivate": "lifecycle/deactivate.ts",
    "uninstall": "migrations/uninstall.ts"
  },
  
  "admin": {
    "menu": {
      "label": "Ödemeler",
      "icon": "ph-credit-card",
      "route": "/admin/payments",
      "order": 25
    },
    "settings": {
      "label": "Ödeme Ayarları",
      "route": "/admin/settings/payments"
    }
  },
  
  "settings": {
    "schema": "settings.schema.json",
    "defaults": {
      "defaultGateway": "iyzico",
      "currency": "TRY",
      "testMode": true
    }
  }
}
```

### 2.3 Adım 3: TypeScript Types (payment.types.ts)

```typescript
// src/modules/payment/payment.types.ts

// === ENUMS ===
export enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REFUNDED = 'refunded',
  PARTIALLY_REFUNDED = 'partially_refunded',
}

export enum PaymentMethod {
  CREDIT_CARD = 'credit_card',
  DEBIT_CARD = 'debit_card',
  BANK_TRANSFER = 'bank_transfer',
  WALLET = 'wallet',
}

export enum PaymentGateway {
  IYZICO = 'iyzico',
  STRIPE = 'stripe',
  PAYTR = 'paytr',
}

// === ENTITIES ===
export interface Payment {
  id: string;
  organizationId: string;
  orderId: string;
  
  // Amount
  amount: number;           // Kuruş cinsinden
  currency: string;
  
  // Status
  status: PaymentStatus;
  method: PaymentMethod;
  gateway: PaymentGateway;
  
  // Gateway response
  gatewayTransactionId?: string;
  gatewayResponse?: Record<string, unknown>;
  
  // Timestamps
  initiatedAt: Date;
  completedAt?: Date;
  failedAt?: Date;
  
  // Metadata
  metadata?: Record<string, unknown>;
  
  createdAt: Date;
  updatedAt: Date;
}

export interface PaymentRefund {
  id: string;
  paymentId: string;
  amount: number;
  reason?: string;
  status: 'pending' | 'completed' | 'failed';
  gatewayRefundId?: string;
  createdAt: Date;
}

// === DTOs ===
export interface CreatePaymentDto {
  orderId: string;
  amount: number;
  currency?: string;
  method: PaymentMethod;
  gateway?: PaymentGateway;
  metadata?: Record<string, unknown>;
}

export interface ProcessPaymentDto {
  paymentId: string;
  cardToken?: string;          // Tokenized card
  saveCard?: boolean;
  installments?: number;
}

export interface RefundPaymentDto {
  paymentId: string;
  amount?: number;             // Partial refund
  reason?: string;
}

// === RESPONSES ===
export interface PaymentResult {
  success: boolean;
  payment: Payment;
  redirectUrl?: string;        // 3D Secure için
  error?: PaymentError;
}

export interface PaymentError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// === EVENTS ===
export interface PaymentInitiatedEvent {
  paymentId: string;
  orderId: string;
  amount: number;
  gateway: PaymentGateway;
}

export interface PaymentCompletedEvent {
  paymentId: string;
  orderId: string;
  transactionId: string;
}

export interface PaymentFailedEvent {
  paymentId: string;
  orderId: string;
  error: PaymentError;
}

// === CONFIG ===
export interface PaymentModuleConfig {
  defaultGateway: PaymentGateway;
  currency: string;
  testMode: boolean;
  gateways: {
    iyzico?: {
      apiKey: string;
      secretKey: string;
      baseUrl: string;
    };
    stripe?: {
      publishableKey: string;
      secretKey: string;
    };
  };
}
```

### 2.4 Adım 4: Validation Schema (payment.schema.ts)

```typescript
// src/modules/payment/payment.schema.ts
import { z } from 'zod';
import { PaymentMethod, PaymentGateway } from './payment.types';

// === CREATE PAYMENT ===
export const createPaymentSchema = z.object({
  orderId: z.string().uuid('Geçerli sipariş ID gerekli'),
  amount: z.number().positive('Tutar pozitif olmalı'),
  currency: z.string().length(3).default('TRY'),
  method: z.nativeEnum(PaymentMethod),
  gateway: z.nativeEnum(PaymentGateway).optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type CreatePaymentInput = z.infer<typeof createPaymentSchema>;

// === PROCESS PAYMENT ===
export const processPaymentSchema = z.object({
  paymentId: z.string().uuid(),
  cardToken: z.string().optional(),
  saveCard: z.boolean().default(false),
  installments: z.number().int().min(1).max(12).default(1),
});

export type ProcessPaymentInput = z.infer<typeof processPaymentSchema>;

// === REFUND ===
export const refundPaymentSchema = z.object({
  paymentId: z.string().uuid(),
  amount: z.number().positive().optional(),
  reason: z.string().max(500).optional(),
});

export type RefundPaymentInput = z.infer<typeof refundPaymentSchema>;

// === QUERY ===
export const paymentQuerySchema = z.object({
  organizationId: z.string().uuid().optional(),
  orderId: z.string().uuid().optional(),
  status: z.nativeEnum(PaymentStatus).optional(),
  gateway: z.nativeEnum(PaymentGateway).optional(),
  startDate: z.coerce.date().optional(),
  endDate: z.coerce.date().optional(),
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});

// === CONFIG ===
export const paymentConfigSchema = z.object({
  defaultGateway: z.nativeEnum(PaymentGateway),
  currency: z.string().length(3),
  testMode: z.boolean(),
  gateways: z.object({
    iyzico: z.object({
      apiKey: z.string().min(1),
      secretKey: z.string().min(1),
      baseUrl: z.string().url(),
    }).optional(),
    stripe: z.object({
      publishableKey: z.string().startsWith('pk_'),
      secretKey: z.string().startsWith('sk_'),
    }).optional(),
  }),
});
```

### 2.5 Adım 5: Repository (payment.repository.ts)

```typescript
// src/modules/payment/payment.repository.ts
import { Injectable } from '@/core/di';
import { PrismaService } from '@/core/database';
import { Payment, PaymentRefund, PaymentStatus } from './payment.types';

@Injectable()
export class PaymentRepository {
  constructor(private prisma: PrismaService) {}
  
  async create(data: Omit<Payment, 'id' | 'createdAt' | 'updatedAt'>): Promise<Payment> {
    return this.prisma.payment.create({
      data: {
        ...data,
        initiatedAt: new Date(),
      },
    });
  }
  
  async findById(id: string): Promise<Payment | null> {
    return this.prisma.payment.findUnique({
      where: { id },
    });
  }
  
  async findByOrderId(orderId: string): Promise<Payment[]> {
    return this.prisma.payment.findMany({
      where: { orderId },
      orderBy: { createdAt: 'desc' },
    });
  }
  
  async findByOrganization(
    organizationId: string,
    options?: {
      status?: PaymentStatus;
      startDate?: Date;
      endDate?: Date;
      limit?: number;
      offset?: number;
    }
  ): Promise<{ payments: Payment[]; total: number }> {
    const where = {
      organizationId,
      ...(options?.status && { status: options.status }),
      ...(options?.startDate && {
        createdAt: {
          gte: options.startDate,
          ...(options?.endDate && { lte: options.endDate }),
        },
      }),
    };
    
    const [payments, total] = await Promise.all([
      this.prisma.payment.findMany({
        where,
        take: options?.limit ?? 20,
        skip: options?.offset ?? 0,
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.payment.count({ where }),
    ]);
    
    return { payments, total };
  }
  
  async updateStatus(
    id: string,
    status: PaymentStatus,
    gatewayResponse?: Record<string, unknown>
  ): Promise<Payment> {
    const updateData: Record<string, unknown> = { status };
    
    if (status === PaymentStatus.COMPLETED) {
      updateData.completedAt = new Date();
    } else if (status === PaymentStatus.FAILED) {
      updateData.failedAt = new Date();
    }
    
    if (gatewayResponse) {
      updateData.gatewayResponse = gatewayResponse;
    }
    
    return this.prisma.payment.update({
      where: { id },
      data: updateData,
    });
  }
  
  async createRefund(
    data: Omit<PaymentRefund, 'id' | 'createdAt'>
  ): Promise<PaymentRefund> {
    return this.prisma.paymentRefund.create({ data });
  }
}
```

### 2.6 Adım 6: Service (payment.service.ts)

```typescript
// src/modules/payment/payment.service.ts
import { Injectable } from '@/core/di';
import { EventBus } from '@/core/events';
import { Logger } from '@/core/logger';
import { PaymentRepository } from './payment.repository';
import { PaymentGatewayFactory } from './providers/gateway.factory';
import {
  Payment,
  PaymentStatus,
  CreatePaymentDto,
  ProcessPaymentDto,
  RefundPaymentDto,
  PaymentResult,
  PaymentError,
} from './payment.types';
import {
  PaymentNotFoundError,
  PaymentAlreadyProcessedError,
  PaymentProcessingError,
  RefundNotAllowedError,
} from './payment.errors';

@Injectable()
export class PaymentService {
  constructor(
    private repository: PaymentRepository,
    private gatewayFactory: PaymentGatewayFactory,
    private events: EventBus,
    private logger: Logger,
  ) {}
  
  /**
   * Ödeme oluştur
   */
  async createPayment(
    organizationId: string,
    dto: CreatePaymentDto
  ): Promise<Payment> {
    this.logger.debug('Creating payment', { organizationId, dto });
    
    const payment = await this.repository.create({
      organizationId,
      orderId: dto.orderId,
      amount: dto.amount,
      currency: dto.currency ?? 'TRY',
      status: PaymentStatus.PENDING,
      method: dto.method,
      gateway: dto.gateway ?? this.getDefaultGateway(organizationId),
      metadata: dto.metadata,
    });
    
    this.events.emit('payment.initiated', {
      paymentId: payment.id,
      orderId: payment.orderId,
      amount: payment.amount,
      gateway: payment.gateway,
    });
    
    return payment;
  }
  
  /**
   * Ödeme işle
   */
  async processPayment(dto: ProcessPaymentDto): Promise<PaymentResult> {
    const payment = await this.repository.findById(dto.paymentId);
    
    if (!payment) {
      throw new PaymentNotFoundError(dto.paymentId);
    }
    
    if (payment.status !== PaymentStatus.PENDING) {
      throw new PaymentAlreadyProcessedError(dto.paymentId);
    }
    
    // Update status to processing
    await this.repository.updateStatus(dto.paymentId, PaymentStatus.PROCESSING);
    
    try {
      // Get appropriate gateway
      const gateway = this.gatewayFactory.getGateway(payment.gateway);
      
      // Process with gateway
      const result = await gateway.processPayment({
        amount: payment.amount,
        currency: payment.currency,
        orderId: payment.orderId,
        cardToken: dto.cardToken,
        installments: dto.installments,
      });
      
      if (result.success) {
        const updatedPayment = await this.repository.updateStatus(
          dto.paymentId,
          PaymentStatus.COMPLETED,
          result.gatewayResponse
        );
        
        this.events.emit('payment.completed', {
          paymentId: payment.id,
          orderId: payment.orderId,
          transactionId: result.transactionId,
        });
        
        return {
          success: true,
          payment: updatedPayment,
        };
      } else {
        const updatedPayment = await this.repository.updateStatus(
          dto.paymentId,
          PaymentStatus.FAILED,
          result.gatewayResponse
        );
        
        this.events.emit('payment.failed', {
          paymentId: payment.id,
          orderId: payment.orderId,
          error: result.error,
        });
        
        return {
          success: false,
          payment: updatedPayment,
          error: result.error,
        };
      }
    } catch (error) {
      this.logger.error('Payment processing failed', { error, paymentId: dto.paymentId });
      
      await this.repository.updateStatus(dto.paymentId, PaymentStatus.FAILED);
      
      throw new PaymentProcessingError(error.message);
    }
  }
  
  /**
   * İade işle
   */
  async refundPayment(dto: RefundPaymentDto): Promise<PaymentResult> {
    const payment = await this.repository.findById(dto.paymentId);
    
    if (!payment) {
      throw new PaymentNotFoundError(dto.paymentId);
    }
    
    if (payment.status !== PaymentStatus.COMPLETED) {
      throw new RefundNotAllowedError('Only completed payments can be refunded');
    }
    
    const refundAmount = dto.amount ?? payment.amount;
    
    // Process refund with gateway
    const gateway = this.gatewayFactory.getGateway(payment.gateway);
    const result = await gateway.refund({
      transactionId: payment.gatewayTransactionId!,
      amount: refundAmount,
    });
    
    if (result.success) {
      // Create refund record
      await this.repository.createRefund({
        paymentId: payment.id,
        amount: refundAmount,
        reason: dto.reason,
        status: 'completed',
        gatewayRefundId: result.refundId,
      });
      
      // Update payment status
      const newStatus = refundAmount === payment.amount
        ? PaymentStatus.REFUNDED
        : PaymentStatus.PARTIALLY_REFUNDED;
      
      const updatedPayment = await this.repository.updateStatus(
        dto.paymentId,
        newStatus
      );
      
      this.events.emit('payment.refunded', {
        paymentId: payment.id,
        amount: refundAmount,
        isPartial: newStatus === PaymentStatus.PARTIALLY_REFUNDED,
      });
      
      return { success: true, payment: updatedPayment };
    }
    
    return { success: false, payment, error: result.error };
  }
  
  /**
   * Ödeme getir
   */
  async getPayment(id: string): Promise<Payment | null> {
    return this.repository.findById(id);
  }
  
  /**
   * Sipariş ödemelerini getir
   */
  async getOrderPayments(orderId: string): Promise<Payment[]> {
    return this.repository.findByOrderId(orderId);
  }
  
  // Private methods
  private getDefaultGateway(organizationId: string): PaymentGateway {
    // TODO: Get from organization settings
    return PaymentGateway.IYZICO;
  }
}
```

### 2.7 Adım 7: Controller (payment.controller.ts)

```typescript
// src/modules/payment/payment.controller.ts
import { Request, Response, NextFunction } from 'express';
import { Injectable } from '@/core/di';
import { PaymentService } from './payment.service';
import {
  createPaymentSchema,
  processPaymentSchema,
  refundPaymentSchema,
  paymentQuerySchema,
} from './payment.schema';

@Injectable()
export class PaymentController {
  constructor(private service: PaymentService) {}
  
  /**
   * POST /api/v1/payments
   * Ödeme oluştur
   */
  async create(req: Request, res: Response, next: NextFunction) {
    try {
      const dto = createPaymentSchema.parse(req.body);
      const payment = await this.service.createPayment(
        req.user.organizationId,
        dto
      );
      
      res.status(201).json({
        success: true,
        data: payment,
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * POST /api/v1/payments/:id/process
   * Ödeme işle
   */
  async process(req: Request, res: Response, next: NextFunction) {
    try {
      const dto = processPaymentSchema.parse({
        paymentId: req.params.id,
        ...req.body,
      });
      
      const result = await this.service.processPayment(dto);
      
      if (result.success) {
        res.json({
          success: true,
          data: result.payment,
          redirectUrl: result.redirectUrl,
        });
      } else {
        res.status(400).json({
          success: false,
          error: result.error,
        });
      }
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * POST /api/v1/payments/:id/refund
   * İade et
   */
  async refund(req: Request, res: Response, next: NextFunction) {
    try {
      const dto = refundPaymentSchema.parse({
        paymentId: req.params.id,
        ...req.body,
      });
      
      const result = await this.service.refundPayment(dto);
      
      res.json({
        success: result.success,
        data: result.payment,
        error: result.error,
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * GET /api/v1/payments/:id
   * Ödeme detayı
   */
  async getById(req: Request, res: Response, next: NextFunction) {
    try {
      const payment = await this.service.getPayment(req.params.id);
      
      if (!payment) {
        return res.status(404).json({
          success: false,
          error: { code: 'NOT_FOUND', message: 'Payment not found' },
        });
      }
      
      res.json({
        success: true,
        data: payment,
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * GET /api/v1/payments
   * Ödeme listesi
   */
  async list(req: Request, res: Response, next: NextFunction) {
    try {
      const query = paymentQuerySchema.parse(req.query);
      const { payments, total } = await this.service.listPayments(
        req.user.organizationId,
        query
      );
      
      res.json({
        success: true,
        data: payments,
        meta: {
          total,
          page: query.page,
          limit: query.limit,
          totalPages: Math.ceil(total / query.limit),
        },
      });
    } catch (error) {
      next(error);
    }
  }
}
```

### 2.8 Adım 8: Routes (payment.routes.ts)

```typescript
// src/modules/payment/payment.routes.ts
import { Router } from 'express';
import { container } from '@/core/di';
import { auth, rbac, tenantGuard } from '@/core/middleware';
import { PaymentController } from './payment.controller';

export function createPaymentRoutes(): Router {
  const router = Router();
  const controller = container.resolve(PaymentController);
  
  // All routes require authentication
  router.use(auth());
  router.use(tenantGuard());
  
  // CRUD
  router.post(
    '/',
    rbac('payment:process'),
    controller.create.bind(controller)
  );
  
  router.get(
    '/',
    rbac('payment:read'),
    controller.list.bind(controller)
  );
  
  router.get(
    '/:id',
    rbac('payment:read'),
    controller.getById.bind(controller)
  );
  
  // Actions
  router.post(
    '/:id/process',
    rbac('payment:process'),
    controller.process.bind(controller)
  );
  
  router.post(
    '/:id/refund',
    rbac('payment:refund'),
    controller.refund.bind(controller)
  );
  
  return router;
}

export const paymentRoutes = {
  prefix: '/api/v1/payments',
  router: createPaymentRoutes,
};
```

### 2.9 Adım 9: Module Definition (payment.module.ts)

```typescript
// src/modules/payment/payment.module.ts
import { Module, ModuleContext } from '@/core/module-loader';
import { PaymentController } from './payment.controller';
import { PaymentService } from './payment.service';
import { PaymentRepository } from './payment.repository';
import { PaymentEventHandlers } from './payment.events';
import { PaymentGatewayFactory } from './providers/gateway.factory';
import { paymentRoutes } from './payment.routes';
import manifest from './module.json';

@Module({
  id: 'payment',
  manifest,
})
export class PaymentModule {
  static providers = [
    PaymentService,
    PaymentRepository,
    PaymentEventHandlers,
    PaymentGatewayFactory,
  ];
  
  static controllers = [PaymentController];
  
  static routes = paymentRoutes;
  
  static async onInstall(context: ModuleContext): Promise<void> {
    context.logger.info('Installing Payment module...');
    
    // Run migrations
    await context.runMigrations(__dirname + '/migrations');
    
    context.logger.info('Payment module installed');
  }
  
  static async onActivate(context: ModuleContext): Promise<void> {
    context.logger.info('Activating Payment module...');
    
    // Register routes
    context.registerRoutes(this.routes);
    
    // Subscribe to events
    context.events.on('order.created', PaymentEventHandlers.onOrderCreated);
    context.events.on('order.cancelled', PaymentEventHandlers.onOrderCancelled);
    
    // Register permissions
    context.permissions.register([
      { id: 'payment:read', name: 'View Payments', module: 'payment' },
      { id: 'payment:process', name: 'Process Payments', module: 'payment' },
      { id: 'payment:refund', name: 'Refund Payments', module: 'payment' },
      { id: 'payment:config', name: 'Configure Payments', module: 'payment' },
    ]);
    
    context.logger.info('Payment module activated');
  }
  
  static async onDeactivate(context: ModuleContext): Promise<void> {
    context.logger.info('Deactivating Payment module...');
    
    // Unregister routes
    context.unregisterRoutes(this.routes);
    
    // Unsubscribe from events
    context.events.off('order.created', PaymentEventHandlers.onOrderCreated);
    context.events.off('order.cancelled', PaymentEventHandlers.onOrderCancelled);
    
    context.logger.info('Payment module deactivated');
  }
  
  static async onUninstall(context: ModuleContext): Promise<void> {
    if (!context.options.force) {
      throw new Error('Use --force to delete payment data');
    }
    
    context.logger.warn('Uninstalling Payment module - DATA WILL BE DELETED');
    
    // Rollback migrations
    await context.rollbackMigrations(__dirname + '/migrations');
    
    context.logger.info('Payment module uninstalled');
  }
}
```

### 2.10 Adım 10: Public Exports (index.ts)

```typescript
// src/modules/payment/index.ts

// Module
export { PaymentModule } from './payment.module';

// Types (public interface)
export {
  Payment,
  PaymentStatus,
  PaymentMethod,
  PaymentGateway,
  PaymentResult,
  PaymentError,
  CreatePaymentDto,
  ProcessPaymentDto,
  RefundPaymentDto,
} from './payment.types';

// Events
export {
  PaymentInitiatedEvent,
  PaymentCompletedEvent,
  PaymentFailedEvent,
} from './payment.types';

// Service (for DI in other modules)
export { PaymentService } from './payment.service';

// DO NOT EXPORT:
// - Repository (internal)
// - Controller (internal)
// - Schema (internal)
// - Providers (internal)
```

---

## 3. DATABASE MIGRATION

### 3.1 Migration Dosyası Oluştur

```typescript
// src/modules/payment/migrations/001_create_payments.ts
import { Prisma } from '@prisma/client';

export const up = async (prisma: any) => {
  // payments tablosu
  await prisma.$executeRaw`
    CREATE TABLE IF NOT EXISTS payments (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id UUID NOT NULL REFERENCES organizations(id),
      order_id UUID NOT NULL REFERENCES orders(id),
      
      amount INTEGER NOT NULL,
      currency VARCHAR(3) NOT NULL DEFAULT 'TRY',
      
      status VARCHAR(30) NOT NULL DEFAULT 'pending',
      method VARCHAR(30) NOT NULL,
      gateway VARCHAR(30) NOT NULL,
      
      gateway_transaction_id VARCHAR(255),
      gateway_response JSONB,
      
      initiated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      completed_at TIMESTAMPTZ,
      failed_at TIMESTAMPTZ,
      
      metadata JSONB,
      
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  
  // payment_refunds tablosu
  await prisma.$executeRaw`
    CREATE TABLE IF NOT EXISTS payment_refunds (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      payment_id UUID NOT NULL REFERENCES payments(id),
      amount INTEGER NOT NULL,
      reason TEXT,
      status VARCHAR(30) NOT NULL DEFAULT 'pending',
      gateway_refund_id VARCHAR(255),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `;
  
  // Indexes
  await prisma.$executeRaw`
    CREATE INDEX IF NOT EXISTS idx_payments_organization 
    ON payments(organization_id)
  `;
  
  await prisma.$executeRaw`
    CREATE INDEX IF NOT EXISTS idx_payments_order 
    ON payments(order_id)
  `;
  
  await prisma.$executeRaw`
    CREATE INDEX IF NOT EXISTS idx_payments_status 
    ON payments(status)
  `;
};

export const down = async (prisma: any) => {
  await prisma.$executeRaw`DROP TABLE IF EXISTS payment_refunds`;
  await prisma.$executeRaw`DROP TABLE IF EXISTS payments`;
};
```

### 3.2 Prisma Schema Güncelle

```prisma
// prisma/schema.prisma içine ekle

model Payment {
  id             String   @id @default(uuid())
  organizationId String   @map("organization_id")
  orderId        String   @map("order_id")
  
  amount         Int
  currency       String   @default("TRY") @db.VarChar(3)
  
  status         String   @default("pending") @db.VarChar(30)
  method         String   @db.VarChar(30)
  gateway        String   @db.VarChar(30)
  
  gatewayTransactionId String? @map("gateway_transaction_id")
  gatewayResponse      Json?   @map("gateway_response")
  
  initiatedAt    DateTime @default(now()) @map("initiated_at")
  completedAt    DateTime? @map("completed_at")
  failedAt       DateTime? @map("failed_at")
  
  metadata       Json?
  
  createdAt      DateTime @default(now()) @map("created_at")
  updatedAt      DateTime @updatedAt @map("updated_at")
  
  // Relations
  organization   Organization @relation(fields: [organizationId], references: [id])
  order          Order        @relation(fields: [orderId], references: [id])
  refunds        PaymentRefund[]
  
  @@index([organizationId])
  @@index([orderId])
  @@index([status])
  @@map("payments")
}

model PaymentRefund {
  id              String   @id @default(uuid())
  paymentId       String   @map("payment_id")
  amount          Int
  reason          String?
  status          String   @default("pending") @db.VarChar(30)
  gatewayRefundId String?  @map("gateway_refund_id")
  createdAt       DateTime @default(now()) @map("created_at")
  
  payment         Payment  @relation(fields: [paymentId], references: [id])
  
  @@map("payment_refunds")
}
```

---

## 4. TEST YAZMA

### 4.1 Service Test

```typescript
// src/modules/payment/__tests__/payment.service.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PaymentService } from '../payment.service';
import { PaymentRepository } from '../payment.repository';
import { PaymentGatewayFactory } from '../providers/gateway.factory';
import { EventBus } from '@/core/events';
import { PaymentStatus, PaymentMethod, PaymentGateway } from '../payment.types';

describe('PaymentService', () => {
  let service: PaymentService;
  let mockRepository: jest.Mocked<PaymentRepository>;
  let mockGatewayFactory: jest.Mocked<PaymentGatewayFactory>;
  let mockEvents: jest.Mocked<EventBus>;
  
  beforeEach(() => {
    mockRepository = {
      create: vi.fn(),
      findById: vi.fn(),
      updateStatus: vi.fn(),
    } as any;
    
    mockGatewayFactory = {
      getGateway: vi.fn(),
    } as any;
    
    mockEvents = {
      emit: vi.fn(),
    } as any;
    
    service = new PaymentService(
      mockRepository,
      mockGatewayFactory,
      mockEvents,
      console as any
    );
  });
  
  describe('createPayment', () => {
    it('should create a pending payment', async () => {
      const dto = {
        orderId: 'order-123',
        amount: 10000,
        method: PaymentMethod.CREDIT_CARD,
      };
      
      const expectedPayment = {
        id: 'payment-123',
        ...dto,
        status: PaymentStatus.PENDING,
        gateway: PaymentGateway.IYZICO,
      };
      
      mockRepository.create.mockResolvedValue(expectedPayment as any);
      
      const result = await service.createPayment('org-123', dto);
      
      expect(result.status).toBe(PaymentStatus.PENDING);
      expect(mockEvents.emit).toHaveBeenCalledWith(
        'payment.initiated',
        expect.objectContaining({ paymentId: 'payment-123' })
      );
    });
  });
  
  describe('processPayment', () => {
    it('should process payment successfully', async () => {
      const payment = {
        id: 'payment-123',
        status: PaymentStatus.PENDING,
        amount: 10000,
        gateway: PaymentGateway.IYZICO,
      };
      
      mockRepository.findById.mockResolvedValue(payment as any);
      
      const mockGateway = {
        processPayment: vi.fn().mockResolvedValue({
          success: true,
          transactionId: 'tx-123',
        }),
      };
      
      mockGatewayFactory.getGateway.mockReturnValue(mockGateway as any);
      mockRepository.updateStatus.mockResolvedValue({
        ...payment,
        status: PaymentStatus.COMPLETED,
      } as any);
      
      const result = await service.processPayment({ paymentId: 'payment-123' });
      
      expect(result.success).toBe(true);
      expect(result.payment.status).toBe(PaymentStatus.COMPLETED);
      expect(mockEvents.emit).toHaveBeenCalledWith(
        'payment.completed',
        expect.any(Object)
      );
    });
    
    it('should throw error for non-pending payment', async () => {
      const payment = {
        id: 'payment-123',
        status: PaymentStatus.COMPLETED,
      };
      
      mockRepository.findById.mockResolvedValue(payment as any);
      
      await expect(
        service.processPayment({ paymentId: 'payment-123' })
      ).rejects.toThrow('already processed');
    });
  });
});
```

---

## 5. CHECKLIST

### 5.1 Modül Geliştirme Checklist

```yaml
PLANLAMA:
  [ ] Modül scope tanımlandı
  [ ] Dependencies belirlendi
  [ ] API endpoints tasarlandı
  [ ] Database schema tasarlandı
  [ ] Events/hooks tasarlandı

IMPLEMENTASYON:
  [ ] module.json oluşturuldu
  [ ] Types tanımlandı
  [ ] Schemas yazıldı
  [ ] Repository implement edildi
  [ ] Service implement edildi
  [ ] Controller implement edildi
  [ ] Routes tanımlandı
  [ ] Events implement edildi
  [ ] Module class oluşturuldu
  [ ] index.ts exports tanımlandı

VERİTABANI:
  [ ] Migration yazıldı
  [ ] Prisma schema güncellendi
  [ ] Indexes eklendi
  [ ] Seeds hazırlandı (dev için)

TEST:
  [ ] Unit tests yazıldı
  [ ] Integration tests yazıldı
  [ ] Coverage %80+ 

DOKÜMANTASYON:
  [ ] README.md yazıldı
  [ ] API docs güncellendi
  [ ] JSDoc comments eklendi

REVIEW:
  [ ] Kod review yapıldı
  [ ] Security review yapıldı
  [ ] Performance review yapıldı
```

---

## 6. YAYGN HATALAR

```yaml
YAPILMAMASI GEREKENLER:

❌ Başka modülün internal dosyasını import etme
❌ Global state kullanma
❌ Hardcoded değerler
❌ Circular dependencies
❌ Test yazmadan PR açma
❌ Migration olmadan schema değiştirme
❌ Event'siz cross-module communication
❌ Type'sız export
```

---

*Bu rehber, E-Menum için yeni modül geliştirmek isteyenler için referans niteliğindedir.*
