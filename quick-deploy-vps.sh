#!/bin/bash

# Quick VPS Deployment Script
# Automated deployment for Aarya Clothing authentication fixes

set -e  # Exit on any error

echo "=========================================="
echo "Quick VPS Deployment - Authentication Fixes"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="${1:-/root/Aarya_Clothing}"
BRANCH="${2:-testing}"

echo -e "${BLUE}🔧 Configuration:${NC}"
echo "Project Directory: $PROJECT_DIR"
echo "Branch: $BRANCH"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker status
check_docker() {
    if ! command_exists docker; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker is properly installed and running${NC}"
}

# Function to check project directory
check_project() {
    if [[ ! -d "$PROJECT_DIR" ]]; then
        echo -e "${RED}❌ Project directory does not exist: $PROJECT_DIR${NC}"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    if [[ ! -f "docker-compose.yml" ]]; then
        echo -e "${RED}❌ docker-compose.yml not found in project directory${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Project directory verified${NC}"
}

# Function to pull latest changes
pull_changes() {
    echo -e "${BLUE}🔄 Pulling latest changes...${NC}"
    
    # Check if we're in a git repository
    if [[ ! -d ".git" ]]; then
        echo -e "${RED}❌ Not a git repository${NC}"
        exit 1
    fi
    
    # Checkout the specified branch
    git checkout "$BRANCH"
    
    # Pull latest changes
    git pull origin "$BRANCH"
    
    echo -e "${GREEN}✅ Latest changes pulled${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping current services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Function to build and start services
start_services() {
    echo -e "${BLUE}🏗️ Building and starting services...${NC}"
    
    # Build and start all services
    docker-compose up --build -d
    
    echo -e "${GREEN}✅ Services started${NC}"
}

# Function to wait for services to be healthy
wait_for_services() {
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        local healthy_count=$(docker-compose ps --services --filter "status=healthy" | wc -l)
        local total_services=$(docker-compose ps --services | wc -l)
        
        if [[ $healthy_count -eq $total_services ]]; then
            echo -e "${GREEN}✅ All services are healthy${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $((attempt + 1))/$max_attempts: $healthy_count/$total_services services healthy${NC}"
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}❌ Services did not become healthy in time${NC}"
    docker-compose ps
    return 1
}

# Function to test authentication
test_auth() {
    echo -e "${BLUE}🧪 Testing authentication endpoints...${NC}"
    
    # Test health endpoint
    local health_response=$(curl -s -w "%{http_code}" http://localhost:8001/api/v1/health)
    local http_code="${health_response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ Core service health check passed${NC}"
    else
        echo -e "${RED}❌ Core service health check failed (HTTP $http_code)${NC}"
        return 1
    fi
    
    # Test through nginx if domain is configured
    if [[ -n "$(dig +short aaryaclothing.cloud 2>/dev/null)" ]]; then
        local external_response=$(curl -s -w "%{http_code}" https://aaryaclothing.cloud/api/v1/health)
        local external_code="${external_response: -3}"
        
        if [[ "$external_code" == "200" ]]; then
            echo -e "${GREEN}✅ External health check passed${NC}"
        else
            echo -e "${YELLOW}⚠️ External health check failed (HTTP $external_code)${NC}"
        fi
    fi
    
    return 0
}

# Function to show service status
show_status() {
    echo -e "${BLUE}📊 Service Status:${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${BLUE}📊 Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Recent Logs:${NC}"
    echo ""
    echo -e "${YELLOW}Core Service:${NC}"
    docker-compose logs --tail=10 core
    echo ""
    echo -e "${YELLOW}Frontend Service:${NC}"
    docker-compose logs --tail=10 frontend
    echo ""
    echo -e "${YELLOW}PostgreSQL:${NC}"
    docker-compose logs --tail=5 postgres
    echo ""
    echo -e "${YELLOW}Redis:${NC}"
    docker-compose logs --tail=5 redis
}

# Main deployment function
deploy() {
    echo -e "${BLUE}🚀 Starting deployment...${NC}"
    echo ""
    
    # Check prerequisites
    check_docker
    check_project
    
    # Pull latest changes
    pull_changes
    
    # Stop current services
    stop_services
    
    # Start services
    start_services
    
    # Wait for services to be healthy
    wait_for_services
    
    # Test authentication
    test_auth
    
    # Show status
    show_status
    
    # Show logs
    show_logs
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}🌐 Your website should be available at:${NC}"
    echo "https://aaryaclothing.cloud"
    echo ""
    echo -e "${BLUE}🧪 Test the following:${NC}"
    echo "1. Registration: https://aaryaclothing.cloud/login"
    echo "2. Login with email"
    echo "3. Login with username"
    echo "4. OTP verification"
    echo "5. Password reset"
    echo ""
    echo -e "${BLUE}📋 Useful Commands:${NC}"
    echo "- View logs: docker-compose logs -f [service]"
    echo "- Restart service: docker-compose restart [service]"
    echo "- Check status: docker-compose ps"
    echo "- Access container: docker-compose exec [service] sh"
    echo ""
}

# Run deployment
deploy "$@"
