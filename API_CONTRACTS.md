# E-Menum API Contracts

> **Auto-Claude API Document**  
> RESTful conventions, endpoint specifications, request/response formats.  
> Son Güncelleme: 2026-01-31

---

## 1. API OVERVIEW

### 1.1 Base Information

| Property | Value |
|----------|-------|
| Base URL | `https://api.e-menum.net` |
| Version | `v1` |
| Format | JSON |
| Encoding | UTF-8 |
| Authentication | Bearer JWT |

### 1.2 URL Structure

```
https://api.e-menum.net/v1/{resource}/{id?}/{sub-resource?}

Examples:
├── GET    /v1/menus                    # List menus
├── POST   /v1/menus                    # Create menu
├── GET    /v1/menus/:id                # Get menu
├── PUT    /v1/menus/:id                # Update menu (full)
├── PATCH  /v1/menus/:id                # Update menu (partial)
├── DELETE /v1/menus/:id                # Delete menu (soft)
├── GET    /v1/menus/:id/categories     # List menu's categories
└── POST   /v1/menus/:id/publish        # Custom action
```

---

## 2. REQUEST CONVENTIONS

### 2.1 HTTP Methods

| Method | Usage | Idempotent | Safe |
|--------|-------|------------|------|
| `GET` | Retrieve resource(s) | Yes | Yes |
| `POST` | Create resource / Custom action | No | No |
| `PUT` | Full update (replace) | Yes | No |
| `PATCH` | Partial update | Yes | No |
| `DELETE` | Remove resource (soft) | Yes | No |

### 2.2 Request Headers

```
Required Headers:
├── Content-Type: application/json
├── Accept: application/json
└── Authorization: Bearer {access_token}    # Protected routes

Optional Headers:
├── Accept-Language: tr | en                # i18n (default: tr)
├── X-Request-ID: {uuid}                    # Client correlation ID
├── X-Timezone: Europe/Istanbul             # Timezone for dates
└── X-Idempotency-Key: {uuid}               # POST idempotency
```

### 2.3 Query Parameters

#### Pagination

```
GET /v1/products?page=2&perPage=20

Parameters:
├── page      Int     Current page (1-indexed, default: 1)
├── perPage   Int     Items per page (default: 20, max: 100)
└── cursor    String  Cursor-based pagination (alternative)
```

#### Filtering

```
GET /v1/products?status=active&categoryId=cat_xxx

Filter Operators:
├── field=value           # Exact match
├── field[gte]=10         # Greater than or equal
├── field[lte]=100        # Less than or equal
├── field[like]=keyword   # Contains (ILIKE)
├── field[in]=a,b,c       # In array
└── field[null]=true      # Is null check
```

#### Sorting

```
GET /v1/products?sort=-createdAt,name

Format: sort={field},-{field}  (- prefix = DESC)

Default: -createdAt (newest first)
```

#### Field Selection

```
GET /v1/products?fields=id,name,price

Returns only specified fields (sparse fieldsets)
```

#### Expansion (Relations)

```
GET /v1/products?include=category,variants

Includes related resources in response
```

### 2.4 Request Body Format

```json
// POST /v1/menus
{
  "name": "Ana Menü",
  "description": "Restaurant ana menüsü",
  "themeId": "thm_xxx",
  "settings": {
    "showPrices": true,
    "currency": "TRY"
  }
}
```

---

## 3. RESPONSE CONVENTIONS

### 3.1 Success Responses

#### Single Resource

```json
// GET /v1/menus/:id
// Status: 200 OK

{
  "success": true,
  "data": {
    "id": "mnu_cuid123",
    "name": "Ana Menü",
    "slug": "ana-menu",
    "description": "Restaurant ana menüsü",
    "isPublished": true,
    "publishedAt": "2026-01-15T10:30:00Z",
    "createdAt": "2026-01-10T08:00:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  }
}
```

#### Collection (Paginated)

```json
// GET /v1/menus?page=1&perPage=20
// Status: 200 OK

{
  "success": true,
  "data": [
    { "id": "mnu_1", "name": "Ana Menü", ... },
    { "id": "mnu_2", "name": "İçecek Menüsü", ... }
  ],
  "meta": {
    "page": 1,
    "perPage": 20,
    "total": 45,
    "totalPages": 3,
    "hasNextPage": true,
    "hasPrevPage": false
  }
}
```

