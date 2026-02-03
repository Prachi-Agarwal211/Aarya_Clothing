# Aarya Clothing - Production Deployment Checklist

This document provides a comprehensive checklist for deploying Aarya Clothing to production.

---

## 1. Pre-Deployment Checklist

### 1.1 Environment Preparation

```bash
# Verify server specifications
CPU_CORES=$(nproc)
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
DISK_SSD=$(lsblk -d --output NAME,ROTA | awk 'NR==2 {print $2}')
NVME_SPEED=$(cat /sys/block/nvme0n1/queue/rotational)

echo "CPU Cores: $CPU_CORES"
echo "RAM (GB): $RAM_GB"
echo "Storage Type: $([ "$DISK_SSD" = "0" ] && echo "NVMe/SSD" || echo "HDD")"
```

**Requirements:**
- [ ] CPU: Minimum 4 cores (8+ recommended)
- [ ] RAM: Minimum 16GB (32GB recommended)
- [ ] Storage: NVMe SSD with 100GB+ free space
- [ ] Network: 1Gbps connection

### 1.2 Operating System Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    vim \
    htop \
    iotop \
    ntp

# Configure timezone
sudo timedatectl set-timezone UTC

# Configure sysctl
cat >> /etc/sysctl.conf << EOF
# Aarya Clothing Production Settings
vm.swappiness=10
vm.max_map_count=262144
fs.file-max=65536
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
net.core.netdev_max_backlog=65535
EOF

sudo sysctl -p
```

**OS Checklist:**
- [ ] System updated
- [ ] Timezone configured (UTC)
- [ ] NTP service enabled
- [ ] SWappiness set to 10
- [ ] File descriptor limits increased
- [ ] Kernel parameters applied

### 1.3 Docker Installation

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose V2
sudo mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Configure Docker daemon
sudo mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOF
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  },
  "metrics-addr": "0.0.0.0:9323",
  "experimental": true
}
EOF

sudo systemctl restart docker
sudo systemctl enable docker
```

**Docker Checklist:**
- [ ] Docker CE installed
- [ ] Docker Compose V2 installed
- [ ] Docker daemon configured
- [ ] Docker service enabled
- [ ] Docker-compose command verified

### 1.4 SSL/TLS Certificates

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate certificates
sudo certbot --nginx -d api.yourdomain.com
sudo certbot --nginx -d yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

**SSL Checklist:**
- [ ] SSL certificates obtained
- [ ] Certificate renewal cron job configured
- [ ] HTTPS redirects configured in Nginx
- [ ] HSTS header enabled

### 1.5 Secret Management

```bash
# Create secrets directory
mkdir -p /opt/aarya/secrets
chmod 700 /opt/aarya/secrets

# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Store secrets (use a secrets manager in production)
echo "$POSTGRES_PASSWORD" > /opt/aarya/secrets/postgres_password
echo "$JWT_SECRET_KEY" > /opt/aarya/secrets/jwt_secret
echo "$ENCRYPTION_KEY" > /opt/aarya/secrets/encryption_key

chmod 600 /opt/aarya/secrets/*
```

**Secrets Checklist:**
- [ ] PostgreSQL password generated
- [ ] JWT secret key generated
- [ ] Encryption keys generated
- [ ] Secrets stored securely
- [ ] API keys obtained (Stripe, SMTP, etc.)

---

## 2. Application Deployment

### 2.1 Clone and Configure

```bash
# Clone repository
cd /opt/aarya
sudo git clone https://github.com/your-org/aarya-clothing.git .
sudo chown -R $USER:$USER /opt/aarya

# Create required directories
mkdir -p /data/postgres/{data,wal,replica}
mkdir -p /data/redis
mkdir -p /data/elasticsearch
mkdir -p /data/prometheus
mkdir -p /data/grafana
mkdir -p /data/loki

# Set permissions
sudo chown -R 999:999 /data/postgres
sudo chown -R 1000:1000 /data/elasticsearch
```

**Directory Checklist:**
- [ ] Repository cloned
- [ ] Required directories created
- [ ] Permissions configured

### 2.2 Environment Configuration

```bash
# Create .env file
cat > .env << EOF
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# PostgreSQL
POSTGRES_PASSWORD=your_secure_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# Security
JWT_SECRET_KEY=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# External Services
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your_smtp_password

# Domain
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
DOMAIN_NAME=yourdomain.com

# Monitoring
GRAFANA_ADMIN_PASSWORD=your_grafana_password
EOF

chmod 600 .env
```

**Environment Checklist:**
- [ ] .env file created
- [ ] All secrets configured
- [ ] Domain URLs set
- [ ] External API keys configured

### 2.3 Docker Configuration Files

```bash
# Create necessary directories
mkdir -p docker/{postgres,redis,elasticsearch,gateway,core_platform,commerce,content,search,monitoring,worker}

# Copy example configs and modify
cp backend/.env.example backend/.env
```

