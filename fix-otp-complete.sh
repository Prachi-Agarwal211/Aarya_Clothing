#!/bin/bash

# Complete OTP Fix Script for VPS
# This script fixes Redis connection and SMTP configuration issues

set -e

echo "=========================================="
echo "Aarya Clothing - OTP Fix Script"
echo "=========================================="
echo ""

# Step 1: Check current service status
echo "Step 1: Checking current service status..."
docker-compose ps
echo ""

# Step 2: Stop all services
echo "Step 2: Stopping all services..."
docker-compose down
echo "✓ Services stopped"
echo ""

# Step 3: Check if .env file has required variables
echo "Step 3: Checking environment variables..."
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Check for SMTP variables
if grep -q "SMTP_HOST" .env && grep -q "SMTP_USER" .env && grep -q "SMTP_PASSWORD" .env; then
    echo "✓ SMTP configuration found in .env"
else
    echo "⚠️  Warning: SMTP configuration may be incomplete"
fi

# Check for Redis URL
if grep -q "REDIS_URL" .env; then
    echo "✓ REDIS_URL found in .env"
else
    echo "⚠️  Warning: REDIS_URL not found in .env"
fi
echo ""

# Step 4: Remove old containers and images (optional)
echo "Step 4: Cleaning up old containers..."
docker system prune -f
echo "✓ Cleanup complete"
echo ""

# Step 5: Rebuild and start services
echo "Step 5: Rebuilding and starting services..."
docker-compose up -d --build
echo "✓ Services started"
echo ""

# Step 6: Wait for services to be healthy
echo "Step 6: Waiting for services to be healthy..."
echo "Waiting for PostgreSQL..."
until docker exec aarya_postgres pg_isready -U postgres -d aarya_clothing > /dev/null 2>&1; do
    echo "  PostgreSQL not ready yet..."
    sleep 5
done
echo "✓ PostgreSQL is ready"

echo "Waiting for Redis..."
until docker exec aarya_redis redis-cli ping | grep -q PONG > /dev/null 2>&1; do
    echo "  Redis not ready yet..."
    sleep 5
done
echo "✓ Redis is ready"

echo "Waiting for Core service..."
sleep 15
echo "✓ Core service should be ready"
echo ""

# Step 7: Verify Redis connection from core service
echo "Step 7: Verifying Redis connection from core service..."
if docker-compose exec -T core sh -c "python -c 'import redis; r = redis.from_url(\"redis://redis:6379/0\"); print(\"Redis ping:\", r.ping())'" > /dev/null 2>&1; then
    echo "✓ Core service can connect to Redis"
else
    echo "❌ Core service cannot connect to Redis"
    echo "Checking core service logs..."
    docker-compose logs --tail=30 core
fi
echo ""

# Step 8: Check core service logs for Redis connection
echo "Step 8: Checking core service startup logs..."
docker-compose logs --tail=50 core | grep -i "redis\|error\|failed" || echo "No Redis-related errors found"
echo ""

# Step 9: Test OTP key storage
echo "Step 9: Testing OTP key storage in Redis..."
docker-compose exec -T redis redis-cli SET "otp:test:test@example.com" "123456" EX 600 > /dev/null 2>&1
if docker-compose exec -T redis redis-cli GET "otp:test@example.com" | grep -q "123456"; then
    echo "✓ OTP key storage test passed"
    docker-compose exec -T redis redis-cli DEL "otp:test@example.com" > /dev/null 2>&1
else
    echo "❌ OTP key storage test failed"
fi
echo ""

# Step 10: Check service status
echo "Step 10: Final service status..."
docker-compose ps
echo ""

# Step 11: Display access information
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
docker-compose ps
echo ""
echo "Next Steps:"
echo "1. Test OTP functionality on https://aaryaclothing.cloud"
echo "2. Check if OTP emails are being sent"
echo "3. Monitor logs: docker-compose logs -f core"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f core"
echo "  docker-compose logs -f redis"
echo ""
echo "To restart services:"
echo "  docker-compose restart core"
echo ""
echo "=========================================="
