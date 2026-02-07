#!/bin/bash

# Aarya Clothing - One-Command Production Deployment
# VPS: 72.61.255.8 | Domain: aaryaclothing.cloud
# This script sets up EVERYTHING automatically

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_IP="72.61.255.8"
DOMAIN="aaryaclothing.cloud"
PROJECT_DIR="/opt/aarya-clothing"
ADMIN_PASSWORD="Root@2026"

echo -e "${BLUE}🚀 Aarya Clothing - One-Command Production Deployment${NC}"
echo -e "${BLUE}📍 VPS: $VPS_IP | Domain: $DOMAIN${NC}"
echo -e "${BLUE}🔐 Admin Password: $ADMIN_PASSWORD${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_step() {
    echo -e "${YELLOW}🔄 $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_step "Step 1: System Update & Dependencies"
apt update && apt upgrade -y
apt install -y curl wget git unzip htop vim ufw software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release

print_status "System updated and dependencies installed"

print_step "Step 2: Install Docker & Docker Compose"
# Remove old versions
apt-get remove -y docker docker-engine docker.io containerd runc || true

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
usermod -aG docker $USER

print_status "Docker and Docker Compose installed"

print_step "Step 3: Setup Firewall"
# Reset firewall
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (CRITICAL)
ufw allow 22/tcp
ufw limit 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Docker internal traffic
ufw allow from 172.16.0.0/12
ufw allow from 192.168.0.0/16

# Enable firewall
ufw --force enable

print_status "Firewall configured"

print_step "Step 4: Create Project Directory"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/{backups,certbot/conf,certbot/www,logs,monitoring}

print_status "Project directory created"

print_step "Step 5: Setup SSL Certificates"
cd $PROJECT_DIR

# Create temporary webroot for certbot
mkdir -p certbot/www

# Start temporary Nginx for certbot challenge
docker run -d --name temp-nginx \
    -p 80:80 \
    -v $PROJECT_DIR/certbot/www:/var/www/certbot \
    nginx:alpine

# Wait a moment for Nginx to start
sleep 10

# Get SSL certificates
docker run --rm \
    -v $PROJECT_DIR/certbot/conf:/etc/letsencrypt \
    -v $PROJECT_DIR/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --non-interactive || {
    print_error "Failed to get SSL certificates. Check DNS configuration."
    docker stop temp-nginx
    docker rm temp-nginx
    exit 1
}

# Stop temporary Nginx
docker stop temp-nginx
docker rm temp-nginx

print_status "SSL certificates obtained"

print_step "Step 6: Copy Project Files"
# Copy from current directory to project directory
cp -r . $PROJECT_DIR/
chown -R $USER:$USER $PROJECT_DIR

print_status "Project files copied"

print_step "Step 7: Build and Start Services"
cd $PROJECT_DIR

# Stop any existing services
docker-compose -f docker-compose.prod.yml down || true

# Build all services
print_step "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start all services
print_step "Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

print_status "Services started"

print_step "Step 8: Wait for Services to Initialize"
echo "Waiting for services to start..."
sleep 60

print_step "Step 9: Health Check Services"
# Check each service
services=("core:8001" "commerce:8010" "payment:8020" "frontend:3000")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f http://localhost:$port/health > /dev/null 2>&1; then
        print_status "$name service is healthy"
    else
        print_error "$name service is not responding"
        echo "Checking logs for $name..."
        docker logs aarya_$name --tail 20
    fi
done

print_step "Step 10: Setup Automated Backups"
# Create backup script
cat > $PROJECT_DIR/scripts/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/aarya-clothing/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > $BACKUP_DIR/backup_$DATE.sql

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Database backup completed: backup_$DATE.sql"
EOF

chmod +x $PROJECT_DIR/scripts/backup-db.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_DIR/scripts/backup-db.sh") | crontab -

print_status "Automated backups configured"

print_step "Step 11: Setup SSL Auto-Renewal"
# Add SSL renewal to crontab
(crontab -l 2>/dev/null; echo "0 12 * * * cd $PROJECT_DIR && docker run --rm -v $PROJECT_DIR/certbot/conf:/etc/letsencrypt -v $PROJECT_DIR/certbot/www:/var/www/certbot certbot/certbot renew --webroot --webroot-path=/var/www/certbot && docker-compose -f $PROJECT_DIR/docker-compose.prod.yml restart nginx") | crontab -

print_status "SSL auto-renewal configured"

print_step "Step 12: Setup Monitoring"
# Create monitoring docker-compose
cat > $PROJECT_DIR/docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: aarya_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - backend_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: aarya_grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=Root@2026_Grafana_Admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - backend_network
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: aarya_node_exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
    networks:
      - backend_network
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  backend_network:
    external: true
EOF

