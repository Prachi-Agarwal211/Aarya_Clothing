# Data Persistence & Safe Deployment Guide

## 🛡️ Will Updates Delete My Database?

**NO!** Your database is **safe** during updates. Here's why:

### How Your Data is Protected

Your [`docker-compose.yml`](docker-compose.yml:20) uses **Docker volumes** for persistent storage:

```yaml
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data  # ← Your database lives here

volumes:
  postgres_data:  # ← Persistent volume
    driver: local
```

**What this means:**
- ✅ Database data is stored in a separate Docker volume
- ✅ Data persists even when containers are stopped
- ✅ Data persists even when containers are removed
- ✅ Data persists even when you rebuild images
- ✅ Data persists even when you run `docker-compose down`

## 📊 What Gets Preserved

| Data Type | Location | Preserved During Updates? |
|------------|----------|-------------------------|
| **Database** (users, products, orders, etc.) | Docker volume `postgres_data` | ✅ YES |
| **Redis cache** (sessions, cart data) | Docker volume `redis_data` | ✅ YES |
| **Uploaded files** (if any) | Container filesystem | ❌ NO (see below) |
| **Application code** | Container image | ❌ NO (replaced on rebuild) |

## ⚠️ What Gets Lost During Updates

### 1. Application Code
When you rebuild containers, the application code is replaced with the new version. This is **expected and desired**.

### 2. Uploaded Files (If Any)
If your application allows file uploads (product images, user avatars, etc.), these are stored in the container filesystem and **will be lost** during rebuilds.

**Solution:** Use Cloudflare R2 or S3 for file storage (already configured in your `.env`).

## 🔄 Safe Deployment Commands

### ✅ SAFE - Preserves Database

```bash
# Pull latest code
git pull origin testing

# Rebuild and restart (database preserved)
docker-compose up -d --build

# Or use the fix script
./fix-and-redeploy.sh
```

### ✅ SAFE - Preserves Database

```bash
# Stop containers (database preserved)
docker-compose down

# Start containers (database preserved)
docker-compose up -d
```

### ✅ SAFE - Preserves Database

```bash
# Restart specific service (database preserved)
docker-compose restart frontend
docker-compose restart core
```

### ⚠️ DANGEROUS - Deletes Database

```bash
# NEVER RUN THIS unless you want to delete everything
docker-compose down -v  # ← The -v flag removes volumes!
```

### ⚠️ DANGEROUS - Deletes Database

```bash
# NEVER RUN THIS unless you want to delete everything
docker volume rm aarya_clothing_postgres_data
```

## 💾 Backup Strategy

### Automatic Backups (Recommended)

Set up automated daily backups:

```bash
# Create backup script
cat > /opt/Aarya_Clothing/backup-database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/Aarya_Clothing/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql"
EOF

chmod +x /opt/Aarya_Clothing/backup-database.sh

# Add to cron (daily at 2 AM)
crontab -e
# Add this line:
0 2 * * * /opt/Aarya_Clothing/backup-database.sh
```

### Manual Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > backups/backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v aarya_clothing_postgres_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/postgres_volume_$(date +%Y%m%d).tar.gz /data
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Remove old volume (WARNING: This deletes current data!)
docker volume rm aarya_clothing_postgres_data

# Create new volume
docker volume create aarya_clothing_postgres_data

# Start services
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
sleep 10

# Restore database
docker exec -i aarya_postgres psql -U postgres aarya_clothing < backups/backup_20260209.sql

# Start remaining services
docker-compose up -d
```

## 🧪 Testing Updates Safely

### Before Production Update

1. **Backup first:**
   ```bash
   docker exec aarya_postgres pg_dump -U postgres aarya_clothing > backup_before_update.sql
   ```

2. **Test on staging:**
   ```bash
   # Create staging environment
   docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
   ```

3. **Update production:**
   ```bash
   git pull origin testing
   docker-compose up -d --build
   ```

4. **Verify:**
   ```bash
   # Check if data is intact
   docker exec -it aarya_postgres psql -U postgres -d aarya_clothing -c "SELECT COUNT(*) FROM users;"
   ```

## 📋 Update Checklist

Before running updates:

- [ ] Create database backup
- [ ] Test changes in staging (if possible)
- [ ] Review git diff to see what changed
- [ ] Check for database migrations in code
- [ ] Notify users of planned maintenance (if needed)

After running updates:

- [ ] Verify all services are running: `docker-compose ps`
- [ ] Check logs for errors: `docker-compose logs`
- [ ] Test critical functionality (login, checkout, etc.)
- [ ] Verify database integrity
- [ ] Monitor for issues for 24 hours

## 🔍 Check Database Integrity

```bash
# Connect to database
docker exec -it aarya_postgres psql -U postgres -d aarya_clothing

# Check tables
\dt

# Check user count
SELECT COUNT(*) FROM users;

# Check product count
SELECT COUNT(*) FROM products;

# Check order count
SELECT COUNT(*) FROM orders;

# Exit
\q
```

## 🚨 Emergency Recovery

If something goes wrong during update:

```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
docker exec -i aarya_postgres psql -U postgres aarya_clothing < backup_before_update.sql

# 3. Start services
docker-compose up -d

# 4. Verify
docker-compose ps
```

## 📊 Monitoring Data

### Check Volume Usage

```bash
# List all volumes
docker volume ls

# Check volume size
docker system df -v | grep postgres_data

# Inspect volume
docker volume inspect aarya_clothing_postgres_data
```

### Check Database Size

```bash
docker exec -it aarya_postgres psql -U postgres -d aarya_clothing -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE pg_database.datname = 'aarya_clothing';
"
```

## ✅ Summary

**Your database is SAFE during normal updates:**

✅ `git pull` - Safe
✅ `docker-compose up -d --build` - Safe
✅ `docker-compose restart` - Safe
✅ `docker-compose down` - Safe
✅ `./fix-and-redeploy.sh` - Safe

**Only these commands delete your database:**

❌ `docker-compose down -v` - Deletes volumes
❌ `docker volume rm` - Deletes specific volume
❌ `docker system prune -a --volumes` - Deletes all volumes

**Best Practices:**

1. Always backup before major updates
2. Test changes in staging first
3. Monitor after updates
4. Set up automated daily backups
5. Keep backups for at least 7 days

---

*Last Updated: 2026-02-09*
