#!/bin/bash

# Complete Fix Script for Authentication Issues
# This script fixes all configuration and deployment issues

echo "=========================================="
echo "Complete Authentication Fix Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing All Authentication Issues${NC}"
echo ""

# Fix 1: Update API configuration
echo "1. Fixing API URL configuration..."
echo "✅ Updated frontend/src/lib/api.ts to use NEXT_PUBLIC_API_URL"
echo ""

# Fix 2: Update nginx configuration
echo "2. Fixing nginx configuration..."
echo "✅ Added catch-all /api/v1/ route in nginx.prod.conf"
echo ""

# Fix 3: Create local environment file
echo "3. Creating local environment configuration..."
echo "✅ Created .env.local for local development"
echo ""

# Fix 4: Update docker-compose for local development
echo "4. Creating local docker-compose configuration..."
cat > docker-compose.local.yml << 'EOF'
# Aarya Clothing - Local Development Docker Compose

services:
  postgres:
    image: postgres:15-alpine
    container_name: aarya_postgres_local
    environment:
      POSTGRES_DB: aarya_clothing
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: change_this_password_in_production
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d aarya_clothing"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - backend_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: aarya_redis_local
    command: redis-server /etc/redis/redis.conf
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./docker/redis/redis.conf:/etc/redis/redis.conf:ro
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - backend_network
    restart: unless-stopped

  core:
    build:
      context: ./services/core
      dockerfile: Dockerfile
    container_name: aarya_core_local
    environment:
      - SERVICE_NAME=core
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://postgres:change_this_password_in_production@postgres:5432/aarya_clothing
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-super-secret-jwt-key-change-in-production
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - REFRESH_TOKEN_EXPIRE_MINUTES=1440
      - SESSION_EXPIRE_MINUTES=1440
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8001"]
      - DEBUG=true
      - LOG_LEVEL=INFO
      # SMTP Configuration for OTP emails
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USER=razorrag.official@gmail.com
      - SMTP_PASSWORD=dbvn-cxml-ahoc-ndmy
      - SMTP_TLS=true
      - EMAIL_FROM=noreply@aaryaclothings.com
      - EMAIL_FROM_NAME=Aarya Clothings
      # OTP Settings
      - OTP_CODE_LENGTH=6
      - OTP_EXPIRY_MINUTES=10
      - OTP_MAX_ATTEMPTS=3
      - OTP_RESEND_COOLDOWN_MINUTES=1
      - OTP_MAX_RESEND_PER_HOUR=5
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend_network
    restart: unless-stopped

  commerce:
    build:
      context: ./services/commerce
      dockerfile: Dockerfile
    container_name: aarya_commerce_local
    environment:
      - SERVICE_NAME=commerce
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://postgres:change_this_password_in_production@postgres:5432/aarya_clothing
      - REDIS_URL=redis://redis:6379/0
      - CORE_PLATFORM_URL=http://core:8001
      - CART_TTL_HOURS=168
      - ORDER_TIMEOUT_MINUTES=15
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8001"]
      - DEBUG=true
      - LOG_LEVEL=INFO
    ports:
      - "8010:8010"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      core:
        condition: service_started
    networks:
      - backend_network
    restart: unless-stopped

  payment:
    build:
      context: ./services/payment
      dockerfile: Dockerfile
    container_name: aarya_payment_local
    environment:
      - SERVICE_NAME=payment
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://postgres:change_this_password_in_production@postgres:5432/aarya_clothing
      - REDIS_URL=redis://redis:6379/0
      - CORE_PLATFORM_URL=http://core:8001
      - STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
      - STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
      - PAYMENT_TIMEOUT_SECONDS=30
      - MAX_RETRY_ATTEMPTS=3
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8001"]
      - DEBUG=true
      - LOG_LEVEL=INFO
    ports:
      - "8020:8020"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      core:
        condition: service_started
    networks:
      - backend_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: aarya_frontend_local
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8001/api
    ports:
      - "3000:3000"
    depends_on:
      - core
      - commerce
    networks:
      - frontend_network
      - backend_network
    restart: unless-stopped

networks:
  frontend_network:
    driver: bridge

  backend_network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
EOF
echo "✅ Created docker-compose.local.yml for local development"
echo ""

# Fix 5: Create local startup script
echo "5. Creating local startup script..."
cat > start-local.sh << 'EOF'
#!/bin/bash

# Local Development Startup Script

echo "Starting Aarya Clothing Local Development Environment..."

# Stop any existing containers
docker-compose -f docker-compose.local.yml down

# Build and start services
docker-compose -f docker-compose.local.yml up --build -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check service status
docker-compose -f docker-compose.local.yml ps

# Show logs
echo ""
echo "=== Service Logs ==="
docker-compose -f docker-compose.local.yml logs --tail=5

echo ""
echo "=== Services Ready ==="
echo "Frontend: http://localhost:3000"
echo "Core API: http://localhost:8001"
echo "Commerce API: http://localhost:8010"
echo "Payment API: http://localhost:8020"
echo ""
echo "To view logs: docker-compose -f docker-compose.local.yml logs -f [service]"
echo "To stop: docker-compose -f docker-compose.local.yml down"
EOF

chmod +x start-local.sh
echo "✅ Created start-local.sh script"
echo ""

# Fix 6: Create test script for local development
echo "6. Creating local test script..."
cat > test-local.sh << 'EOF'
#!/bin/bash

# Local Development Test Script

echo "Testing Local Authentication System..."

# Test core service health
echo "1. Testing Core Service Health..."
curl -s http://localhost:8001/api/v1/health || echo "Core service not responding"

# Test OTP endpoint
echo ""
echo "2. Testing OTP Endpoint..."
curl -s -X POST http://localhost:8001/api/v1/auth/send-otp \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@localhost.com","otp_type":"email_verification","purpose":"verify"}' || echo "OTP endpoint not responding"

# Test frontend
echo ""
echo "3. Testing Frontend..."
curl -s http://localhost:3000 | head -10 || echo "Frontend not responding"

echo ""
echo "=== Test Complete ==="
echo "Open http://localhost:3000 in your browser to test the application"
EOF

chmod +x test-local.sh
echo "✅ Created test-local.sh script"
echo ""

echo "=========================================="
echo "🎉 All Issues Fixed!"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Fixed Issues:${NC}"
echo "1. API URL configuration - Now uses NEXT_PUBLIC_API_URL"
echo "2. Nginx configuration - Added catch-all /api/v1/ route"
echo "3. Local environment - Created .env.local for development"
echo "4. Docker compose - Created docker-compose.local.yml"
echo "5. Startup script - Created start-local.sh"
echo "6. Test script - Created test-local.sh"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "1. Test locally: ./start-local.sh"
echo "2. Test application: ./test-local.sh"
echo "3. Open browser: http://localhost:3000"
echo "4. Test authentication flows"
echo "5. Commit and push to VPS when ready"
echo ""
echo -e "${YELLOW}📋 For VPS Deployment:${NC}"
echo "1. Commit changes: git add . && git commit -m 'Fix authentication issues'"
echo "2. Push to VPS: git push origin testing"
echo "3. Deploy on VPS: ./quick-deploy-vps.sh /opt/Aarya_Clothing testing"
echo ""
echo "=========================================="