#### Created Resource

```json
// POST /v1/menus
// Status: 201 Created
// Header: Location: /v1/menus/mnu_newid

{
  "success": true,
  "data": {
    "id": "mnu_newid",
    "name": "Yeni Menü",
    ...
  }
}
```

#### No Content

```json
// DELETE /v1/menus/:id
// Status: 204 No Content

(empty body)
```

### 3.2 Error Responses

#### Standard Error Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "name",
        "message": "Name is required",
        "code": "required"
      },
      {
        "field": "price",
        "message": "Price must be positive",
        "code": "min",
        "params": { "min": 0 }
      }
    ],
    "requestId": "req_xxx",
    "timestamp": "2026-01-31T12:00:00Z"
  }
}
```

#### Error Codes Catalog

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_JSON` | 400 | Malformed JSON body |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `TOKEN_EXPIRED` | 401 | JWT expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `ALREADY_EXISTS` | 409 | Duplicate resource |
| `CONFLICT` | 409 | State conflict |
| `UNPROCESSABLE` | 422 | Business rule violation |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Dependency down |

### 3.3 HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## 4. AUTHENTICATION

### 4.1 Login Flow

```
POST /v1/auth/login

Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response (200):
{
  "success": true,
  "data": {
    "accessToken": "eyJhbG...",
    "expiresIn": 900,
    "tokenType": "Bearer"
  }
}

+ Set-Cookie: refreshToken=xxx; HttpOnly; Secure; SameSite=Strict; Path=/v1/auth
```

### 4.2 Token Refresh

```
POST /v1/auth/refresh

Headers:
Cookie: refreshToken=xxx

Response (200):
{
  "success": true,
  "data": {
    "accessToken": "eyJhbG...",
    "expiresIn": 900,
    "tokenType": "Bearer"
  }
}
```

### 4.3 Logout

```
POST /v1/auth/logout

Headers:
Authorization: Bearer {accessToken}

Response (204): No Content

+ Clear-Cookie: refreshToken
```

---

## 5. RATE LIMITING

### 5.1 Rate Limit Tiers

| Tier | Requests | Window | Applies To |
|------|----------|--------|------------|
| Anonymous | 60 | 1 min | Public endpoints |
| Authenticated | 300 | 1 min | User requests |
| API Key | 1000 | 1 min | Integration keys |
| Premium | 3000 | 1 min | Enterprise plan |

### 5.2 Rate Limit Headers

```
Response Headers:
├── X-RateLimit-Limit: 300
├── X-RateLimit-Remaining: 295
├── X-RateLimit-Reset: 1706702400
└── Retry-After: 45              # Only on 429
```

### 5.3 Rate Limited Response

```json
// Status: 429 Too Many Requests

{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please retry after 45 seconds.",
    "retryAfter": 45
  }
}
```

---

## 6. VERSIONING

### 6.1 Version Strategy

```
URL-based versioning: /v1/, /v2/

Version Lifecycle:
├── Current:    v1 (active development)
├── Deprecated: (none yet)
└── Sunset:     (none yet)

Deprecation Policy:
├── 6 months notice before deprecation
├── Deprecation header in responses
└── 12 months until sunset
```

### 6.2 Deprecation Headers

```
X-API-Deprecated: true
X-API-Sunset-Date: 2027-01-01
X-API-Successor: /v2/menus
```

---

## 7. ENDPOINT CATALOG

### 7.1 Authentication (`/v1/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | User registration | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/refresh` | Refresh token | Cookie |
| POST | `/auth/logout` | User logout | Yes |
| POST | `/auth/forgot-password` | Request reset | No |
| POST | `/auth/reset-password` | Reset password | Token |
| POST | `/auth/verify-email` | Verify email | Token |
| GET | `/auth/me` | Current user | Yes |

### 7.2 Users (`/v1/users`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/users` | List org users | `users.view` |
| POST | `/users` | Invite user | `users.create` |
| GET | `/users/:id` | Get user | `users.view` |
| PATCH | `/users/:id` | Update user | `users.update` |
| DELETE | `/users/:id` | Remove user | `users.delete` |
| PATCH | `/users/:id/role` | Change role | `users.update` |
| POST | `/users/:id/resend-invite` | Resend invite | `users.create` |

