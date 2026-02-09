# Aarya Clothing - VPS Deployment Guide

## Quick VPS Setup

### 1. Server Requirements
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 20GB+ free space
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Software**: Docker & Docker Compose

### 2. One-Command Deployment

```bash
# Clone and setup
git clone <your-repo> Aarya_Clothing
cd Aarya_Clothing

# Configure environment
cp .env.example .env
nano .env  # Edit your settings

# Deploy everything
chmod +x deploy-production.sh
./deploy-production.sh
```

### 3. Essential Environment Variables

```bash
# Required - Change these!
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your-super-secret-jwt-key

# Optional - Payment gateways
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
STRIPE_SECRET_KEY=your_stripe_secret

# Your domain
NEXT_PUBLIC_API_URL=http://your-domain.com:8001
```

### 4. Access Points

- **Frontend**: http://your-domain.com:3000
- **Core API**: http://your-domain.com:8001
- **Commerce API**: http://your-domain.com:8010
- **Payment API**: http://your-domain.com:8020

### 5. Management Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all
docker-compose down
```

## Services Overview

- **Core Service** (Port 8001): Authentication & Users
- **Commerce Service** (Port 8010): Products, Cart & Orders
- **Payment Service** (Port 8020): Payment Processing
- **Frontend** (Port 3000): Next.js Storefront
- **PostgreSQL** (Port 5432): Database
- **Redis** (Port 6379): Cache & Sessions

## Security Notes

1. **Change default passwords** before production
2. **Use firewall** to restrict access to database ports
3. **Set up SSL** with reverse proxy for production
4. **Regularly update** Docker images

## Troubleshooting

```bash
# Check service health
curl http://localhost:8001/health  # Core
curl http://localhost:8010/health  # Commerce
curl http://localhost:8020/health  # Payment

# Database issues
docker-compose exec postgres pg_isready -U postgres

# Redis issues
docker-compose exec redis redis-cli ping
```

---

**Clean Project Structure**: All development files removed, production-ready only.
