# Aarya Clothing - Development Setup & Testing Guide

## Overview
This guide covers setting up the complete Aarya Clothing e-commerce platform for development and testing, including virtual environments, database setup, and authentication testing.

## Quick Start (Recommended)

### One-Command Setup
If you have already set up the virtual environments (run `setup_compatible_env.bat` first):

```bash
# Start all services for local development
start-local.bat
```

This will start:
- PostgreSQL and Redis (Docker containers)
- Core Service (Port 8001)
- Commerce Service (Port 8010)
- Payment Service (Port 8020)
- Frontend (Port 3000)

### Test Your Setup
```bash
# Run connection tests
test-connection.bat
```

## Prerequisites

### Required Software
- **Python 3.11+** (Docker uses Python 3.11-slim for compatibility)
- **Docker & Docker Compose** (version 29.2.0+)
- **Node.js 18+** (Node.js 25.6.0+ recommended)
- **Git**

### System Requirements
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 10GB free space
- **Ports**: 3000, 8001, 8010, 8020, 5432, 6379 must be available

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│                       Port 3000                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│   CORE    │  │ COMMERCE  │  │  PAYMENT  │
│ Port 8001 │  │ Port 8010 │  │ Port 8020 │
│  Auth &   │  │ Products  │  │ Razorpay  │
│  Users    │  │ Cart/Ord  │  │  Stripe   │
└─────┬─────┘  └─────┬─────┘  └─────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
  ┌───────────┐            ┌───────────┐
  │ PostgreSQL│            │   Redis   │
  │  Port 5432│            │  Port 6379│
  └───────────┘            └───────────┘
```

## Environment Setup

### 1. Project Structure
```
Aarya_Clothing/
├── docker-compose.yml
├── .env.example
├── venv_core/              # Core service virtual environment
├── venv_commerce/          # Commerce service virtual environment  
├── venv_payment/           # Payment service virtual environment
├── frontend/               # Next.js frontend
├── services/
│   ├── core/              # Authentication service (Port 8001)
│   ├── commerce/          # Product/cart/orders (Port 8010)
│   └── payment/           # Payment processing (Port 8020)
└── docker/
    ├── postgres/init.sql
    └── redis/redis.conf
```

### 2. Virtual Environment Setup

#### Core Service Virtual Environment
```bash
# Create virtual environment
python -m venv venv_core

# Activate (Windows)
venv_core\Scripts\activate

# Install dependencies
pip install fastapi==0.109.0 uvicorn==0.27.0 python-multipart==0.0.6
pip install sqlalchemy==2.0.25 psycopg2==2.9.11 redis==5.0.1
pip install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4
pip install bcrypt==4.1.2 email-validator==2.1.0 python-dotenv==1.0.0
pip install httpx==0.26.0 pydantic-settings==2.1.0
```

#### Commerce Service Virtual Environment
```bash
# Create virtual environment
python -m venv venv_commerce

# Activate (Windows)
venv_commerce\Scripts\activate

# Install dependencies
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0
pip install pydantic==2.12.5 pydantic-settings==2.1.0
pip install python-multipart==0.0.6 sqlalchemy==2.0.25
pip install psycopg2==2.9.11 redis==5.0.1
pip install python-jose[cryptography]==3.3.0 python-dotenv==1.2.1
pip install httpx==0.26.0 boto3==1.34.34
```

#### Payment Service Virtual Environment
```bash
# Create virtual environment
python -m venv venv_payment

# Activate (Windows)
venv_payment\Scripts\activate

# Install dependencies
pip install fastapi==0.109.0 uvicorn[standard]==0.27.0
pip install pydantic==2.12.5 pydantic-settings==2.1.0
pip install python-multipart==0.0.6 sqlalchemy==2.0.25
pip install psycopg2==2.9.11 redis==5.0.1
pip install python-jose[cryptography]==3.3.0 python-dotenv==1.2.1
pip install httpx==0.26.0 razorpay==2.0.0 cryptography==42.0.8
pip install email-validator==2.1.0
```

### 3. Database Setup

#### Start Database Containers
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Check status
docker-compose ps

# View logs
docker-compose logs -f postgres redis
```

#### Database Initialization
The PostgreSQL database is automatically initialized with:
- Users table with admin user (admin@aarya.com / admin123)
- OTP table for verification
- Basic categories
- All necessary indexes and triggers

### 4. Environment Configuration

#### Copy Environment File
```bash
cp .env.example .env
```

#### Required Environment Variables
```bash
# Database
POSTGRES_PASSWORD=change_this_password_in_production
DATABASE_URL=postgresql://postgres:change_this_password_in_production@localhost:5432/aarya_clothing

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
SECRET_KEY=your-encryption-secret-key-change-in-production

# Token Settings
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=1440

# URLs
NEXT_PUBLIC_API_URL=http://localhost:8001
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8001"]
```