**Configuration Checklist:**
- [ ] PostgreSQL config created
- [ ] Redis config created
- [ ] Elasticsearch config created
- [ ] Nginx/Gateway config created
- [ ] Monitoring configs created

---

## 3. Database Setup

### 3.1 Initialize PostgreSQL

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for initialization
sleep 30

# Verify PostgreSQL is ready
docker exec -it aarya_postgres pg_isready -U postgres

# Run migrations
docker-compose exec -T postgres psql -U postgres -d aarya_clothing -f /docker-entrypoint-initdb.d/init.sql

# Create read replica user (on primary)
docker exec -it aarya_postgres psql -U postgres -c "
CREATE USER replica_user WITH REPLICATION PASSWORD 'replica_password';
"
```

**Database Checklist:**
- [ ] PostgreSQL started
- [ ] Database created
- [ ] Tables initialized
- [ ] User accounts created
- [ ] Replication configured

### 3.2 Initialize Redis

```bash
# Start Redis
docker-compose up -d redis

# Verify Redis
docker exec -it aarya_redis redis-cli ping
docker exec -it aarya_redis redis-cli info memory

# Test ACL
docker exec -it aarya_redis redis-cli -a your_password ACL LIST
```

**Redis Checklist:**
- [ ] Redis started
- [ ] Authentication configured
- [ ] Persistence enabled
- [ ] Memory limits set

### 3.3 Initialize Elasticsearch

```bash
# Start Elasticsearch
docker-compose up -d elasticsearch

# Wait for startup
sleep 30

# Verify
curl -s http://localhost:9200/_cluster/health

# Create indices
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d @docker/elasticsearch/products_mapping.json
curl -X PUT "localhost:9200/users" -H 'Content-Type: application/json' -d @docker/elasticsearch/users_mapping.json
```

**Elasticsearch Checklist:**
- [ ] Elasticsearch started
- [ ] Cluster health green
- [ ] Indices created
- [ ] Mappings applied

---

## 4. Application Services

### 4.1 Build and Deploy Services

```bash
# Build all services
docker-compose build --no-cache

# Start core services first
docker-compose up -d postgres redis elasticsearch

# Wait for dependencies
sleep 30

# Start application services
docker-compose up -d core_platform

# Verify health
curl http://localhost:8001/health

# Start remaining services
docker-compose up -d commerce payment content_services search_recommendation api_gateway frontend

# Verify all services
docker-compose ps
```

**Service Checklist:**
- [ ] All services built
- [ ] All services started
- [ ] All health checks passing
- [ ] Services responding to requests

### 4.2 Verify Inter-Service Communication

```bash
# Test API Gateway
curl -f https://api.yourdomain.com/health

# Test service endpoints
curl -f http://localhost:8001/health
curl -f http://localhost:8010/health
curl -f http://localhost:8020/health
curl -f http://localhost:8030/health
curl -f http://localhost:8040/health

# Test database connections
docker-compose exec core_platform python -c "from database import get_db; db = next(get_db()); print('Core DB: OK')"
docker-compose exec commerce python -c "from database import get_db; db = next(get_db()); print('Commerce DB: OK')"
```

**Communication Checklist:**
- [ ] Gateway responding
- [ ] All services healthy
- [ ] Database connections working
- [ ] Redis connections working
- [ ] Elasticsearch connections working

---

## 5. Post-Deployment Verification

### 5.1 Functional Testing

```bash
# Run smoke tests
./tests/smoke_test.sh

# Run integration tests
./tests/integration_test.sh

# Run load tests (optional)
./tests/load_test.sh --duration=300 --users=50
```

**Functional Checklist:**
- [ ] Smoke tests passing
- [ ] Integration tests passing
- [ ] User registration working
- [ ] Product browsing working
- [ ] Cart operations working
- [ ] Checkout flow working
- [ ] Payment processing working

### 5.2 Performance Verification

```bash
# Check response times
curl -w "\nTime: %{time_total}s\n" -o /dev/null -s https://api.yourdomain.com/health

# Check database query performance
docker-compose exec postgres psql -U postgres -d aarya_clothing -c "SELECT * FROM pg_stat_activity;"

# Check Redis performance
docker exec -it aarya_redis redis-cli --stat

# Monitor resource usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
```

**Performance Checklist:**
- [ ] API response time < 200ms
- [ ] Database connections < 80%
- [ ] Redis memory < 80%
- [ ] CPU usage < 70%

### 5.3 Security Verification

```bash
# Check SSL configuration
curl -sI https://api.yourdomain.com | grep -i "strict-transport-security"

# Verify headers
curl -sI https://api.yourdomain.com | grep -iE "(x-frame-options|x-content-type-options|csp)"

# Check for exposed ports
netstat -tlnp | grep docker

