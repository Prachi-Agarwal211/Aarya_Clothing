#!/bin/bash

# Aarya Clothing - VPS Health Check Script
# Verifies all services are running correctly

set -e

echo "=========================================="
echo "Aarya Clothing - Health Check"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local service_name=$1
    local container_name=$2
    local health_check=$3
    
    echo -n "Checking $service_name... "
    
    if docker ps | grep -q "$container_name"; then
        if [ -n "$health_check" ]; then
            if eval "$health_check" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Healthy${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ Running but health check failed${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✓ Running${NC}"
            return 0
        fi
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Check all services
echo "=== Service Status ==="
check_service "PostgreSQL" "aarya_postgres" "docker exec aarya_postgres pg_isready -U postgres -d aarya_clothing"
check_service "Redis" "aarya_redis" "docker exec aarya_redis redis-cli ping"
check_service "Core API" "aarya_core" ""
check_service "Commerce API" "aarya_commerce" ""
check_service "Payment API" "aarya_payment" ""
check_service "Frontend" "aarya_frontend" ""
check_service "Nginx" "aarya_nginx" ""

echo ""
echo "=== Port Availability ==="

# Check if ports are listening
check_port() {
    local port=$1
    local service=$2
    
    echo -n "Port $port ($service)... "
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓ Listening${NC}"
    else
        echo -e "${RED}✗ Not listening${NC}"
    fi
}

check_port "80" "HTTP"
check_port "443" "HTTPS"
check_port "5432" "PostgreSQL"
check_port "6379" "Redis"

echo ""
echo "=== SSL Certificate Check ==="

if [ -f "docker/nginx/ssl/aaryaclothing.cloud.crt" ] && [ -f "docker/nginx/ssl/aaryaclothing.cloud.key" ]; then
    echo -e "${GREEN}✓ SSL certificates exist${NC}"
    
    # Check certificate validity
    cert_expiry=$(openssl x509 -in docker/nginx/ssl/aaryaclothing.cloud.crt -noout -enddate 2>/dev/null | cut -d= -f2)
    if [ -n "$cert_expiry" ]; then
        echo "  Expires: $cert_expiry"
    fi
else
    echo -e "${RED}✗ SSL certificates missing${NC}"
fi

echo ""
echo "=== Docker Compose Status ==="
docker-compose ps

echo ""
echo "=== Recent Logs (Last 20 lines) ==="
echo "--- Nginx ---"
docker logs --tail=20 aarya_nginx 2>&1 | tail -5

echo ""
echo "--- Frontend ---"
docker logs --tail=20 aarya_frontend 2>&1 | tail -5

echo ""
echo "--- Core API ---"
docker logs --tail=20 aarya_core 2>&1 | tail -5

echo ""
echo "--- Commerce API ---"
docker logs --tail=20 aarya_commerce 2>&1 | tail -5

echo ""
echo "--- Payment API ---"
docker logs --tail=20 aarya_payment 2>&1 | tail -5

echo ""
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "=== Disk Usage ==="
df -h | grep -E "Filesystem|/$"

echo ""
echo "=== Docker System Info ==="
docker system df

echo ""
echo "=========================================="
echo "Health Check Complete!"
echo "=========================================="
echo ""
echo "If all services show green, your deployment is successful!"
echo ""
echo "Access URLs:"
echo "  Frontend:  https://aaryaclothing.cloud"
echo "  Health:    https://aaryaclothing.cloud/health"
echo ""
echo "For detailed logs:"
echo "  docker-compose logs -f"
echo ""
