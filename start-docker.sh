#!/bin/bash

# Aarya Clothing - Docker Development Environment Starter
# This script starts the complete e-commerce platform with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_status "Docker is running ✓"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install docker-compose first."
        exit 1
    fi
    print_status "docker-compose is available ✓"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p docker/postgres
    mkdir -p docker/redis
    mkdir -p docker/nginx
    mkdir -p logs
    print_status "Directories created ✓"
}

# Create init.sql if it doesn't exist
create_init_sql() {
    if [ ! -f "docker/postgres/init.sql" ]; then
        print_status "Creating PostgreSQL initialization script..."
        cat > docker/postgres/init.sql << 'EOF'
-- Aarya Clothing Database Initialization
-- This script creates the initial database schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by the services automatically
EOF
        print_status "PostgreSQL init script created ✓"
    fi
}

# Create redis.conf if it doesn't exist
create_redis_conf() {
    if [ ! -f "docker/redis/redis.conf" ]; then
        print_status "Creating Redis configuration..."
        cat > docker/redis/redis.conf << 'EOF'
# Redis Configuration for Aarya Clothing
bind 0.0.0.0
port 6379
timeout 0
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /data
appendonly yes
appendfsync everysec
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF
        print_status "Redis configuration created ✓"
    fi
}

# Create nginx config for development
create_nginx_conf() {
    if [ ! -f "docker/nginx/nginx.dev.conf" ]; then
        print_status "Creating Nginx configuration..."
        mkdir -p docker/nginx
        cat > docker/nginx/nginx.dev.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream core_api {
        server core:8001;
    }

    upstream commerce_api {
        server commerce:8010;
    }

    upstream payment_api {
        server payment:8020;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Core API
        location /api/auth/ {
            proxy_pass http://core_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Commerce API
        location /api/products/ {
            proxy_pass http://commerce_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/cart/ {
            proxy_pass http://commerce_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/orders/ {
            proxy_pass http://commerce_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Payment API
        location /api/payments/ {
            proxy_pass http://payment_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
        print_status "Nginx configuration created ✓"
    fi
}

# Stop existing containers
stop_existing() {
    print_status "Stopping existing containers..."
    docker-compose -f docker-compose.dev.yml down --remove-orphans || true
    print_status "Existing containers stopped ✓"
}

# Build and start services
start_services() {
    print_header "Starting Aarya Clothing E-Commerce Platform"
    
    print_status "Building Docker images..."
    docker-compose -f docker-compose.dev.yml build --no-cache
    
    print_status "Starting all services..."
    docker-compose -f docker-compose.dev.yml up -d
    
    print_status "Waiting for services to be healthy..."
    sleep 10
}

# Check service health
check_health() {
    print_status "Checking service health..."
    
    # Check PostgreSQL
    if docker exec aarya_postgres_dev pg_isready -U postgres > /dev/null 2>&1; then
        print_status "PostgreSQL is healthy ✓"
    else
        print_error "PostgreSQL is not healthy"
    fi
    
    # Check Redis
    if docker exec aarya_redis_dev redis-cli ping > /dev/null 2>&1; then
        print_status "Redis is healthy ✓"
    else
        print_error "Redis is not healthy"
    fi
    
    # Check Core Service
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        print_status "Core Service is healthy ✓"
    else
        print_warning "Core Service might still be starting..."
    fi
    
    # Check Commerce Service
    if curl -s http://localhost:8010/health > /dev/null 2>&1; then
        print_status "Commerce Service is healthy ✓"
    else
        print_warning "Commerce Service might still be starting..."
    fi
    
    # Check Payment Service
    if curl -s http://localhost:8020/health > /dev/null 2>&1; then
        print_status "Payment Service is healthy ✓"
    else
        print_warning "Payment Service might still be starting..."
    fi
    
    # Check Frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_status "Frontend is healthy ✓"
    else
        print_warning "Frontend might still be starting..."
    fi
}

# Show access URLs
show_urls() {
    print_header "Access URLs"
    echo -e "${GREEN}Frontend:${NC}     http://localhost:3000"
    echo -e "${GREEN}Core API:${NC}      http://localhost:8001"
    echo -e "${GREEN}Commerce API:${NC}  http://localhost:8010"
    echo -e "${GREEN}Payment API:${NC}   http://localhost:8020"
    echo -e "${GREEN}PostgreSQL:${NC}    localhost:5432"
    echo -e "${GREEN}Redis:${NC}         localhost:6379"
    echo ""
    echo -e "${BLUE}API Documentation:${NC}"
    echo -e "${GREEN}Core:${NC}         http://localhost:8001/docs"
    echo -e "${GREEN}Commerce:${NC}     http://localhost:8010/docs"
    echo -e "${GREEN}Payment:${NC}      http://localhost:8020/docs"
}

# Show logs
show_logs() {
    print_status "Showing logs (press Ctrl+C to exit)..."
    docker-compose -f docker-compose.dev.yml logs -f
}

# Main execution
main() {
    print_header "Aarya Clothing Docker Setup"
    
    check_docker
    check_docker_compose
    create_directories
    create_init_sql
    create_redis_conf
    create_nginx_conf
    stop_existing
    start_services
    check_health
    show_urls
    
    echo ""
    print_status "All services started successfully!"
    print_status "Use './start-docker.sh logs' to view logs"
    print_status "Use './start-docker.sh stop' to stop all services"
    
    # Check for command line arguments
    if [ "$1" = "logs" ]; then
        show_logs
    elif [ "$1" = "stop" ]; then
        print_status "Stopping all services..."
        docker-compose -f docker-compose.dev.yml down
        print_status "All services stopped ✓"
    fi
}

# Run main function
main "$@"
