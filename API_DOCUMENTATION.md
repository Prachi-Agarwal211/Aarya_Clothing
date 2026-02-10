# Aarya Clothing - API Documentation

## System Overview

### Microservices Architecture

Our backend consists of three main microservices:

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| **Core Platform** | 8001 | User Management, Authentication, Sessions | `/health` |
| **Commerce** | 8010 | Products, Orders, Cart, Inventory | `/health` |
| **Payment** | 8020 | Payment Processing, Transactions | `/health` |

### Infrastructure

- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Reverse Proxy**: Nginx
- **Containerization**: Docker & Docker Compose

## Authentication System

### Overview

We use a **dual authentication system** with:
- **JWT Tokens** (Access + Refresh)
- **Cookie-based Sessions** (24-hour login persistence)
- **Role-based Access Control** (Admin, Staff, Customer)

### Authentication Flow

1. **Login**: User submits credentials → JWT tokens + session cookies
2. **API Calls**: Include JWT in Authorization header OR use cookies
3. **Token Refresh**: Automatic refresh using refresh token
4. **Logout**: Clear cookies + revoke tokens

### Authentication Endpoints

#### Core Service (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login (sets cookies) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (clears cookies) |
| POST | `/api/v1/auth/logout-all` | Logout from all devices |
| POST | `/api/v1/auth/change-password` | Change password |
| POST | `/api/v1/auth/forgot-password` | Request password reset |
| POST | `/api/v1/auth/reset-password` | Reset password with token |
| GET | `/api/v1/auth/verify-reset-token/{token}` | Verify reset token |

#### OTP Verification

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/send-otp` | Send OTP (Email/WhatsApp) |
| POST | `/api/v1/auth/verify-otp` | Verify OTP code |
| POST | `/api/v1/auth/resend-otp` | Resend OTP |

#### Password Reset with OTP

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/forgot-password-otp` | Request password reset OTP |
| POST | `/api/v1/auth/reset-password-otp` | Reset password with OTP |

### Cookie Configuration

All authentication cookies are:
- **HttpOnly**: Prevents XSS attacks
- **Secure**: HTTPS only (in production)
- **SameSite**: Lax (CSRF protection)
- **Path**: Scoped appropriately

| Cookie | Purpose | Duration |
|--------|---------|----------|
| `access_token` | JWT access token | 30 minutes |
| `refresh_token` | JWT refresh token | 24 hours (if remember_me) |
| `session_id` | Session identifier | 24 hours |

### Using Authentication

#### Option 1: Cookie-based (Recommended for browsers)
```javascript
// Login - cookies are set automatically
fetch('/api/v1/auth/login', {
  method: 'POST',
  credentials: 'include', // Important!
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password',
    remember_me: true
  })
});

// Subsequent calls - cookies sent automatically
fetch('/api/v1/users/me', {
  credentials: 'include'
});
```

#### Option 2: Authorization Header
```javascript
// Login - get tokens
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});
const { tokens } = await response.json();

// Subsequent calls - include token
fetch('/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`
  }
});
```

## API Endpoints

### Base URLs
- **Core**: `http://localhost:8001`
- **Commerce**: `http://localhost:8010`
- **Payment**: `http://localhost:8020`

### User Management (Core Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/users/me` | Get current user info | ✅ |
| PATCH | `/api/v1/users/me` | Update user profile | ✅ |
| GET | `/api/v1/users/{user_id}` | Get user by ID | ✅ (admin/self) |

### Admin Routes (Core Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/admin/users` | List all users | ✅ Admin |
| PATCH | `/api/v1/admin/users/{user_id}/activate` | Activate user | ✅ Admin |
| PATCH | `/api/v1/admin/users/{user_id}/deactivate` | Deactivate user | ✅ Admin |
| PATCH | `/api/v1/admin/users/{user_id}/role` | Update user role | ✅ Admin |
| GET | `/api/v1/admin/users/role/{role}` | List users by role | ✅ Admin |

### Categories (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/categories` | List categories | ❌ |
| GET | `/api/v1/categories/tree` | Get category tree | ❌ |
| GET | `/api/v1/categories/{category_id}` | Get category by ID | ❌ |
| GET | `/api/v1/categories/slug/{slug}` | Get category by slug | ❌ |

### Products (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/products` | List products | ❌ |
| GET | `/api/v1/products/new-arrivals` | Get new arrivals | ❌ |
| GET | `/api/v1/products/{product_id}` | Get product details | ❌ |
| GET | `/api/v1/products/search` | Search products | ❌ |

### Cart (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/cart/{user_id}` | Get user cart | ❌ |
| POST | `/api/v1/cart/{user_id}/add` | Add to cart | ❌ |
| DELETE | `/api/v1/cart/{user_id}/remove/{product_id}` | Remove from cart | ❌ |
| DELETE | `/api/v1/cart/{user_id}/clear` | Clear cart | ❌ |

### Orders (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/orders` | Create order | ✅ |
| GET | `/api/v1/orders` | List user orders | ✅ |
| GET | `/api/v1/orders/{order_id}` | Get order details | ✅ |
| POST | `/api/v1/orders/{order_id}/cancel` | Cancel order | ✅ |
| GET | `/api/v1/orders/{order_id}/tracking` | Get order tracking | ✅ |