## Docker Setup

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Aarya_Clothing.git
   cd Aarya_Clothing
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Check service status**
   ```bash
   docker-compose ps
   ```

### Docker Build Notes

#### Fixed Issues
1. **Python Version**: Using Python 3.11-slim base images for compatibility
2. **PostgreSQL Dependencies**: Added `libpq-dev` to all Dockerfiles for psycopg2 compilation
3. **JWT Dependencies**: Added `python-jose[cryptography]` to commerce service
4. **Missing Schemas**: Added `OrderUpdate` schema to commerce service
5. **Import Fixes**: Fixed JWT imports to use `from jose import jwt`

#### Rebuilding Services
If you make changes to service code:
```bash
# Rebuild specific service
docker-compose up -d --build <service-name>

# Force rebuild without cache
docker-compose build --no-cache <service-name>
```

## Service Startup

### 1. Core Service (Authentication)
```bash
# Activate virtual environment
venv_core\Scripts\activate

# Run the service
cd services\core
python main.py

# Service will be available at: http://localhost:8001
# Health check: http://localhost:8001/health
# API docs: http://localhost:8001/docs
```

### 2. Commerce Service
```bash
# Activate virtual environment
venv_commerce\Scripts\activate

# Run the service
cd services\commerce
python main.py

# Service will be available at: http://localhost:8010
# Health check: http://localhost:8010/health
# API docs: http://localhost:8010/docs
```

### 3. Payment Service
```bash
# Activate virtual environment
venv_payment\Scripts\activate

# Run the service
cd services\payment
python main.py

# Service will be available at: http://localhost:8020
# Health check: http://localhost:8020/health
# API docs: http://localhost:8020/docs
```

### 4. Frontend
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at: http://localhost:3000
```

## Authentication Testing

### 1. Health Checks
```bash
# Test all services are running
curl http://localhost:8001/health  # Core service
curl http://localhost:8010/health  # Commerce service
curl http://localhost:8020/health  # Payment service
```

### 2. User Registration
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "TestPassword123!"
  }'
```

### 3. User Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "testuser",
    "password": "TestPassword123!",
    "remember_me": true
  }'
```

### 4. Get Current User
```bash
curl -X GET "http://localhost:8001/api/v1/users/me" \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

### 5. Token Refresh
```bash
curl -X POST "http://localhost:8001/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -c cookies.txt
```

### 6. Logout
```bash
curl -X POST "http://localhost:8001/api/v1/auth/logout" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -c cookies.txt
```

## API Endpoints Reference

### Core Service (Port 8001)

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password

#### OTP Verification
- `POST /api/v1/auth/send-otp` - Send OTP
- `POST /api/v1/auth/verify-otp` - Verify OTP
- `POST /api/v1/auth/resend-otp` - Resend OTP

#### Users
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update current user
- `GET /api/v1/users/{user_id}` - Get user by ID

#### Admin
- `GET /api/v1/admin/users` - List all users
- `PATCH /api/v1/admin/users/{user_id}/activate` - Activate user
- `PATCH /api/v1/admin/users/{user_id}/deactivate` - Deactivate user

### Commerce Service (Port 8010)

#### Products
- `GET /api/v1/products` - List products
- `GET /api/v1/products/{product_id}` - Get product
- `GET /api/v1/products/search` - Search products

#### Categories
- `GET /api/v1/categories` - List categories
- `GET /api/v1/categories/tree` - Get category tree
- `GET /api/v1/categories/{category_id}` - Get category

#### Cart
- `GET /api/v1/cart/{user_id}` - Get cart
- `POST /api/v1/cart/{user_id}/add` - Add to cart
- `DELETE /api/v1/cart/{user_id}/remove/{product_id}` - Remove from cart
- `DELETE /api/v1/cart/{user_id}/clear` - Clear cart

#### Orders
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{user_id}` - Get user orders
- `GET /api/v1/orders/{order_id}/details` - Get order details

### Payment Service (Port 8020)

#### Payments
- `POST /api/v1/payments/process` - Process payment
- `GET /api/v1/payments/{transaction_id}/status` - Get payment status
- `POST /api/v1/payments/{transaction_id}/refund` - Refund payment
- `GET /api/v1/payments/methods` - Get payment methods

#### Razorpay
- `POST /api/v1/payments/razorpay/create-order` - Create Razorpay order
- `POST /api/v1/payments/razorpay/verify` - Verify Razorpay payment

## Troubleshooting

### Common Issues

#### 1. Docker Service Won't Start
**Problem**: Service keeps restarting with errors
**Solution**: 
```bash
# Check logs
docker-compose logs <service-name>

