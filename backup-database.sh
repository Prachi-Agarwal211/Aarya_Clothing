#!/bin/bash

# Aarya Clothing - Database Backup Script
# Creates automated backups of PostgreSQL database

set -e

echo "=========================================="
echo "Aarya Clothing - Database Backup"
echo "=========================================="

# Configuration
BACKUP_DIR="/opt/Aarya_Clothing/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Backup directory: $BACKUP_DIR"
echo "Backup file: $BACKUP_FILE"
echo ""

# Check if PostgreSQL is running
if ! docker ps | grep -q aarya_postgres; then
    echo "❌ Error: PostgreSQL container is not running"
    echo "   Start services first: docker-compose up -d"
    exit 1
fi

# Create backup
echo "Creating database backup..."
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > $BACKUP_FILE

# Check if backup was created
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
    echo "✓ Backup created successfully"
    echo "  File: $BACKUP_FILE"
    echo "  Size: $BACKUP_SIZE"
else
    echo "❌ Error: Backup file was not created"
    exit 1
fi

# Compress backup
echo ""
echo "Compressing backup..."
gzip $BACKUP_FILE
BACKUP_FILE="${BACKUP_FILE}.gz"
BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
echo "✓ Backup compressed"
echo "  File: $BACKUP_FILE"
echo "  Size: $BACKUP_SIZE"

# Remove old backups
echo ""
echo "Removing backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
REMOVED_COUNT=$(find $BACKUP_DIR -name "backup_*.sql.gz" | wc -l)
echo "✓ Old backups removed"
echo "  Current backups: $REMOVED_COUNT"

# List all backups
echo ""
echo "Available backups:"
ls -lh $BACKUP_DIR/backup_*.sql.gz 2>/dev/null || echo "  No backups found"

echo ""
echo "=========================================="
echo "Backup Complete!"
echo "=========================================="
echo ""
echo "To restore from backup:"
echo "  gunzip < $BACKUP_FILE | docker exec -i aarya_postgres psql -U postgres aarya_clothing"
echo ""
echo "To view backup contents:"
echo "  gunzip -c $BACKUP_FILE | head -n 50"
echo ""
