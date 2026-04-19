#!/bin/bash

# Django Chatbot Database Backup Script
# This script creates a backup of the PostgreSQL database
# Run as: sudo ./backup.sh
# For automated backups, add to crontab:
# 0 2 * * * /var/www/chatbot/deployment/scripts/backup.sh

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables - UPDATE THESE
PROJECT_DIR="/var/www/chatbot"
BACKUP_DIR="$PROJECT_DIR/backups"
DB_NAME="chatbot_db"
DB_USER="chatbot_user"
RETENTION_DAYS=30  # Keep backups for 30 days

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Backup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "\n${YELLOW}Creating backup directory...${NC}"
    mkdir -p $BACKUP_DIR
    chown www-data:www-data $BACKUP_DIR
fi

# Step 1: Create database backup
echo -e "\n${YELLOW}[1/4] Creating database backup...${NC}"
sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}✓ Database backup created: $BACKUP_FILE${NC}"
    BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
    echo "  Size: $BACKUP_SIZE"
else
    echo -e "${RED}✗ Failed to create database backup${NC}"
    exit 1
fi

# Step 2: Compress backup
echo -e "\n${YELLOW}[2/4] Compressing backup...${NC}"
gzip $BACKUP_FILE

if [ -f "$BACKUP_FILE_GZ" ]; then
    echo -e "${GREEN}✓ Backup compressed: $BACKUP_FILE_GZ${NC}"
    COMPRESSED_SIZE=$(du -h $BACKUP_FILE_GZ | cut -f1)
    echo "  Compressed size: $COMPRESSED_SIZE"
else
    echo -e "${RED}✗ Failed to compress backup${NC}"
    exit 1
fi

# Step 3: Backup media files (optional)
echo -e "\n${YELLOW}[3/4] Backing up media files...${NC}"
if [ -d "$PROJECT_DIR/media" ]; then
    MEDIA_BACKUP="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
    tar -czf $MEDIA_BACKUP -C $PROJECT_DIR media/
    echo -e "${GREEN}✓ Media files backed up: $MEDIA_BACKUP${NC}"
else
    echo "No media directory found, skipping..."
fi

# Step 4: Clean up old backups
echo -e "\n${YELLOW}[4/4] Cleaning up old backups (older than $RETENTION_DAYS days)...${NC}"
OLD_BACKUPS=$(find $BACKUP_DIR -name "*.gz" -type f -mtime +$RETENTION_DAYS)

if [ -z "$OLD_BACKUPS" ]; then
    echo "No old backups to delete"
else
    echo "Deleting old backups:"
    find $BACKUP_DIR -name "*.gz" -type f -mtime +$RETENTION_DAYS -print -delete
    echo -e "${GREEN}✓ Old backups cleaned up${NC}"
fi

# Display backup summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Backup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup location: $BACKUP_FILE_GZ"
echo ""
echo "To restore this backup:"
echo "  gunzip $BACKUP_FILE_GZ"
echo "  sudo -u postgres psql $DB_NAME < $BACKUP_FILE"
echo ""
echo "Current backups in $BACKUP_DIR:"
ls -lh $BACKUP_DIR/*.gz 2>/dev/null | tail -5 || echo "No backups found"
echo ""
echo "Total backup size:"
du -sh $BACKUP_DIR