### 7.3 Organizations (`/v1/organizations`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/organizations/current` | Get current org | Authenticated |
| PATCH | `/organizations/current` | Update org | `organization.update` |
| GET | `/organizations/current/settings` | Get settings | `organization.view` |
| PATCH | `/organizations/current/settings` | Update settings | `organization.update` |
| POST | `/organizations/current/logo` | Upload logo | `organization.update` |

### 7.4 Menus (`/v1/menus`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/menus` | List menus | `menu.view` |
| POST | `/menus` | Create menu | `menu.create` |
| GET | `/menus/:id` | Get menu | `menu.view` |
| PUT | `/menus/:id` | Update menu | `menu.update` |
| DELETE | `/menus/:id` | Delete menu | `menu.delete` |
| POST | `/menus/:id/publish` | Publish menu | `menu.publish` |
| POST | `/menus/:id/unpublish` | Unpublish menu | `menu.publish` |
| POST | `/menus/:id/duplicate` | Clone menu | `menu.create` |
| GET | `/menus/:id/categories` | List categories | `menu.view` |
| POST | `/menus/:id/categories/reorder` | Reorder categories | `menu.update` |

### 7.5 Categories (`/v1/categories`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/categories` | List all categories | `menu.view` |
| POST | `/categories` | Create category | `menu.create` |
| GET | `/categories/:id` | Get category | `menu.view` |
| PUT | `/categories/:id` | Update category | `menu.update` |
| DELETE | `/categories/:id` | Delete category | `menu.delete` |
| GET | `/categories/:id/products` | List products | `menu.view` |
| POST | `/categories/:id/products/reorder` | Reorder products | `menu.update` |

### 7.6 Products (`/v1/products`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/products` | List products | `menu.view` |
| POST | `/products` | Create product | `menu.create` |
| GET | `/products/:id` | Get product | `menu.view` |
| PUT | `/products/:id` | Update product | `menu.update` |
| DELETE | `/products/:id` | Delete product | `menu.delete` |
| PATCH | `/products/:id/availability` | Toggle availability | `menu.update` |
| POST | `/products/:id/image` | Upload image | `menu.update` |
| GET | `/products/:id/variants` | List variants | `menu.view` |
| POST | `/products/:id/variants` | Add variant | `menu.create` |
| GET | `/products/:id/modifiers` | List modifiers | `menu.view` |
| POST | `/products/:id/modifiers` | Add modifier | `menu.create` |

### 7.7 Tables & Zones (`/v1/tables`, `/v1/zones`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/zones` | List zones | `tables.view` |
| POST | `/zones` | Create zone | `tables.create` |
| PUT | `/zones/:id` | Update zone | `tables.update` |
| DELETE | `/zones/:id` | Delete zone | `tables.delete` |
| GET | `/tables` | List tables | `tables.view` |
| POST | `/tables` | Create table | `tables.create` |
| GET | `/tables/:id` | Get table | `tables.view` |
| PUT | `/tables/:id` | Update table | `tables.update` |
| DELETE | `/tables/:id` | Delete table | `tables.delete` |
| PATCH | `/tables/:id/status` | Change status | `tables.update` |

### 7.8 QR Codes (`/v1/qr-codes`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/qr-codes` | List QR codes | `qr.view` |
| POST | `/qr-codes` | Generate QR | `qr.create` |
| GET | `/qr-codes/:id` | Get QR details | `qr.view` |
| DELETE | `/qr-codes/:id` | Revoke QR | `qr.delete` |
| GET | `/qr-codes/:id/stats` | QR statistics | `qr.view` |
| POST | `/qr-codes/:id/regenerate` | Regenerate image | `qr.update` |

### 7.9 Orders (`/v1/orders`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/orders` | List orders | `orders.view` |
| POST | `/orders` | Create order | `orders.create` |
| GET | `/orders/:id` | Get order | `orders.view` |
| PATCH | `/orders/:id/status` | Update status | `orders.update` |
| POST | `/orders/:id/cancel` | Cancel order | `orders.update` |
| GET | `/orders/:id/items` | List items | `orders.view` |
| POST | `/orders/:id/items` | Add item | `orders.update` |
| DELETE | `/orders/:id/items/:itemId` | Remove item | `orders.update` |

