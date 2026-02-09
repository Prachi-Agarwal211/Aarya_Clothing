# Aarya Clothing - VPS Deployment Guide

## Overview
Complete deployment guide for Aarya Clothing e-commerce platform on VPS 72.61.255.8 with domain aaryaclothing.cloud

## Prerequisites
- VPS with Docker and Docker Compose installed
- Domain aaryaclothing.cloud pointing to 72.61.255.8
- SSH access to VPS
- Root or sudo privileges

## Architecture
```
Internet → Nginx (443/80) → Frontend (3000)
                        → Core API (8001)
                        → Commerce API (8010)
                        → Payment API (8020)
                        → PostgreSQL (5432)
                        → Redis (6379)
```

## Quick Deployment Steps

### 1. SSH into your VPS
```bash
ssh root@72.61.255.8
```

### 2. Navigate to project directory
```bash
cd /opt/Aarya_Clothing
```

### 3. Verify .env file exists
```bash
ls -la .env
```

If .env doesn't exist, create it from example:
```bash
cp .env.example .env
nano .env
```

### 4. Make deployment scripts executable
```bash
chmod +x setup-ssl.sh
chmod +x deploy-vps.sh
```

### 5. Run deployment
```bash
./deploy-vps.sh
```

## Manual Deployment Steps

If you prefer manual deployment:

### Step 1: Generate SSL Certificates
```bash
./setup-ssl.sh
```

This creates:
- `docker/nginx/ssl/aaryaclothing.cloud.crt`
- `docker/nginx/ssl/aaryaclothing.cloud.key`

### Step 2: Stop Existing Containers
```bash
docker-compose down
```

### Step 3: Build and Start Services
```bash
docker-compose up -d --build
```

### Step 4: Verify Services
```bash
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
aarya_postgres      Up (healthy)        0.0.0.0:5432->5432/tcp
aarya_redis         Up (healthy)        0.0.0.0:6379->6379/tcp
aarya_core          Up                  8001/tcp
aarya_commerce      Up                  8010/tcp
aarya_payment       Up                  8020/tcp
aarya_frontend      Up                  3000/tcp
aarya_nginx         Up                  0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Step 5: Check Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f nginx
docker-compose logs -f frontend
docker-compose logs -f core
```

## Access URLs

After successful deployment:

- **Frontend**: https://aaryaclothing.cloud
- **Core API**: https://aaryaclothing.cloud/api/auth/
- **Products API**: https://aaryaclothing.cloud/api/products/
- **Categories API**: https://aaryaclothing.cloud/api/categories/
- **Cart API**: https://aaryaclothing.cloud/api/cart/
- **Orders API**: https://aaryaclothing.cloud/api/orders/
- **Payments API**: https://aaryaclothing.cloud/api/payments/
- **Health Check**: https://aaryaclothing.cloud/health

## SSL Certificate Notes

### Self-Signed Certificates (Current Setup)
- Generated automatically by `setup-ssl.sh`
- Valid for 365 days
- Browser will show security warning (normal for self-signed)
- Accept the warning to proceed

### Production SSL (Recommended)
For production, use Let's Encrypt:

```bash
# Install certbot
apt-get update
apt-get install certbot

# Generate certificates
certbot certonly --standalone -d aaryaclothing.cloud -d www.aaryaclothing.cloud

# Copy certificates to nginx ssl directory
cp /etc/letsencrypt/live/aaryaclothing.cloud/fullchain.pem docker/nginx/ssl/aaryaclothing.cloud.crt
cp /etc/letsencrypt/live/aaryaclothing.cloud/privkey.pem docker/nginx/ssl/aaryaclothing.cloud.key

# Restart nginx
docker-compose restart nginx
```

## Firewall Configuration

Ensure ports 80 and 443 are open:

```bash
# UFW (Ubuntu/Debian)
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# iptables (alternative)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

## Common Commands

### View running containers
```bash
docker ps
```

### View container logs
```bash
docker logs aarya_nginx
docker logs aarya_frontend
docker logs aarya_core
docker logs aarya_commerce
docker logs aarya_payment
```

### Restart specific service
```bash
docker-compose restart nginx
docker-compose restart frontend
docker-compose restart core
```

### Stop all services
```bash
docker-compose down
```

### Start all services
```bash
docker-compose up -d
```

### Rebuild specific service
```bash
docker-compose up -d --build frontend
```

### Access container shell
```bash
docker exec -it aarya_core /bin/bash
docker exec -it aarya_postgres psql -U postgres -d aarya_clothing
```

## Troubleshooting

### Services not starting
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check Docker resources
docker system df
```

### Database connection issues
```bash
# Check PostgreSQL
docker exec -it aarya_postgres pg_isready -U postgres

# Connect to database
docker exec -it aarya_postgres psql -U postgres -d aarya_clothing
```

### Redis connection issues
```bash
# Check Redis
docker exec -it aarya_redis redis-cli ping
```

### Nginx configuration issues
```bash
# Test nginx config
docker exec -it aarya_nginx nginx -t

# Reload nginx
docker exec -it aarya_nginx nginx -s reload
```

### SSL certificate issues
```bash
# Check certificate
openssl x509 -in docker/nginx/ssl/aaryaclothing.cloud.crt -text -noout

# Regenerate certificates
./setup-ssl.sh
docker-compose restart nginx
```

### Port conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Stop conflicting services
systemctl stop nginx  # if system nginx is running
```

## Monitoring

### Check service health
```bash
# All services
docker-compose ps

# Specific service health
docker inspect aarya_postgres | grep -A 10 Health
```

### View resource usage
```bash
docker stats
```

### View logs in real-time
```bash
docker-compose logs -f --tail=100
```

## Backup

### Backup database
```bash
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > backup_$(date +%Y%m%d).sql
```

### Backup volumes
```bash
docker run --rm -v aarya_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## Updates

### Update code
```bash
git pull
docker-compose up -d --build
```

### Update specific service
```bash
docker-compose up -d --build frontend
```

## Security Recommendations

1. **Change default passwords** in .env file
2. **Use strong JWT secrets** (already configured)
3. **Enable firewall** (only allow 80, 443)
4. **Use production SSL certificates** (Let's Encrypt)
5. **Regular updates**: Keep Docker and containers updated
6. **Monitor logs**: Check for suspicious activity
7. **Backup regularly**: Database and important data

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Verify configuration: `docker-compose config`
- Test connectivity: `curl https://aaryaclothing.cloud/health`

## Deployment Checklist

- [ ] Domain aaryaclothing.cloud points to 72.61.255.8
- [ ] .env file configured with production values
- [ ] SSL certificates generated
- [ ] Docker and Docker Compose installed
- [ ] Firewall configured (ports 80, 443 open)
- [ ] All services running: `docker-compose ps`
- [ ] Frontend accessible: https://aaryaclothing.cloud
- [ ] API endpoints responding
- [ ] Database connection working
- [ ] Redis connection working
- [ ] Nginx reverse proxy working
- [ ] SSL certificate valid

## Success Indicators

✅ All containers show "Up" status
✅ Frontend loads at https://aaryaclothing.cloud
✅ API endpoints return responses
✅ No errors in logs
✅ Health check returns 200 OK
✅ SSL certificate is valid (or accepted for self-signed)

---

**Deployment Date**: 2026-02-09
**VPS IP**: 72.61.255.8
**Domain**: aaryaclothing.cloud
