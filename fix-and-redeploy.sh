#!/bin/bash

# Aarya Clothing - Fix Issues and Redeploy
# This script fixes the .env file and redeploys the application

set -e

echo "=========================================="
echo "Aarya Clothing - Fix and Redeploy"
echo "=========================================="
echo ""

# Step 1: Fix .env file
echo "Step 1: Fixing .env file special characters..."

# Backup original .env
if [ ! -f .env.backup ]; then
    cp .env .env.backup
    echo "✓ Backup created: .env.backup"
else
    echo "✓ Backup already exists: .env.backup"
fi

# Fix JWT_SECRET_KEY - wrap in quotes to prevent shell variable expansion
sed -i 's/^JWT_SECRET_KEY=Kj9#mP2\$vL8@wQ5!nR3&tY6\*zX1%bN4^cD7$/JWT_SECRET_KEY="Kj9#mP2\$vL8@wQ5!nR3&tY6*zX1%bN4^cD7"/g' .env

# Fix SECRET_KEY - wrap in quotes to prevent shell variable expansion
sed -i 's/^SECRET_KEY=Hf4@qW8!rE2&tY6#uI9\$oP3^vB5\*mZ1$/SECRET_KEY="Hf4@qW8!rE2&tY6#uI9\$oP3^vB5*mZ1"/g' .env

echo "✓ .env file fixed"
echo ""

# Step 2: Stop existing containers
echo "Step 2: Stopping existing containers..."
docker-compose down
echo "✓ Containers stopped"
echo ""

# Step 3: Remove failed images
echo "Step 3: Cleaning up failed images..."
docker system prune -f
echo "✓ Cleanup complete"
echo ""

# Step 4: Rebuild and start services
echo "Step 4: Rebuilding and starting services..."
docker-compose up -d --build
echo "✓ Services building and starting"
echo ""

# Step 5: Wait for services
echo "Step 5: Waiting for services to be healthy..."
sleep 15

# Check PostgreSQL
echo "Checking PostgreSQL..."
until docker exec aarya_postgres pg_isready -U postgres -d aarya_clothing; do
    echo "PostgreSQL is not ready yet..."
    sleep 5
done
echo "✓ PostgreSQL is ready"

# Check Redis
echo "Checking Redis..."
until docker exec aarya_redis redis-cli ping | grep -q PONG; do
    echo "Redis is not ready yet..."
    sleep 5
done
echo "✓ Redis is ready"

# Wait for backend services
echo "Waiting for backend services..."
sleep 15

# Step 6: Verify services
echo ""
echo "Step 6: Verifying services..."
docker-compose ps

echo ""
echo "=========================================="
echo "Fix and Redeploy Complete!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  Frontend:  https://aaryaclothing.cloud"
echo "  Health:    https://aaryaclothing.cloud/health"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "If you still see errors, check the logs:"
echo "  docker-compose logs frontend"
echo "  docker-compose logs core"
echo "  docker-compose logs commerce"
echo "  docker-compose logs payment"
echo ""
echo "=========================================="
