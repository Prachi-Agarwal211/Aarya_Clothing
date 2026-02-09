#!/bin/bash

# Aarya Clothing - Production Deployment Script
# This script deploys the complete e-commerce platform to production

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

# Check if production environment file exists
check_env_file() {
    if [ ! -f ".env.prod" ]; then
        print_error "Production environment file .env.prod not found!"
        print_warning "Please copy .env.prod.example to .env.prod and update the values."
        exit 1
    fi
    print_status "Production environment file found ✓"
}

# Check if SSL certificates exist
check_ssl_certificates() {
    if [ ! -f "docker/nginx/ssl/aaryaclothing.cloud.crt" ] || [ ! -f "docker/nginx/ssl/aaryaclothing.cloud.key" ]; then
        print_warning "SSL certificates not found!"
        print_warning "Please place your SSL certificates in docker/nginx/ssl/"
        print_warning "For testing, you can generate self-signed certificates:"
        print_warning "  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\"
        print_warning "    -keyout docker/nginx/ssl/aaryaclothing.cloud.key \\"
        print_warning "    -out docker/nginx/ssl/aaryaclothing.cloud.crt \\"
        print_warning "    -subj \"/C=US/ST=State/L=City/O=Organization/CN=aaryaclothing.cloud\""
        read -p "Continue without SSL certificates? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "SSL certificates found ✓"
    fi
}

# Stop existing containers
stop_existing() {
    print_status "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans || true
    print_status "Existing containers stopped ✓"
}

# Build and start services
start_services() {
    print_header "Deploying Aarya Clothing E-Commerce Platform"
    
    print_status "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    print_status "Starting all services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    print_status "Waiting for services to be healthy..."
    sleep 15
}

# Check service health
check_health() {
    print_status "Checking service health..."
    
    # Check PostgreSQL
    if docker exec aarya_postgres_prod pg_isready -U postgres > /dev/null 2>&1; then
        print_status "PostgreSQL is healthy ✓"
    else
        print_error "PostgreSQL is not healthy"
    fi
    
    # Check Redis
    if docker exec aarya_redis_prod redis-cli ping > /dev/null 2>&1; then
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
    
    # Check Nginx
    if curl -s http://localhost/health > /dev/null 2>&1; then
        print_status "Nginx is healthy ✓"
    else
        print_warning "Nginx might still be starting..."
    fi
}

# Show access URLs
show_urls() {
    print_header "Production Deployment Complete"
    echo -e "${GREEN}Main Site:${NC}     https://aaryaclothing.cloud"
    echo -e "${GREEN}Health Check:${NC}  https://aaryaclothing.cloud/health"
    echo ""
    echo -e "${BLUE}Internal Services (for debugging):${NC}"
    echo -e "${GREEN}Core API:${NC}      http://localhost:8001/health"
    echo -e "${GREEN}Commerce API:${NC}  http://localhost:8010/health"
    echo -e "${GREEN}Payment API:${NC}   http://localhost:8020/health"
    echo ""
    echo -e "${YELLOW}Note: Make sure your domain DNS points to this server!${NC}"
}

# Show logs
show_logs() {
    print_status "Showing logs (press Ctrl+C to exit)..."
    docker-compose -f docker-compose.prod.yml logs -f
}

# Main execution
main() {
    print_header "Aarya Clothing Production Deployment"
    
    check_docker
    check_docker_compose
    check_env_file
    check_ssl_certificates
    stop_existing
    start_services
    check_health
    show_urls
    
    echo ""
    print_status "Production deployment completed successfully!"
    print_status "Use './deploy-production.sh logs' to view logs"
    print_status "Use './deploy-production.sh stop' to stop all services"
    
    # Check for command line arguments
    if [ "$1" = "logs" ]; then
        show_logs
    elif [ "$1" = "stop" ]; then
        print_status "Stopping all services..."
        docker-compose -f docker-compose.prod.yml down
        print_status "All services stopped ✓"
    fi
}

# Run main function
main "$@"
