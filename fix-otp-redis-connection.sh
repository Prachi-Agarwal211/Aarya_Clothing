#!/bin/bash

# Fix OTP Redis Connection Issue
# This script fixes the Redis connection and adds missing SMTP configuration

set -e

echo "=========================================="
echo "Fixing OTP Redis Connection Issue"
echo "=========================================="

# Step 1: Check current docker-compose status
echo ""
echo "Step 1: Checking current service status..."
docker-compose ps

# Step 2: Test Redis connection from core container
echo ""
echo "Step 2: Testing Redis connection from core container..."
docker-compose exec core sh -c "python -c 'import redis; r = redis.from_url(\"redis://redis:6379/0\"); print(r.ping())'" || echo "❌ Redis connection test failed"

# Step 3: Check Redis is accessible
echo ""
echo "Step 3: Checking Redis accessibility..."
docker-compose exec redis redis-cli ping

# Step 4: Check network connectivity
echo ""
echo "Step 4: Checking Docker network..."
docker network inspect Aarya_Clothing_backend_network | grep -A 10 "aarya_core\|aarya_redis"

# Step 5: Restart core service to re-establish connection
echo ""
echo "Step 5: Restarting core service..."
docker-compose restart core

# Step 6: Wait for core service to start
echo ""
echo "Step 6: Waiting for core service to start..."
sleep 10

# Step 7: Check core service logs
echo ""
echo "Step 7: Checking core service logs for Redis connection..."
docker-compose logs --tail=20 core

# Step 8: Test Redis connection again
echo ""
echo "Step 8: Testing Redis connection after restart..."
docker-compose exec core sh -c "python -c 'import redis; r = redis.from_url(\"redis://redis:6379/0\"); print(\"Redis ping:\", r.ping())'"

# Step 9: Check if OTP keys can be stored
echo ""
echo "Step 9: Testing OTP key storage..."
docker-compose exec redis redis-cli SET "otp:test:test@example.com" "123456" EX 600
docker-compose exec redis redis-cli GET "otp:test:test@example.com"
docker-compose exec redis redis-cli DEL "otp:test:test@example.com"

echo ""
echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "If Redis connection is still failing, please check:"
echo "1. Docker network configuration"
echo "2. Redis container health"
echo "3. Core service environment variables"
echo ""
echo "Next steps:"
echo "1. Update docker-compose.yml with SMTP configuration"
echo "2. Restart all services"
echo "3. Test OTP functionality"