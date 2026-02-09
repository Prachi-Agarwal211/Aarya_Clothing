#!/bin/bash

# Aarya Clothing - VPS Deployment Script
# Domain: aaryaclothing.cloud
# VPS IP: 72.61.255.8

set -e

echo "=========================================="
echo "Aarya Clothing - VPS Deployment"
echo "=========================================="
echo "Domain: aaryaclothing.cloud"
echo "VPS IP: 72.61.255.8"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env file with production configuration."
    exit 1
fi

# Step 1: Generate SSL certificates
echo ""
echo "Step 1: Generating SSL certificates..."
chmod +x setup-ssl.sh
./setup-ssl.sh

# Step 2: Stop existing containers
echo ""
echo "Step 2: Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Step 3: Remove old images (optional - uncomment if needed)
# echo "Removing old Docker images..."
# docker system prune -f

# Step 4: Build and start services
echo ""
echo "Step 3: Building and starting services..."
docker-compose up -d --build

# Step 5: Wait for services to be healthy
echo ""
echo "Step 4: Waiting for services to be healthy..."
sleep 10

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

# Step 6: Verify services are running
echo ""
echo "Step 5: Verifying services..."
docker-compose ps

# Step 7: Display access information
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  Frontend:  https://aaryaclothing.cloud"
echo "  Core API:  https://aaryaclothing.cloud/api/auth/"
echo "  Products:  https://aaryaclothing.cloud/api/products/"
echo "  Cart:      https://aaryaclothing.cloud/api/cart/"
echo "  Orders:    https://aaryaclothing.cloud/api/orders/"
echo "  Payments:  https://aaryaclothing.cloud/api/payments/"
echo ""
echo "Service Status:"
docker-compose ps
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "View specific service logs:"
echo "  docker-compose logs -f frontend"
echo "  docker-compose logs -f core"
echo "  docker-compose logs -f commerce"
echo "  docker-compose logs -f payment"
echo "  docker-compose logs -f nginx"
echo ""
echo "Stop all services:"
echo "  docker-compose down"
echo ""
echo "Restart all services:"
echo "  docker-compose restart"
echo ""
echo "=========================================="
echo "Note: SSL certificates are self-signed."
echo "Your browser will show a security warning."
echo "This is normal for self-signed certificates."
echo "=========================================="
