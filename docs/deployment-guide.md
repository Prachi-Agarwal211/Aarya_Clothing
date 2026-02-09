# Deployment Guide

## Overview

This guide covers the deployment of the Aarya Clothing microservices architecture on a VPS.

## Prerequisites

- Docker & Docker Compose
- At least 4GB RAM available
- Ports 3000, 8001, 8010, 8020, 5432, 6379 available

## Quick Start

### 1. Clone and Navigate

```bash
git clone https://github.com/your-repo/Aarya_Clothing.git
cd Aarya_Clothing
```

### 2. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Required Environment Variables

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET_KEY=your-super-secret-key

# Frontend
NEXT_PUBLIC_API_URL=http://your-domain-or-ip:8001
```

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps
```

### 5. Verify Health

```bash
# Check all services
curl http://localhost:8001/health  # Core
curl http://localhost:8010/health  # Commerce
curl http://localhost:8020/health  # Payment
curl http://localhost:3000          # Frontend
```

## Service Details

### Core Platform (Port 8001)

Handles authentication, user management, and OTP verification.

**Endpoints:**
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/send-otp` - Send OTP
- `POST /api/v1/auth/verify-otp` - Verify OTP
- `GET /api/v1/users/me` - Get current user

### Commerce Service (Port 8010)

Handles products, cart, and orders.

**Endpoints:**
- `GET /api/v1/products` - List products
- `GET /api/v1/products/{id}` - Get product
- `GET /api/v1/cart/{user_id}` - Get cart
- `POST /api/v1/cart/{user_id}/add` - Add to cart
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{user_id}` - Get orders

### Payment Service (Port 8020)

Handles payment processing.

**Endpoints:**
- `POST /api/v1/payments/process` - Process payment
- `POST /api/v1/payments/{id}/refund` - Refund payment
- `GET /api/v1/payments/{id}/status` - Get payment status
- `POST /api/v1/payments/verify` - Verify payment risk

### Frontend (Port 3000)

Next.js application for the storefront.

## Managing Services

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f core
docker-compose logs -f commerce
docker-compose logs -f payment
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart core
docker-compose restart commerce
docker-compose restart payment
docker-compose restart frontend
```

### Stop Services

```bash
# Stop without removing data
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Directory Structure

```
Aarya_Clothing/
├── docker-compose.yml
├── .env.example
│
├── frontend/                   # Next.js Frontend
│   ├── Dockerfile
│   └── src/
│
├── services/
│   ├── core/                   # Core Platform (Port 8001)
│   ├── commerce/               # Commerce Service (Port 8010)
│   └── payment/                # Payment Service (Port 8020)
│
└── docker/
    ├── postgres/init.sql
    └── redis/redis.conf
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs for errors
docker-compose logs

# Check Docker status
docker stats
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check Redis
docker-compose exec redis redis-cli ping
```

### Port Conflicts

```bash
# Check what's using a port
lsof -i :8001

# Change port in docker-compose.yml if needed
```

## Security Notes

1. **Change default passwords** before production deployment
2. **Use HTTPS** in production (configure reverse proxy)
3. **Keep secrets out of version control**
4. **Regularly update dependencies**

## Future Enhancements

For production, consider adding:
- Nginx reverse proxy with SSL
- Automated backups
- Monitoring (Prometheus/Grafana)
- Log aggregation
- Load balancing for scaling