### Wishlist (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/wishlist/{user_id}` | Get wishlist | ❌ |
| POST | `/api/v1/wishlist/{user_id}/add` | Add to wishlist | ❌ |
| DELETE | `/api/v1/wishlist/{user_id}/remove/{product_id}` | Remove from wishlist | ❌ |
| DELETE | `/api/v1/wishlist/{user_id}/clear` | Clear wishlist | ❌ |
| GET | `/api/v1/wishlist/{user_id}/check/{product_id}` | Check if in wishlist | ❌ |

### Promotions (Commerce Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/promotions/validate` | Validate promo code | ❌ |

### Payment (Payment Service)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/payments/razorpay/create-order` | Create Razorpay order | ✅ |
| POST | `/api/v1/payments/razorpay/verify` | Verify Razorpay payment | ✅ |
| POST | `/api/v1/payments/process` | Process payment | ✅ |
| GET | `/api/v1/payments/{transaction_id}/status` | Get payment status | ✅ |
| POST | `/api/v1/payments/{transaction_id}/refund` | Refund payment | ✅ |
| GET | `/api/v1/payments/methods` | Get payment methods | ❌ |
| GET | `/api/v1/payments/history` | Get transaction history | ✅ |

## API Schema Definitions

### Common Types

```typescript
interface SuccessResponse<T> {
  data: T;
  message?: string;
  status: 'success';
}

interface ErrorResponse {
  detail: string | string[];
  status_code: number;
  error_type?: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}
```

### User Registration

**Request:**
```typescript
interface UserCreate {
  email: string;           // Required, valid email
  username: string;        // Required, unique, 3-50 chars
  password: string;        // Required, min 8 chars
  full_name?: string;      // Optional, max 100 chars
  phone?: string;          // Optional, valid phone format
  role?: UserRole;         // Optional (admin only), defaults to CUSTOMER
}
```

**Response:**
```typescript
interface UserResponse {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  phone?: string;
  role: UserRole;          // New: User role (ADMIN, STAFF, CUSTOMER)
  is_active: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  is_admin: boolean;      // Backward compatibility
  created_at: string;      // ISO 8601 datetime
  updated_at: string;      // ISO 8601 datetime
  last_login?: string;     // ISO 8601 datetime
}

enum UserRole {
  ADMIN = "admin";
  STAFF = "staff";
  CUSTOMER = "customer";
}
```

### Login

**Request:**
```typescript
interface LoginRequest {
  username: string;        // Email or username
  password: string;        // User password
  remember_me?: boolean;   // Optional, defaults to false
}
```

**Response:**
```typescript
interface LoginResponse {
  user: UserResponse;
  tokens: Token;
  session_id: string;
}

interface Token {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;      // Seconds until expiry
}
```

### Product Response

```typescript
interface ProductResponse {
  id: number;
  name: string;
  description?: string;
  price: number;           // Decimal with 2 places
  compare_price?: number;  // MRP/original price
  sku: string;
  barcode?: string;
  track_inventory: boolean;
  weight?: number;
  category_id: number;
  category?: CategoryResponse;
  images: ProductImage[];
  total_stock: number;
  is_active: boolean;
  is_featured: boolean;
  is_new_arrival: boolean;
  created_at: string;
  updated_at: string;
}

interface ProductDetailResponse extends ProductResponse {
  variants?: ProductVariant[];
  seo_title?: string;
  seo_description?: string;
  tags?: string[];
}

interface ProductImage {
  id: number;
  product_id: number;
  image_url: string;
  alt_text?: string;
  is_primary: boolean;
  display_order: number;
  created_at: string;
}

interface ProductVariant {
  id: number;
  product_id: number;
  sku: string;
  price: number;
  compare_price?: number;
  weight?: number;
  inventory: number;
  options: {
    size?: string;
    color?: string;
    material?: string;
    [key: string]: string | undefined;
  };
}
```

### Order Response

```typescript
interface OrderResponse {
  id: number;
  user_id: number;
  order_number: string;
  status: OrderStatus;
  total_amount: number;
  subtotal: number;
  tax_amount: number;
  shipping_amount: number;
  discount_amount: number;
  currency: string;
  items: OrderItem[];
  shipping_address: AddressResponse;
  billing_address?: AddressResponse;
  payment_status: PaymentStatus;
  payment_method?: string;
  transaction_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  shipped_at?: string;
  delivered_at?: string;
}

interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  price: number;
  total: number;
  product?: ProductResponse;
}

enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded'
}

enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REFUNDED = 'refunded'
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### Common HTTP Status Codes

| Code | Meaning | When to Expect |
|------|---------|----------------|
| 200 | Success | Successful operation |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Authentication Errors

```json
{
  "detail": "Could not validate credentials",
  "status_code": 401
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

### Authentication Endpoints

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 attempts | 5 minutes |
| OTP Send | 5 per hour | 1 hour |
| Password Reset | 3 attempts | 1 hour |

### General API

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Public endpoints | 100 requests | 15 minutes |
| Authenticated endpoints | 1000 requests | 15 minutes |

### Rate Limit Headers

All rate-limited responses include:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Testing

### Health Checks

Test each service is running:

```bash
# Core Service
curl http://localhost:8001/health

# Commerce Service
curl http://localhost:8010/health

# Payment Service
curl http://localhost:8020/health
```

### Authentication Test

```bash
# Register a user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "SecurePass123!",
    "remember_me": true
  }'

# Get user info (using cookies)
curl -X GET http://localhost:8001/api/v1/users/me \
  -b cookies.txt
```

## Support

If you encounter any issues or have questions:

1. Check the service health endpoints first
2. Review the error messages carefully
3. Ensure proper authentication headers/cookies
4. Verify rate limits haven't been exceeded