# Common fixes:
# 1. Rebuild the service
docker-compose up -d --build <service-name>

# 2. Force rebuild without cache
docker-compose build --no-cache <service-name>

# 3. Check for port conflicts
netstat -ano | findstr :8001
```

#### 2. Common Docker Errors and Solutions

**ModuleNotFoundError: No module named 'jwt'**
- Fixed by adding `python-jose[cryptography]==3.3.0` to requirements.txt
- Rebuild service: `docker-compose up -d --build commerce`

**ImportError: cannot import name 'OrderUpdate'**
- Fixed by adding OrderUpdate schema to `services/commerce/schemas/order.py`
- Rebuild service: `docker-compose up -d --build commerce`

**psycopg2 build errors**
- Fixed by adding `libpq-dev` to Dockerfiles
- Rebuild with: `docker-compose build --no-cache <service-name>`

**SyntaxError in imports**
- Check import statements in Python files
- Fixed syntax error in `services/commerce/schemas/address.py`

#### 3. Python Package Installation Issues
**Problem**: `pydantic-core` requires Rust compilation
**Solution**: Use Python 3.11 with updated packages or install Rust toolchain

#### 4. PostgreSQL Connection Issues
**Problem**: `psycopg2-binary` requires Visual C++ build tools
**Solution**: Use `psycopg2` instead of `psycopg2-binary`

#### 3. Port Conflicts
**Problem**: Services can't start due to port conflicts
**Solution**: 
```bash
# Check what's using a port
netstat -ano | findstr :8001

# Kill the process
taskkill /PID <PID> /F
```

#### 4. Database Connection Issues
**Problem**: Services can't connect to database
**Solution**: 
```bash
# Check PostgreSQL container
docker-compose exec postgres pg_isready -U postgres

# Check Redis container
docker-compose exec redis redis-cli ping

# Reset database
docker-compose down -v
docker-compose up -d postgres redis
```

### Service Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f postgres
docker-compose logs -f redis

# View Python service logs (when running locally)
# Check the terminal where the service is running
```

## Development Workflow

### 1. Daily Development Setup
```bash
# 1. Start databases
docker-compose up -d postgres redis

# 2. Activate core service environment
venv_core\Scripts\activate
cd services\core
python main.py

# 3. In new terminal, activate commerce environment
venv_commerce\Scripts\activate
cd services\commerce
python main.py

# 4. In new terminal, activate payment environment
venv_payment\Scripts\activate
cd services\payment
python main.py

# 5. In new terminal, start frontend
cd frontend
npm run dev
```

### 2. Testing Authentication Flow
1. Register a new user via API or frontend
2. Login and receive authentication cookies
3. Access protected endpoints using cookies
4. Test token refresh mechanism
5. Test logout functionality

### 3. Code Changes & Hot Reload
- **Backend services**: Restart manually after code changes
- **Frontend**: Hot reload enabled by Next.js
- **Database**: Changes to init.sql require container rebuild

## Security Considerations

### Development Environment
- Change default passwords before production
- Use HTTPS in production (configure reverse proxy)
- Keep secrets out of version control
- Regularly update dependencies

### Authentication Security
- JWT tokens with expiration
- HTTP-only cookies for session management
- Password complexity requirements
- Rate limiting on authentication endpoints
- Account lockout after failed attempts

## Production Deployment Notes

### Environment Variables
```bash
# Production-specific variables
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
COOKIE_SECURE=true
POSTGRES_PASSWORD=<strong_password>
JWT_SECRET_KEY=<strong_secret>
```

### Docker Production
```bash
# Build and start all services
docker-compose up -d --build

# Scale services if needed
docker-compose up -d --scale core=2 --scale commerce=2
```

### Monitoring
- Health endpoints: `/health` on all services
- Application logs via Docker
- Database performance metrics
- Redis memory usage

## Next Steps

1. **Complete Service Setup**: Set up commerce and payment services
2. **Frontend Integration**: Connect frontend to backend APIs
3. **Testing**: Write comprehensive tests for all endpoints
4. **CI/CD**: Set up automated testing and deployment
5. **Monitoring**: Add application monitoring and logging
6. **Performance**: Optimize database queries and add caching

## Support

For issues:
1. Check service logs for error messages
2. Verify all containers are running: `docker-compose ps`
3. Check port availability
4. Review environment variables
5. Consult API documentation at `/docs` endpoints

---

**Last Updated**: February 2026  
**Version**: 2.0.0  
**Compatible**: Python 3.11, Docker 29.2.0, Node.js 25.6.0
