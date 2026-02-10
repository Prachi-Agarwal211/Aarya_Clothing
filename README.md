# Aarya Clothing - E-Commerce Platform

A modern, scalable e-commerce platform for women's clothing built with microservices architecture. Features include user authentication, product catalog, shopping cart, order management, admin dashboard, staff operations, customer support chat, and secure payment processing.

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (version 29.2.0+)
- **Node.js 18+** (Node.js 25.6.0+ recommended)
- **Python 3.11+**

### One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd Aarya_Clothing

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d --build

# Check service status
docker-compose ps
```

### Access Points
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Core API | http://localhost:8001/docs | Auth & Users |
| Commerce API | http://localhost:8010/docs | Products, Cart, Orders |
| Payment API | http://localhost:8020/docs | Payment Processing |
| Admin API | http://localhost:8004/docs | Dashboard, Analytics, Chat |
| Meilisearch | http://localhost:7700 | Full-text search engine |
| PostgreSQL | localhost:5432 | Primary database |
| Redis | localhost:6379 | Cache & sessions |

## 🏗️ Architecture

### Microservices Design
```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│                          Port 3000                                │
└──────────────┬──────────────────┬─────────────────┬──────────────┘
               │                  │                 │
    ┌──────────▼──────┐  ┌───────▼───────┐  ┌─────▼──────────┐
    │   CORE SERVICE  │  │   COMMERCE    │  │ PAYMENT SERVICE│
    │   Port 8001     │  │   Port 8010   │  │   Port 8020    │
    │  Auth & Users   │  │ Products/Cart │  │  Razorpay      │
    │  Sessions/OTP   │  │ Orders/Search │  │  Stripe        │
    └────────┬────────┘  └───────┬───────┘  └──────┬─────────┘
             │                   │                  │
    ┌────────▼────────┐          │                  │
    │  ADMIN SERVICE  │          │                  │
    │   Port 8004     │          │                  │
    │  Dashboard      │          │                  │
    │  Analytics/Chat │          │                  │
    └────────┬────────┘          │                  │
             │                   │                  │
    ┌────────┴───────────────────┴──────────────────┘
    │
    ├──►  PostgreSQL (5432)     ──  Primary database
    ├──►  Redis (6379)          ──  Cache & sessions
    └──►  Meilisearch (7700)    ──  Full-text search
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js, TypeScript, Tailwind CSS | UI framework |
| Backend | FastAPI, SQLAlchemy, Pydantic | API services |
| Database | PostgreSQL | Persistent storage |
| Cache | Redis | Sessions, cart, real-time |
| Search | Meilisearch | Product full-text search |
| Payments | Razorpay, Stripe | Payment processing |
| Infrastructure | Docker, Nginx | Deployment |

## 📁 Project Structure

```
Aarya_Clothing/
├── README.md
├── docker-compose.yml
├── .env.example
├── frontend/                        # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── services/
│   ├── core/                        # Auth service (port 8001)
│   │   ├── main.py
│   │   ├── models/user.py
│   │   ├── service/auth_service.py
│   │   └── Dockerfile
│   ├── commerce/                    # Commerce service (port 8010)
│   │   ├── main.py
│   │   ├── models/                  # Product, Order, Cart models
│   │   ├── service/                 # Business logic services
│   │   └── Dockerfile
│   ├── payment/                     # Payment service (port 8020)
│   │   ├── main.py
│   │   ├── models/payment.py
│   │   └── Dockerfile
│   └── admin/                       # Admin service (port 8004)
│       ├── main.py
│       ├── models/                  # Chat, Landing, Analytics models
│       ├── schemas/admin.py
│       └── Dockerfile
├── docker/
│   ├── postgres/init.sql            # Database initialization
│   ├── nginx/nginx.prod.conf        # Reverse proxy config
│   └── redis/redis.conf
└── tests/
    ├── conftest.py                  # Pytest fixtures
    ├── test_all_services.py         # Comprehensive test suite
    └── run_mock_tests.py            # Standalone mock tests
```

## ✨ Features

### 🛍️ Customer Features
- **Product Catalog** — Browse with sorting (price, name, popularity, newest) and advanced filtering
- **Full-Text Search** — Meilisearch-powered typo-tolerant product search
- **Shopping Cart** — Real-time cart with quantity updates, promo codes, shipping calculation
- **Order Management** — Create, track, cancel orders with full history
- **Wishlist** — Save products for later
- **Reviews & Ratings** — Write and browse product reviews
- **Returns & Exchanges** — Submit return/exchange requests
- **Customer Support Chat** — Real-time chat with staff
- **Customer Profile** — Order history, stats, saved addresses

### 🔐 Authentication & Security
- **JWT Authentication** — Secure token-based auth with refresh tokens
- **OTP Verification** — Email and phone verification
- **Password Reset** — Secure forgot-password flow
- **Role-Based Access** — Customer, Staff, Admin roles
- **Rate Limiting** — API endpoint protection
- **CORS Protection** — Cross-origin request security

