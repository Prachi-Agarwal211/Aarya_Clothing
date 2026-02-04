# Aarya Clothing - Microservices Architecture

## Executive Summary

This document outlines the microservices architecture for Aarya Clothing, designed for VPS deployment with Next.js frontend and FastAPI backend services.

---

## 1. Service Architecture

### 1.1 Microservices Overview

```
Microservices Architecture:
├── Core Platform Service (Port 8001)
│   ├── User Management
│   ├── Authentication (JWT)
│   ├── Session Management
│   └── OTP Verification
│
├── Commerce Service (Port 8010)
│   ├── Product Catalog
│   ├── Inventory Management
│   ├── Shopping Cart
│   └── Order Processing
│
├── Payment Service (Port 8020)
│   ├── Payment Processing
│   └── Fraud Detection
│
└── Frontend (Port 3000)
    └── Next.js Application
```

### 1.2 Service Ports

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| core | 8001 | HTTP | Auth, Users, OTP |
| commerce | 8010 | HTTP | Products, Cart, Orders |
| payment | 8020 | HTTP | Payment Processing |
| frontend | 3000 | HTTP | Next.js UI |
| postgres | 5432 | TCP | Database |
| redis | 6379 | TCP | Cache/Sessions |

---

## 2. Network Architecture

### 2.1 Communication Pattern

```
Frontend (Next.js:3000)
    │
    ▼
┌─────────────────────────────────────┐
│      Backend Services               │
│  ├── Core Platform (:8001)         │
│  ├── Commerce (:8010)              │
│  └── Payment (:8020)               │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│         Data Layer                  │
│  ├── PostgreSQL (:5432)            │
│  └── Redis (:6379)                 │
└─────────────────────────────────────┘
```

### 2.2 Docker Networks

```yaml
networks:
  frontend_network:
    driver: bridge

  backend_network:
    driver: bridge
```

---

## 3. Database Architecture

### 3.1 PostgreSQL Tables

```sql
-- Core Platform (users, otps)
CREATE TABLE users (...);
CREATE TABLE otps (...);

-- Commerce (products, orders)
CREATE TABLE products (...);
CREATE TABLE orders (...);
CREATE TABLE order_items (...);
```

### 3.2 Redis Usage

```
Redis Namespaces:
├── session:{id}        → User sessions
├── cart:{user_id}      → Shopping cart
├── cache:{key}         → Application cache
├── otp:{key}          → OTP codes
└── blacklist:{token}   → Blacklisted tokens
```

---

## 4. Project Structure

```
Aarya_Clothing/
├── docker-compose.yml
├── .env.example
│
├── frontend/                   # Next.js Frontend
│   ├── Dockerfile
│   ├── src/
│   └── ...
│
├── services/
│   ├── core/                   # Core Platform (Port 8001)
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── core/config.py
│   │   ├── core/redis_client.py
│   │   ├── database/database.py
│   │   ├── models/user.py
│   │   ├── models/otp.py
│   │   ├── schemas/auth.py
│   │   ├── schemas/otp.py
│   │   └── service/
│   │       ├── auth_service.py
│   │       └── otp_service.py
│   │
│   ├── commerce/               # Commerce Service (Port 8010)
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── core/config.py
│   │   ├── core/redis_client.py
│   │   ├── database/database.py
│   │   ├── models/product.py
│   │   ├── models/order.py
│   │   └── schemas/
│   │       ├── product.py
│   │       └── order.py
│   │
│   └── payment/                # Payment Service (Port 8020)
│       ├── Dockerfile
│       ├── main.py
│       ├── requirements.txt
│       └── core/config.py
│
└── docker/
    ├── postgres/init.sql
    └── redis/redis.conf
```

---

## 5. API Endpoints

### 5.1 Core Platform (Port 8001)

```
Authentication:
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/change-password

OTP:
POST /api/v1/auth/send-otp
POST /api/v1/auth/verify-otp
POST /api/v1/auth/resend-otp

Users:
GET /api/v1/users/me
PATCH /api/v1/users/me
GET /api/v1/users/{user_id}

Admin:
GET /api/v1/admin/users
PATCH /api/v1/admin/users/{user_id}/activate
PATCH /api/v1/admin/users/{user_id}/deactivate
```

### 5.2 Commerce Service (Port 8010)

```
Products:
GET /api/v1/products
GET /api/v1/products/{product_id}
POST /api/v1/products
PATCH /api/v1/products/{product_id}

Cart:
GET /api/v1/cart/{user_id}
POST /api/v1/cart/{user_id}/add
DELETE /api/v1/cart/{user_id}/remove/{product_id}
DELETE /api/v1/cart/{user_id}/clear

Orders:
POST /api/v1/orders
GET /api/v1/orders/{user_id}
GET /api/v1/orders/{order_id}/details
```

### 5.3 Payment Service (Port 8020)

```
Payments:
POST /api/v1/payments/process
POST /api/v1/payments/{transaction_id}/refund
GET /api/v1/payments/{transaction_id}/status
POST /api/v1/payments/verify
```

---

## 6. Environment Variables

### 6.1 Required Variables

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET_KEY=your-super-secret-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 6.2 Optional Variables

```bash
# Payment Gateway (Stripe)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## 7. Deployment

### 7.1 Quick Start

```bash
# 1. Clone and navigate to project
cd Aarya_Clothing

# 2. Copy environment file
cp .env.example .env

# 3. Edit environment variables
nano .env

# 4. Build and start services
docker-compose up -d --build

# 5. Check status
docker-compose ps

# 6. View logs
docker-compose logs -f
```

### 7.2 Service Health Checks

```bash
# Core Platform
curl http://localhost:8001/health

# Commerce Service
curl http://localhost:8010/health

# Payment Service
curl http://localhost:8020/health

# Frontend
curl http://localhost:3000
```

### 7.3 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 8. Monitoring

### 8.1 Health Endpoints

All services expose `/health` endpoint for monitoring:

```json
{
  "status": "healthy",
  "service": "core",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z",
  "dependencies": {
    "redis": "healthy",
    "database": "healthy"
  }
}
```

---

## 9. Security Considerations

### 9.1 Authentication

- JWT-based authentication
- Refresh token rotation
- Session management via Redis
- HTTP-only secure cookies

### 9.2 Network Security

- Services communicate over internal Docker network
- CORS configured for frontend origin
- Rate limiting on authentication endpoints

---

## 10. Future Enhancements

Potential future improvements:

1. **API Gateway** - Nginx/Traefik for centralized routing
2. **Load Balancing** - Horizontal scaling of services
3. **Monitoring** - Prometheus/Grafana integration
4. **Search** - Meilisearch for product search
5. **CDN** - Static asset delivery via CDN