# Verify authentication
curl -f https://api.yourdomain.com/api/v1/users/me -H "Authorization: Bearer invalid" | jq .
```

**Security Checklist:**
- [ ] HTTPS enabled
- [ ] HSTS header present
- [ ] Security headers present
- [ ] No unnecessary ports exposed
- [ ] Authentication working
- [ ] Authorization enforced

---

## 6. Monitoring Setup

### 6.1 Start Monitoring Stack

```bash
# Start Prometheus
docker-compose up -d prometheus

# Start Grafana
docker-compose up -d grafana

# Start Loki and Promtail
docker-compose up -d loki promtail
```

**Monitoring Checklist:**
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards available
- [ ] Logs flowing to Loki
- [ ] Alert rules configured

### 6.2 Configure Alerts

```bash
# Verify alert rules
curl -s http://localhost:9090/api/v1/rules | jq .

# Test alert firing
# Trigger a test alert (if configured)
curl -X POST http://localhost:9090/api/v1/alerts -H "Content-Type: application/json" -d @docker/monitoring/test_alert.json
```

**Alert Checklist:**
- [ ] Alert rules loaded
- [ ] Alertmanager configured
- [ ] Email/Slack notifications tested
- [ ] PagerDuty integration working (if applicable)

---

## 7. Backup and Recovery

### 7.1 Configure Backups

```bash
# Create backup script
cat > /opt/aarya/scripts/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR=/data/backups
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker exec aarya_postgres pg_dump -U postgres aarya_clothing | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Redis backup
docker exec aarya_redis redis-cli BGSAVE
docker exec aarya_redis redis-cli LASTSAVE > $BACKUP_DIR/redis_$DATE.txt
docker cp aarya_redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Elasticsearch backup (optional)
curl -X PUT "localhost:9200/_snapshot/aarya_backup/snapshot_$DATE?wait_for_completion=true"

# Upload to S3/R2 (optional)
# aws s3 cp $BACKUP_DIR/ s3://aarya-backups/ --recursive

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.txt" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/aarya/scripts/backup.sh

# Schedule daily backups
echo "0 3 * * * /opt/aarya/scripts/backup.sh" | sudo tee -a /etc/crontab
```

**Backup Checklist:**
- [ ] Backup script created
- [ ] Backup directory created
- [ ] Cron job scheduled
- [ ] Backup verification tested
- [ ] Restore procedure documented

### 7.2 Recovery Procedure

```bash
# Create recovery script
cat > /opt/aarya/scripts/recover.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# Stop application
docker-compose stop core_platform commerce payment content_services search_recommendation

# Restore PostgreSQL
docker exec -i aarya_postgres psql -U postgres -d aarya_clothing < <(gunzip -c $BACKUP_FILE)

# Restart application
docker-compose start core_platform commerce payment content_services search_recommendation

echo "Recovery completed from: $BACKUP_FILE"
EOF

chmod +x /opt/aarya/scripts/recover.sh
```

**Recovery Checklist:**
- [ ] Recovery script created
- [ ] Recovery tested from backup
- [ ] Rollback procedure documented

---

## 8. Documentation

### 8.1 Update Documentation

```bash
# Document deployment
echo "$(date): Production deployment completed" >> /opt/aarya/deployment_log.txt

# Document current versions
docker-compose version > /opt/aarya/versions.txt
echo "Deployment Date: $(date)" >> /opt/aarya/versions.txt
```

**Documentation Checklist:**
- [ ] Deployment log maintained
- [ ] Version history documented
- [ ] Architecture diagram updated
- [ ] Runbooks created

---

## 9. Handover

### 9.1 Pre-Handover Checklist

```bash
# Final verification
echo "=== Final Deployment Status ==="
docker-compose ps
echo ""
echo "=== Resource Usage ==="
docker stats --no-stream
echo ""
echo "=== Recent Logs ==="
docker-compose logs --tail=50
```

**Handover Checklist:**
- [ ] All services running
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Documentation complete
- [ ] Team trained
- [ ] On-call schedule configured
- [ ] Escalation policy defined

---

## Emergency Contacts

| Role | Contact |
|------|---------|
| DevOps Lead | [EMAIL] |
| Backend Lead | [EMAIL] |
| Infrastructure | [EMAIL] |
| Security | [EMAIL] |

---

## Rollback Procedure

If deployment fails:

```bash
# Option 1: Rollback to previous version
git checkout previous_tag
docker-compose down
docker-compose pull
docker-compose up -d

# Option 2: Restore from backup
/opt/aarya/scripts/recover.sh /data/backups/postgres_previous_backup.sql.gz
```

---

## Quick Commands

```bash
# View logs
docker-compose logs -f

# Restart all services
docker-compose restart

# Check health
docker-compose ps | grep -E "(Up|Down)" | grep Down

# Scale a service (if using Swarm)
docker-compose scale core_platform=3

# Update single service
docker-compose up -d --no-deps core_platform
```
