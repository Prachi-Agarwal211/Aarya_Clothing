# Production Deployment Checklist

This checklist covers deploying Aarya Clothing microservices to production.

---

## 1. Pre-Deployment

### 1.1 Server Requirements

- [ ] At least 4GB RAM available
- [ ] At least 20GB disk space
- [ ] Ports 3000, 8001, 8010, 8020, 5432, 6379 available
- [ ] Docker & Docker Compose installed

### 1.2 System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker if needed
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
```

---

## 2. Deployment Steps

### 2.1 Clone Repository

```bash
cd /opt
sudo git clone https://github.com/your-repo/Aarya_Clothing.git
sudo chown -R $USER:$USER Aarya_Clothing
cd Aarya_Clothing
```

### 2.2 Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit with secure values
nano .env
```

Required environment variables:
```bash
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET_KEY=your-super-secret-key
NEXT_PUBLIC_API_URL=http://your-domain:8001
```

### 2.3 Start Services

```bash
# Build and start
docker-compose up -d --build

# Wait for services
sleep 30

# Verify
docker-compose ps
```

---

## 3. Health Checks

### 3.1 Verify Services

```bash
# Core Platform
curl http://localhost:8001/health

# Commerce Service
curl http://localhost:8010/health

# Payment Service
curl http://localhost:8020/health

# Frontend
curl http://localhost:3000
```

### 3.2 Verify Database

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check Redis
docker-compose exec redis redis-cli ping
```

---

## 4. Post-Deployment

### 4.1 Functional Tests

- [ ] User registration works
- [ ] User login works
- [ ] Product listing loads
- [ ] Add to cart works
- [ ] Order creation works

### 4.2 Performance Check

```bash
# Check response times
curl -w "\nTime: %{time_total}s\n" -o /dev/null -s http://localhost:8001/health

# Check Docker stats
docker stats
```

---

## 5. Maintenance

### 5.1 Common Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop with data
docker-compose down -v
```

### 5.2 Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres aarya_clothing > backup_$(date +%Y%m%d).sql

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
docker-compose cp redis:/data/dump.rdb ./redis_backup.rdb
```

---

## 6. Rollback

If issues occur:

```bash
# Stop services
docker-compose down

# Restore database if needed
docker-compose exec -T postgres psql -U postgres -d aarya_clothing < backup_file.sql

# Restart
docker-compose up -d
```

---

## 7. Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS (configure reverse proxy)
- [ ] Keep secrets out of version control
- [ ] Regular dependency updates
- [ ] Monitor logs for suspicious activity
