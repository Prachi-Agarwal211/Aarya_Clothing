# Aarya Clothing - Troubleshooting Guide

## Common Deployment Issues and Solutions

### Issue 1: Frontend Build Fails - TypeScript Not Found

**Error:**
```
Error: Cannot find module 'typescript'
```

**Cause:**
The frontend Dockerfile was only installing production dependencies, but the build process requires TypeScript and other dev dependencies.

**Solution:**
The Dockerfile has been fixed. Pull the latest changes and redeploy:

```bash
git pull origin testing
./fix-and-redeploy.sh
```

---

### Issue 2: Shell Variable Expansion Warnings

**Error:**
```
WARNING: The "vL8" variable is not set. Defaulting to a blank string.
WARNING: The "oP3" variable is not set. Defaulting to a blank string.
```

**Cause:**
The `.env` file contains special characters (`$`) that are being interpreted as shell variables:
```
JWT_SECRET_KEY=Kj9#mP2$vL8@wQ5!nR3&tY6*zX1%bN4^cD7
SECRET_KEY=Hf4@qW8!rE2&tY6#uI9$oP3^vB5*mZ1
```

**Solution:**
Run the fix script to properly escape these values:

```bash
./fix-and-redeploy.sh
```

Or manually edit `.env` and wrap the values in quotes:
```bash
JWT_SECRET_KEY="Kj9#mP2$vL8@wQ5!nR3&tY6*zX1%bN4^cD7"
SECRET_KEY="Hf4@qW8!rE2&tY6#uI9$oP3^vB5*mZ1"
```

---

### Issue 3: Containers Not Starting

**Symptoms:**
- `docker-compose ps` shows containers as "Exited" or "Restarting"
- Services not accessible

**Solution:**

1. Check logs:
```bash
docker-compose logs
```

2. Check specific service:
```bash
docker-compose logs frontend
docker-compose logs core
docker-compose logs commerce
docker-compose logs payment
```

3. Restart services:
```bash
docker-compose restart
```

4. If still failing, rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

### Issue 4: Database Connection Errors

**Error:**
```
connection to server at "postgres" (172.x.x.x), port 5432 failed
```

**Solution:**

1. Check if PostgreSQL is running:
```bash
docker exec aarya_postgres pg_isready -U postgres
```

2. Check PostgreSQL logs:
```bash
docker logs aarya_postgres
```

3. Restart PostgreSQL:
```bash
docker-compose restart postgres
```

4. Verify database exists:
```bash
docker exec -it aarya_postgres psql -U postgres -d aarya_clothing
```

---

### Issue 5: Redis Connection Errors

**Error:**
```
Error connecting to Redis
```

**Solution:**

1. Check if Redis is running:
```bash
docker exec aarya_redis redis-cli ping
```

2. Check Redis logs:
```bash
docker logs aarya_redis
```

3. Restart Redis:
```bash
docker-compose restart redis
```

---

### Issue 6: Nginx Configuration Errors

**Error:**
```
nginx: [emerg] invalid number of arguments in "ssl_certificate" directive
```

**Solution:**

1. Check if SSL certificates exist:
```bash
ls -la docker/nginx/ssl/
```

2. If missing, generate them:
```bash
./setup-ssl.sh
```

3. Test Nginx configuration:
```bash
docker exec -it aarya_nginx nginx -t
```

4. Reload Nginx:
```bash
docker exec -it aarya_nginx nginx -s reload
```

---

### Issue 7: Port Already in Use

**Error:**
```
Bind for 0.0.0.0:80 failed: port is already allocated
```

**Solution:**

1. Check what's using the port:
```bash
netstat -tulpn | grep :80
netstat -tulpn | grep :443
```

2. Stop conflicting service (e.g., system nginx):
```bash
systemctl stop nginx
```

3. Restart Docker containers:
```bash
docker-compose restart nginx
```

---

### Issue 8: SSL Certificate Browser Warning

**Symptoms:**
- Browser shows "Your connection is not private" warning
- "NET::ERR_CERT_AUTHORITY_INVALID"

**Cause:**
Using self-signed SSL certificates (normal for testing)

**Solution:**

1. For testing: Click "Advanced" → "Proceed to aaryaclothing.cloud (unsafe)"
2. For production: Use Let's Encrypt certificates:

```bash
# Install certbot
apt-get update
apt-get install certbot

# Generate certificates
certbot certonly --standalone -d aaryaclothing.cloud -d www.aaryaclothing.cloud

# Copy certificates
cp /etc/letsencrypt/live/aaryaclothing.cloud/fullchain.pem docker/nginx/ssl/aaryaclothing.cloud.crt
cp /etc/letsencrypt/live/aaryaclothing.cloud/privkey.pem docker/nginx/ssl/aaryaclothing.cloud.key

# Restart nginx
docker-compose restart nginx
```

---

### Issue 9: Out of Disk Space

**Error:**
```
no space left on device
```

**Solution:**

1. Check disk usage:
```bash
df -h
```

2. Clean Docker system:
```bash
docker system prune -a
```

3. Remove old Docker images:
```bash
docker image prune -a
```

4. Remove unused volumes:
```bash
docker volume prune
```

---

### Issue 10: API Endpoints Not Responding

**Symptoms:**
- Frontend loads but API calls fail
- 502 Bad Gateway errors

**Solution:**

1. Check if backend services are running:
```bash
docker-compose ps
```

2. Check backend service logs:
```bash
docker-compose logs core
docker-compose logs commerce
docker-compose logs payment
```

3. Test API directly:
```bash
curl http://localhost:8001/health
curl http://localhost:8010/health
curl http://localhost:8020/health
```

4. Restart backend services:
```bash
docker-compose restart core commerce payment
```

---

## Quick Fix Commands

### Fix Everything at Once
```bash
./fix-and-redeploy.sh
```

### Check All Services
```bash
./health-check.sh
```

### View All Logs
```bash
docker-compose logs -f
```

### Restart All Services
```bash
docker-compose restart
```

### Clean and Rebuild
```bash
docker-compose down
docker system prune -f
docker-compose up -d --build
```

---

## Getting Help

If you're still having issues:

1. **Check logs first:**
   ```bash
   docker-compose logs -f --tail=100
   ```

2. **Run health check:**
   ```bash
   ./health-check.sh
   ```

3. **Verify configuration:**
   ```bash
   docker-compose config
   ```

4. **Check Docker resources:**
   ```bash
   docker stats
   docker system df
   ```

5. **Test connectivity:**
   ```bash
   curl https://aaryaclothing.cloud/health
   ```

---

## Prevention Tips

1. **Always pull latest changes before deploying:**
   ```bash
   git pull origin testing
   ```

2. **Use the fix-and-redeploy script:**
   ```bash
   ./fix-and-redeploy.sh
   ```

3. **Monitor logs regularly:**
   ```bash
   docker-compose logs -f
   ```

4. **Keep Docker updated:**
   ```bash
   apt-get update && apt-get upgrade docker docker-compose
   ```

5. **Regular backups:**
   ```bash
   docker exec aarya_postgres pg_dump -U postgres aarya_clothing > backup_$(date +%Y%m%d).sql
   ```

---

## Emergency Recovery

If everything is broken:

```bash
# Stop everything
docker-compose down

# Clean Docker
docker system prune -a --volumes

# Pull latest code
git pull origin testing

# Fix and redeploy
./fix-and-redeploy.sh
```

---

*Last Updated: 2026-02-09*
