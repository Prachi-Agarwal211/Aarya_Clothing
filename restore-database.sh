#!/bin/bash

# Aarya Clothing - Database Restore Script
# Restores PostgreSQL database from backup

set -e

echo "=========================================="
echo "Aarya Clothing - Database Restore"
echo "=========================================="

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh /opt/Aarya_Clothing/backups/backup_*.sql.gz 2>/dev/null || echo "  No backups found"
    echo ""
    exit 1
fi

BACKUP_FILE=$1

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Backup file: $BACKUP_FILE"
echo ""

# Confirm restore
echo "⚠️  WARNING: This will replace your current database!"
echo "   All existing data will be lost."
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if PostgreSQL is running
if ! docker ps | grep -q aarya_postgres; then
    echo "❌ Error: PostgreSQL container is not running"
    echo "   Start services first: docker-compose up -d"
    exit 1
fi

# Create backup of current database before restore
echo ""
echo "Creating safety backup of current database..."
SAFETY_BACKUP="/opt/Aarya_Clothing/backups/safety_before_restore_$(date +%Y%m%d_%H%M%S).sql"
docker exec aarya_postgres pg_dump -U postgres aarya_clothing > $SAFETY_BACKUP
gzip $SAFETY_BACKUP
echo "✓ Safety backup created: ${SAFETY_BACKUP}.gz"

# Restore database
echo ""
echo "Restoring database from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Compressed backup
    gunzip -c $BACKUP_FILE | docker exec -i aarya_postgres psql -U postgres -d aarya_clothing
else
    # Uncompressed backup
    cat $BACKUP_FILE | docker exec -i aarya_postgres psql -U postgres -d aarya_clothing
fi

echo "✓ Database restored successfully"

# Verify restore
echo ""
echo "Verifying restore..."
USER_COUNT=$(docker exec -it aarya_postgres psql -U postgres -d aarya_clothing -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
echo "✓ Users in database: $USER_COUNT"

echo ""
echo "=========================================="
echo "Restore Complete!"
echo "=========================================="
echo ""
echo "Safety backup: ${SAFETY_BACKUP}.gz"
echo ""
echo "To verify the restore:"
echo "  docker exec -it aarya_postgres psql -U postgres -d aarya_clothing"
echo ""
echo "To restart services:"
echo "  docker-compose restart"
echo ""
