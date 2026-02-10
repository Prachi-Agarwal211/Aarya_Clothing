# API Schemas - Request & Response Formats

This document provides detailed schemas for all API requests and responses.

## 📝 Common Types

### Standard Response Format

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

---

## 🔐 Authentication Schemas

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

### Password Change

**Request:**
```typescript
interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
```

### Password Reset

**Request:**
```typescript
interface ForgotPasswordRequest {
  email: string;
}

interface PasswordResetConfirm {
  token: string;
  new_password: string;
}
```

---

## 🔢 OTP Schemas

### Send OTP

**Request:**
```typescript
interface OTPSendRequest {
  identifier: string;      // Email or phone number
  otp_type: 'EMAIL' | 'WHATSAPP';
  purpose?: 'LOGIN' | 'REGISTER' | 'PASSWORD_RESET';
}
```

**Response:**
```typescript
interface OTPSendResponse {
  message: string;
  otp_id: string;
  expires_at: string;      // ISO 8601 datetime
  resend_cooldown: number; // Seconds
}
```

### Verify OTP

**Request:**
```typescript
interface OTPVerifyRequest {
  identifier: string;
  otp_code: string;        // 6-digit code
  otp_type: 'EMAIL' | 'WHATSAPP';
}
```

**Response:**
```typescript
interface OTPVerifyResponse {
  verified: boolean;
  message: string;
  temporary_token?: string; // For registration flows
}
```

### Resend OTP

**Request:**
```typescript
interface OTPResendRequest {
  identifier: string;
  otp_type: 'EMAIL' | 'WHATSAPP';
}
```

---

## 🛍️ Product Schemas

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

### Category Response

```typescript
interface CategoryResponse {
  id: number;
  name: string;
  slug: string;
  description?: string;
  image_url?: string;
  parent_id?: number;
  display_order: number;
  is_active: boolean;
  is_featured: boolean;
  seo_title?: string;
  seo_description?: string;
  created_at: string;
  updated_at: string;
}

interface CategoryWithChildren extends CategoryResponse {
  children: CategoryResponse[];
  product_count: number;
}

interface CategoryTree {
  categories: CategoryWithChildren[];
}
```

---

## 🛒 Cart Schemas

### Cart Item

```typescript
interface CartItem {
  product_id: number;
  quantity: number;
  variant_id?: number;
}

interface CartResponse {
  user_id: number;
  items: CartItemResponse[];
  total: number;           // Total price
  total_items: number;     // Total quantity
  updated_at: string;
}

interface CartItemResponse {
  product_id: number;
  name: string;
  price: number;
  quantity: number;
  image_url?: string;
  variant?: ProductVariant;
  subtotal: number;
}
```

---

## 📦 Order Schemas

### Order Create

**Request:**
```typescript
interface OrderCreate {
  user_id: number;
  shipping_address: AddressCreate;
  billing_address?: AddressCreate;
  promo_code?: string;
  notes?: string;
  payment_method: 'razorpay' | 'stripe';
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

---

## 📍 Address Schemas

### Address Create/Update

```typescript
interface AddressCreate {
  type: AddressType;
  name: string;            // Full name
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default?: boolean;
}

interface AddressUpdate {
  type?: AddressType;
  name?: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  is_default?: boolean;
}