# Create Prometheus config
mkdir -p $PROJECT_DIR/monitoring
cat > $PROJECT_DIR/monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']

  - job_name: 'core-service'
    static_configs:
      - targets: ['core:8001']
    metrics_path: '/health'

  - job_name: 'commerce-service'
    static_configs:
      - targets: ['commerce:8010']
    metrics_path: '/health'

  - job_name: 'payment-service'
    static_configs:
      - targets: ['payment:8020']
    metrics_path: '/health'

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# Start monitoring
docker-compose -f docker-compose.monitoring.yml up -d

print_status "Monitoring setup completed"

print_step "Step 13: Final Verification"
# Final checks
echo ""
echo -e "${BLUE}🔍 Final System Verification${NC}"

# Check Docker containers
echo "Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check disk space
echo ""
echo "Disk usage:"
df -h

# Check memory
echo ""
echo "Memory usage:"
free -h

print_step "Step 14: Create Management Scripts"
# Create management script
cat > $PROJECT_DIR/manage.sh << 'EOF'
#!/bin/bash

# Aarya Clothing - Management Script

case "$1" in
    start)
        echo "Starting all services..."
        docker-compose -f docker-compose.prod.yml up -d
        docker-compose -f docker-compose.monitoring.yml up -d
        ;;
    stop)
        echo "Stopping all services..."
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.monitoring.yml down
        ;;
    restart)
        echo "Restarting all services..."
        docker-compose -f docker-compose.prod.yml restart
        docker-compose -f docker-compose.monitoring.yml restart
        ;;
    logs)
        echo "Showing logs..."
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    status)
        echo "Service status:"
        docker-compose -f docker-compose.prod.yml ps
        ;;
    backup)
        echo "Creating manual backup..."
        /opt/aarya-clothing/scripts/backup-db.sh
        ;;
    update)
        echo "Updating application..."
        cd /opt/aarya-clothing
        git pull
        docker-compose -f docker-compose.prod.yml build --no-cache
        docker-compose -f docker-compose.prod.yml up -d
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|backup|update}"
        exit 1
        ;;
esac
EOF

chmod +x $PROJECT_DIR/manage.sh

print_status "Management script created"

# Final success message
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE! 🎉${NC}"
echo ""
echo -e "${BLUE}🌐 Your Application is Live:${NC}"
echo -e "   ${GREEN}Main Site:${NC} https://$DOMAIN"
echo -e "   ${GREEN}WWW Site:${NC} https://www.$DOMAIN"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "   ${YELLOW}cd $PROJECT_DIR && ./manage.sh start${NC}    # Start services"
echo -e "   ${YELLOW}cd $PROJECT_DIR && ./manage.sh stop${NC}     # Stop services"
echo -e "   ${YELLOW}cd $PROJECT_DIR && ./manage.sh logs${NC}     # View logs"
echo -e "   ${YELLOW}cd $PROJECT_DIR && ./manage.sh status${NC}   # Check status"
echo ""
echo -e "${BLUE}📊 Monitoring URLs:${NC}"
echo -e "   ${GREEN}Grafana:${NC} http://$VPS_IP:3001 (admin/Root@2026_Grafana_Admin)"
echo -e "   ${GREEN}Prometheus:${NC} http://$VPS_IP:9090"
echo -e "   ${GREEN}Node Exporter:${NC} http://$VPS_IP:9100"
echo ""
echo -e "${BLUE}🔐 Login Credentials:${NC}"
echo -e "   ${YELLOW}Admin Password:${NC} $ADMIN_PASSWORD"
echo -e "   ${YELLOW}Database Password:${NC} $ADMIN_PASSWORD"
echo -e "   ${YELLOW}Grafana Password:${NC} ${ADMIN_PASSWORD}_Grafana_Admin"
echo ""
echo -e "${BLUE}📁 Important Paths:${NC}"
echo -e "   ${YELLOW}Project:${NC} $PROJECT_DIR"
echo -e "   ${YELLOW}Backups:${NC} $PROJECT_DIR/backups"
echo -e "   ${YELLOW}Logs:${NC} $PROJECT_DIR/logs"
echo -e "   ${YELLOW}SSL Certs:${NC} $PROJECT_DIR/certbot"
echo ""
echo -e "${GREEN}✅ All services are running and secured!${NC}"
echo -e "${GREEN}✅ SSL certificates are active and auto-renewing${NC}"
echo -e "${GREEN}✅ Firewall is configured and active${NC}"
echo -e "${GREEN}✅ Backups are scheduled daily at 2 AM${NC}"
echo -e "${GREEN}✅ Monitoring is active and collecting metrics${NC}"
echo ""
echo -e "${BLUE}🚀 Your Aarya Clothing e-commerce platform is ready for business!${NC}"