### 7.10 Analytics (`/v1/analytics`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/analytics/dashboard` | Dashboard stats | `analytics.view` |
| GET | `/analytics/sales` | Sales report | `analytics.view` |
| GET | `/analytics/products` | Product performance | `analytics.view` |
| GET | `/analytics/qr-scans` | QR scan stats | `analytics.view` |
| GET | `/analytics/customers` | Customer insights | `analytics.view` |
| POST | `/analytics/export` | Export report | `analytics.export` |

### 7.11 AI Features (`/v1/ai`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/ai/content/generate` | Generate content | `ai.content` |
| POST | `/ai/content/improve` | Improve text | `ai.content` |
| POST | `/ai/content/translate` | Translate text | `ai.translate` |
| POST | `/ai/image/generate` | Generate image | `ai.image` |
| POST | `/ai/image/search` | Search stock photos | `ai.image` |
| POST | `/ai/query` | Natural language query | `ai.query` |
| GET | `/ai/credits` | Check credit balance | Authenticated |
| GET | `/ai/usage` | Usage history | `ai.view` |

### 7.12 Public Endpoints (`/v1/public`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/public/menu/:slug` | View public menu | No |
| GET | `/public/menu/:slug/categories` | Menu categories | No |
| GET | `/public/menu/:slug/products` | Menu products | No |
| GET | `/public/menu/:slug/product/:id` | Product details | No |
| POST | `/public/qr/:code/scan` | Record QR scan | No |
| POST | `/public/order` | Submit order | Optional |
| POST | `/public/feedback` | Submit feedback | Optional |
| POST | `/public/service-request` | Call waiter | No |

---

## 8. WEBHOOK EVENTS

### 8.1 Event Catalog

| Event | Trigger | Payload |
|-------|---------|---------|
| `menu.created` | New menu created | `{ menuId, name }` |
| `menu.published` | Menu published | `{ menuId, publishedAt }` |
| `menu.unpublished` | Menu unpublished | `{ menuId }` |
| `product.created` | New product | `{ productId, name, price }` |
| `product.updated` | Product changed | `{ productId, changes }` |
| `product.availability_changed` | Stock change | `{ productId, isAvailable }` |
| `order.created` | New order | `{ orderId, items, total }` |
| `order.status_changed` | Status update | `{ orderId, from, to }` |
| `qr.scanned` | QR code scanned | `{ qrCodeId, timestamp }` |
| `subscription.created` | New subscription | `{ planId, orgId }` |
| `subscription.changed` | Plan change | `{ from, to, orgId }` |
| `subscription.cancelled` | Cancellation | `{ orgId, reason }` |

### 8.2 Webhook Payload Format

```json
{
  "id": "evt_xxx",
  "type": "order.created",
  "timestamp": "2026-01-31T12:00:00Z",
  "data": {
    "orderId": "ord_xxx",
    "items": [...],
    "total": 150.00
  },
  "organizationId": "org_xxx"
}
```

### 8.3 Webhook Signature

```
X-Webhook-Signature: sha256=xxx

Verification:
1. Compute HMAC-SHA256(payload, webhookSecret)
2. Compare with signature header
3. Reject if mismatch
```

---

## 9. SDK PATTERNS

### 9.1 Resource Pattern

```
Each resource follows consistent patterns:

list(params?)     → GET    /resource
create(data)      → POST   /resource
get(id)           → GET    /resource/:id
update(id, data)  → PUT    /resource/:id
patch(id, data)   → PATCH  /resource/:id
delete(id)        → DELETE /resource/:id
```

### 9.2 Error Handling Pattern

```
API errors contain:
├── code       Machine-readable error code
├── message    Human-readable message
├── details    Validation errors (if applicable)
├── requestId  For support reference
└── timestamp  Error occurrence time

Client should:
├── Check success field first
├── Handle specific codes (RATE_LIMITED, TOKEN_EXPIRED)
├── Display message to user
└── Log requestId for debugging
```

---

## 10. API DOCUMENTATION

### 10.1 OpenAPI Spec Location

```
GET /v1/openapi.json    # OpenAPI 3.0 spec
GET /v1/docs            # Swagger UI (dev only)
```

### 10.2 Postman Collection

```
Available at: /docs/postman-collection.json

Includes:
├── All endpoints
├── Environment variables
├── Example requests
└── Test scripts
```

---

*Bu döküman, E-Menum API sözleşmelerini tanımlar. Tüm endpoint implementasyonları bu spesifikasyonla tutarlı olmalıdır.*
