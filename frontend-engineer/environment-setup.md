# Environment Setup Guide

This guide helps you set up your development environment to work with the Aarya Clothing backend.

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16 or higher)
- **Docker** & **Docker Compose**
- **Git**

### 1. Clone and Setup Backend

```bash
# Clone the repository
git clone <repository-url>
cd Aarya_Clothing

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

### 2. Start Backend Services

```bash
# Start all services
docker-compose up -d postgres redis core commerce payment

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Verify Services

```bash
# Test Core Service
curl http://localhost:8001/health

# Test Commerce Service
curl http://localhost:8010/health

# Test Payment Service
curl http://localhost:8020/health
```

---

## ⚙️ Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:your_secure_password_here@localhost:5432/aarya_clothing

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here_minimum_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=1440
SESSION_EXPIRE_MINUTES=1440

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBER=true
PASSWORD_REQUIRE_SPECIAL=false

# Rate Limiting
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=300
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# Cookie Settings
COOKIE_SECURE=false
COOKIE_HTTPONLY=true
COOKIE_SAMESITE=lax
```

### Email Configuration (for OTP)

```env
# Gmail SMTP (Recommended for development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
SMTP_TLS=true
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Aarya Clothing

# OTP Settings
OTP_CODE_LENGTH=6
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_MINUTES=1
OTP_MAX_RESEND_PER_HOUR=5
```

### WhatsApp Business API (Optional)

```env
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_API_VERSION=v18.0
```

### Payment Configuration

```env
# Razorpay (Primary for India)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Payment URLs
PAYMENT_SUCCESS_URL=http://localhost:3000/payment/success
PAYMENT_FAILURE_URL=http://localhost:3000/payment/failure

# Payment Settings
PAYMENT_TIMEOUT_SECONDS=30
MAX_RETRY_ATTEMPTS=3
```

### Cloud Storage (for product images)

```env
# Cloudflare R2
R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=aarya-clothing-images
R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev
R2_REGION=auto
```

---

## 🌐 Frontend Configuration

### Environment Variables for Frontend

Create a `.env.local` file in your frontend project:

```env
# API Base URLs
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
NEXT_PUBLIC_COMMERCE_API_URL=http://localhost:8010
NEXT_PUBLIC_PAYMENT_API_URL=http://localhost:8020

# Application Settings
NEXT_PUBLIC_APP_NAME=Aarya Clothing
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_WHATSAPP_OTP=false
NEXT_PUBLIC_ENABLE_RAZORPAY=true

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=your_google_analytics_id
NEXT_PUBLIC_HOTJAR_ID=your_hotjar_id
```

### Production Environment Variables

```env
# Production URLs
NEXT_PUBLIC_API_BASE_URL=https://aaryaclothing.cloud/api
NEXT_PUBLIC_COMMERCE_API_URL=https://aaryaclothing.cloud/api/commerce
NEXT_PUBLIC_PAYMENT_API_URL=https://aaryaclothing.cloud/api/payment

# Production Settings
NEXT_PUBLIC_APP_URL=https://aaryaclothing.cloud
NEXT_PUBLIC_ENABLE_WHATSAPP_OTP=true
```

---

## 🛠️ Development Setup

### Option 1: Docker (Recommended)

```bash
# Start all services with Docker
docker-compose up -d

# View logs
docker-compose logs -f core
docker-compose logs -f commerce
docker-compose logs -f payment

# Stop services
docker-compose down
```

### Option 2: Local Development

If you prefer running services locally:

```bash
# Install Python dependencies
cd services/core
pip install -r requirements.txt

cd ../commerce
pip install -r requirements.txt

cd ../payment
pip install -r requirements.txt

# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis

# Run services locally
cd services/core && python main.py
cd services/commerce && python main.py
cd services/payment && python main.py
```

---

## 🧪 Testing Environment

### Test Database Setup

```bash
# Create test database
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE aarya_clothing_test;"

# Run tests
cd tests
pytest test_all_services.py -v
```

### API Testing with Postman

Import the Postman collection (if available) or use these examples:

```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8010/health
curl http://localhost:8020/health

# Registration
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

# Get user info
curl -X GET http://localhost:8001/api/v1/users/me \
  -b cookies.txt
```

---

## 🔧 Common Issues & Solutions

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
netstat -tulpn | grep :8001
netstat -tulpn | grep :8010
netstat -tulpn | grep :8020

# Kill processes if needed
sudo kill -9 <PID>

# Or change ports in docker-compose.yml
```

### Database Connection Issues

```bash
# Check PostgreSQL container
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Connect to database directly
docker-compose exec postgres psql -U postgres -d aarya_clothing
```

### Redis Connection Issues

```bash
# Check Redis container
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Email/OTP Not Working

1. **Check SMTP credentials** in `.env`
2. **Use App Password** for Gmail (not regular password)
3. **Enable less secure apps** in Gmail settings
4. **Check firewall/antivirus** blocking SMTP

### Payment Gateway Issues

1. **Verify Razorpay credentials**
2. **Check webhook URL** is accessible
3. **Ensure CORS** allows your frontend domain
4. **Test with Razorpay test mode** first

---

## 📊 Monitoring & Debugging

### Service Health Monitoring

```bash
# Create health check script
cat > health-check.sh << 'EOF'
#!/bin/bash
echo "=== Service Health Check ==="
echo "Core Service: $(curl -s http://localhost:8001/health | jq -r '.status')"
echo "Commerce Service: $(curl -s http://localhost:8010/health | jq -r '.status')"
echo "Payment Service: $(curl -s http://localhost:8020/health | jq -r '.status')"
echo "PostgreSQL: $(docker-compose exec -T postgres pg_isready -U postgres)"
echo "Redis: $(docker-compose exec -T redis redis-cli ping)"
EOF

chmod +x health-check.sh
./health-check.sh
```

### Log Monitoring

```bash
# Follow all service logs
docker-compose logs -f

# Follow specific service logs
docker-compose logs -f core
docker-compose logs -f commerce
docker-compose logs -f payment

# View last 100 lines
docker-compose logs --tail=100
```

### Database Monitoring

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d aarya_clothing

# Useful queries
\dt                    # List tables
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM orders;
```

---

## 🚀 Production Deployment

### Environment Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Set `COOKIE_SECURE=true`
- [ ] Configure proper SSL certificates
- [ ] Set up production database
- [ ] Configure production email service
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CDN for static assets
- [ ] Configure rate limiting
- [ ] Set up error reporting

### Production Docker Compose

Use the provided production configuration:

```bash
# Deploy with production config
docker-compose -f docker-compose.yml --env-file .env.production up -d
```

---

## 📚 Additional Resources

### Documentation Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Razorpay API Docs](https://razorpay.com/docs/api/)

### Useful Commands

```bash
# Rebuild services after code changes
docker-compose build core commerce payment

# Run database migrations
docker-compose exec core python -m alembic upgrade head

# Backup database
docker-compose exec postgres pg_dump -U postgres aarya_clothing > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres aarya_clothing < backup.sql

# Clean up unused Docker resources
docker system prune -a
```

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs** for error messages
2. **Verify environment variables** are set correctly
3. **Ensure all services are running**
4. **Check network connectivity** between services
5. **Review this documentation** for common solutions

For additional support, refer to the project's issue tracker or contact the development team.