interface AddressResponse {
  id: number;
  user_id: number;
  type: AddressType;
  name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

enum AddressType {
  SHIPPING = 'shipping',
  BILLING = 'billing'
}
```

---

## 💳 Payment Schemas

### Razorpay Order

**Request:**
```typescript
interface RazorpayOrderRequest {
  amount: number;          // Amount in paise (100 paise = 1 INR)
  currency: string;        // Defaults to 'INR'
  receipt?: string;        // Your order ID
  notes?: Record<string, string>;
}
```

**Response:**
```typescript
interface RazorpayOrderResponse {
  id: string;              // Razorpay order ID
  entity: string;
  amount: number;
  amount_paid: number;
  amount_due: number;
  currency: string;
  receipt: string;
  status: string;
  attempts: number;
  notes: Record<string, string>;
  created_at: number;
}
```

### Payment Verification

**Request:**
```typescript
interface RazorpayPaymentVerification {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}
```

### Payment Response

```typescript
interface PaymentResponse {
  transaction_id: string;
  order_id: number;
  user_id: number;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_method: PaymentMethod;
  gateway_transaction_id?: string;
  gateway_response?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

enum PaymentMethod {
  RAZORPAY = 'razorpay',
  STRIPE = 'stripe',
  CASH_ON_DELIVERY = 'cod'
}
```

### Refund

**Request:**
```typescript
interface RefundRequest {
  transaction_id: string;
  amount?: number;         // Partial refund amount
  reason: string;
}
```

**Response:**
```typescript
interface RefundResponse {
  refund_id: string;
  transaction_id: string;
  amount: number;
  status: RefundStatus;
  reason: string;
  processed_at?: string;
  gateway_refund_id?: string;
}

enum RefundStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}
```

---

## � Role Management Schemas

### Update User Role

**Request:**
```typescript
interface RoleUpdateRequest {
  role: UserRole;           // New role to assign
}
```

**Response:**
```typescript
interface RoleUpdateResponse extends UserResponse {
  // Same as UserResponse with updated role
}
```

### List Users by Role

**Parameters:**
- `role`: UserRole (ADMIN, STAFF, CUSTOMER)
- `skip`: number (default: 0)
- `limit`: number (default: 100)

**Response:**
```typescript
interface UsersByRoleResponse {
  users: UserResponse[];
  total: number;
  skip: number;
  limit: number;
}
```

---

## �💝 Wishlist Schemas

### Wishlist Item

**Request:**
```typescript
interface WishlistItemCreate {
  product_id: number;
}
```

**Response:**
```typescript
interface WishlistItemResponse {
  id: number;
  user_id: number;
  product_id: number;
  product?: ProductResponse;
  created_at: string;
}

interface WishlistResponse {
  user_id: number;
  items: WishlistItemResponse[];
  total_items: number;
}
```

---

## 🎫 Promotion Schemas

### Promotion Validation

**Request:**
```typescript
interface PromotionValidateRequest {
  code: string;
  user_id: number;
  order_total: number;
  product_ids?: number[];
}
```

**Response:**
```typescript
interface PromotionValidateResponse {
  valid: boolean;
  promotion?: PromotionResponse;
  discount_amount: number;
  final_total: number;
  message?: string;
}

interface PromotionResponse {
  id: number;
  code: string;
  name: string;
  description?: string;
  type: PromotionType;
  value: number;
  minimum_amount?: number;
  usage_limit?: number;
  usage_count: number;
  user_usage_limit?: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

enum PromotionType {
  PERCENTAGE = 'percentage',
  FIXED_AMOUNT = 'fixed_amount',
  FREE_SHIPPING = 'free_shipping'
}
```

---

## 📊 Inventory Schemas

### Inventory Response

```typescript
interface InventoryResponse {
  id: number;
  product_id: number;
  sku: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  low_stock_threshold: number;
  track_quantity: boolean;
  allow_backorder: boolean;
  location?: string;
  last_updated: string;
}

interface StockAdjustment {
  sku: string;
  adjustment: number;     // Positive for addition, negative for removal
  reason: string;
  notes?: string;
}

interface LowStockItem {
  product_id: number;
  product_name: string;
  sku: string;
  current_stock: number;
  threshold: number;
  shortage: number;
}
```

---

## 📝 Review Schemas

### Review Create

**Request:**
```typescript
interface ReviewCreate {
  product_id: number;
  rating: number;          // 1-5 stars
  title?: string;
  content?: string;
  images?: string[];       // Image URLs
}
```

**Response:**
```typescript
interface ReviewResponse {
  id: number;
  product_id: number;
  user_id: number;
  user_name: string;
  rating: number;
  title?: string;
  content?: string;
  images?: string[];
  is_verified_purchase: boolean;
  is_approved: boolean;
  helpful_count: number;
  created_at: string;
  updated_at: string;
}
```

---

## 🚚 Order Tracking Schemas

### Order Tracking

```typescript
interface OrderTrackingResponse {
  id: number;
  order_id: number;
  status: OrderStatus;
  location?: string;
  description: string;
  timestamp: string;
  is_current: boolean;
}
```

---

## 🔄 Return Request Schemas

### Return Request Create

**Request:**
```typescript
interface ReturnRequestCreate {
  order_id: number;
  order_item_id: number;
  reason: ReturnReason;
  description: string;
  images?: string[];
  refund_preference: 'refund' | 'exchange' | 'store_credit';
}
```

**Response:**
```typescript
interface ReturnRequestResponse {
  id: number;
  order_id: number;
  order_item_id: number;
  user_id: number;
  reason: ReturnReason;
  description: string;
  images?: string[];
  status: ReturnStatus;
  refund_preference: string;
  refund_amount?: number;
  admin_notes?: string;
  created_at: string;
  updated_at: string;
}

enum ReturnReason {
  DAMAGED = 'damaged',
  WRONG_ITEM = 'wrong_item',
  NOT_AS_DESCRIBED = 'not_as_described',
  SIZE_ISSUE = 'size_issue',
  QUALITY_ISSUE = 'quality_issue',
  NO_LONGER_NEEDED = 'no_longer_needed',
  OTHER = 'other'
}

enum ReturnStatus {
  REQUESTED = 'requested',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  RECEIVED = 'received',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}
```

---

## 🔍 Search & Filtering

### Product Search Parameters

```typescript
interface ProductSearchParams {
  q?: string;              // Search query
  category_id?: number;
  min_price?: number;
  max_price?: number;
  new_arrivals?: boolean;
  featured?: boolean;
  in_stock?: boolean;
  sort_by?: 'name' | 'price' | 'created_at' | 'popularity';
  sort_order?: 'asc' | 'desc';
  skip?: number;
  limit?: number;
}
```

### Order History Parameters

```typescript
interface OrderHistoryParams {
  status?: OrderStatus;
  payment_status?: PaymentStatus;
  date_from?: string;      // ISO 8601 date
  date_to?: string;        // ISO 8601 date
  skip?: number;
  limit?: number;
}
```

---

## 📈 Analytics & Reports

### Sales Report

```typescript
interface SalesReport {
  period: string;
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  top_products: ProductSales[];
  sales_by_category: CategorySales[];
  daily_sales: DailySales[];
}

interface ProductSales {
  product_id: number;
  product_name: string;
  quantity_sold: number;
  revenue: number;
}

interface CategorySales {
  category_id: number;
  category_name: string;
  quantity_sold: number;
  revenue: number;
}

interface DailySales {
  date: string;
  orders: number;
  revenue: number;
}
```

These schemas provide comprehensive type definitions for all API interactions. Use them as reference when implementing your frontend application to ensure proper request/response handling.