### 📊 Admin Dashboard
- **Dashboard Overview** — Revenue, orders, customers, inventory alerts
- **Revenue Analytics** — Daily/monthly/yearly revenue reports
- **Customer Analytics** — Growth metrics and top customers
- **Product Analytics** — Top-selling products, performance data
- **Order Management** — Bulk status updates, detailed order views
- **User Management** — Search, activate/deactivate users
- **Inventory Alerts** — Low-stock and out-of-stock notifications
- **Chat Management** — Assign/manage customer support rooms
- **Landing Page Config** — Dynamic homepage content management
- **Export** — CSV export for orders and products

### 👷 Staff Operations
- **Inventory Management** — Add/adjust stock, bulk updates, movement history
- **Order Processing** — Process, ship, and track orders
- **Product Variants** — CRUD for sizes, colors, SKUs
- **Task Management** — Assigned tasks with completion tracking
- **Notifications** — Real-time alerts for inventory and orders
- **Reports** — Inventory summary, processed orders report

### 💳 Payment Processing
- **Razorpay** — Primary payment gateway for India (UPI, Cards, Wallets)
- **Stripe** — International payment support
- **Refunds** — Automated refund processing
- **Webhooks** — Payment event processing
- **Transaction History** — Full payment audit trail

## 📡 API Endpoints

### Core Service (Port 8001)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | User registration |
| POST | `/api/v1/auth/login` | Login with JWT |
| POST | `/api/v1/auth/logout` | Logout & invalidate session |
| POST | `/api/v1/auth/forgot-password` | Initiate password reset |
| POST | `/api/v1/auth/reset-password` | Complete password reset |
| GET | `/api/v1/users/me` | Current user profile |

### Commerce Service (Port 8010)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products/browse` | Browse with filters & sorting |
| GET | `/api/v1/products/search` | Meilisearch full-text search |
| GET | `/api/v1/products/slug/{slug}` | Get product by slug |
| GET | `/api/v1/products/{id}/related` | Related products |
| POST | `/api/v1/cart/{id}/add` | Add item to cart |
| PUT | `/api/v1/cart/{id}/update-quantity` | Update cart quantity |
| POST | `/api/v1/cart/{id}/apply-promo` | Apply promo code |
| GET | `/api/v1/cart/{id}/summary` | Cart totals + shipping |
| POST | `/api/v1/orders` | Create order |
| GET | `/api/v1/me/profile` | Customer profile + stats |
| POST | `/api/v1/chat/rooms` | Start support chat |
| GET | `/api/v1/landing/featured` | Homepage content |
| POST | `/api/v1/returns/{id}/exchange` | Exchange request |

### Admin Service (Port 8004)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard/overview` | Dashboard stats |
| GET | `/api/v1/admin/analytics/revenue` | Revenue analytics |
| GET | `/api/v1/admin/orders` | Manage all orders |
| POST | `/api/v1/admin/orders/bulk-update` | Bulk status update |
| GET | `/api/v1/admin/users` | User management |
| GET | `/api/v1/admin/inventory/low-stock` | Low stock alerts |
| POST | `/api/v1/admin/export/orders` | Export orders CSV |
| GET | `/api/v1/staff/dashboard` | Staff dashboard |
| POST | `/api/v1/staff/inventory/add-stock` | Add inventory |
| POST | `/api/v1/staff/orders/{id}/ship` | Ship order |

### Payment Service (Port 8020)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payments/create-order` | Create Razorpay order |
| POST | `/api/v1/payments/verify` | Verify payment |
| POST | `/api/v1/payments/refund` | Process refund |
| POST | `/api/v1/payments/webhook` | Payment webhook |

## 🧪 Testing

### Run All Tests
```bash
# Standalone mock tests (no dependencies)
python tests/run_mock_tests.py

# Full pytest suite
cd tests && pip install -r requirements.txt && pytest -v

# Individual service tests
pytest tests/test_all_services.py -v -k "core"
pytest tests/test_all_services.py -v -k "commerce"
pytest tests/test_all_services.py -v -k "admin"
pytest tests/test_all_services.py -v -k "payment"
```

### Health Checks
```bash
curl http://localhost:8001/health   # Core
curl http://localhost:8010/health   # Commerce
curl http://localhost:8020/health   # Payment
curl http://localhost:8004/health   # Admin
```

## 🚀 Deployment

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d --build

# Scale services
docker-compose up -d --scale core=2 --scale commerce=2
```

### Environment Variables
See [.env.example](.env.example) for required configuration.

## 📚 Documentation

- [Development Setup](DEVELOPMENT_SETUP.md) — Local dev guide
- [Architecture](docs/architecture.md) — System design
- [Deployment Guide](docs/deployment-guide.md) — Production deployment
- [Payment Service](services/payment/README.md) — Payment integration

## 🔒 Security

- JWT Authentication with refresh tokens
- Bcrypt password hashing
- CORS protection & rate limiting
- SQL injection prevention (parameterized queries)
- Input validation with Pydantic
- Secure HTTP-only cookies

---

**Version**: 3.0.0
**Last Updated**: February 2026
**Compatible**: Python 3.11, Docker 29.2.0, Node.js 25.6.0