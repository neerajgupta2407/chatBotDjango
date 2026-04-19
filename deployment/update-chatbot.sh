#!/bin/bash
#
# Django Chatbot - Update Script
# Pulls latest code from GitHub and restarts the application
#
# Usage: ssh root@142.93.222.67 'sudo /usr/local/bin/update-chatbot'
#

set -e  # Exit on error

# Configuration
PROJECT_DIR="/var/www/chatbot"
LOGFILE="/var/log/chatbot-updates.log"
BACKUP_DIR="/var/www/chatbot/backups"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOGFILE
}

error() {
    echo "${RED}[ERROR]${NC} $1" | tee -a $LOGFILE
    exit 1
}

success() {
    echo "${GREEN}[SUCCESS]${NC} $1" | tee -a $LOGFILE
}

info() {
    echo "${YELLOW}[INFO]${NC} $1" | tee -a $LOGFILE
}

# Start update
log "=== Starting application update ==="
info "Project directory: $PROJECT_DIR"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
fi

# Navigate to project directory
cd $PROJECT_DIR || error "Failed to navigate to project directory"

# Check current branch and status
info "Checking Git status..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
log "Current branch: $CURRENT_BRANCH"

# Backup database before update
info "Creating database backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
    mkdir -p $BACKUP_DIR
    cp $PROJECT_DIR/db.sqlite3 $BACKUP_DIR/db_backup_pre_update_$TIMESTAMP.sqlite3
    gzip $BACKUP_DIR/db_backup_pre_update_$TIMESTAMP.sqlite3
    success "Database backed up"
else
    info "No database file found, skipping backup"
fi

# Pull latest code (using root's SSH key which has access)
info "Pulling latest code from GitHub..."
git fetch origin 2>&1 | tee -a $LOGFILE
BEFORE_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
git pull origin $CURRENT_BRANCH 2>&1 | tee -a $LOGFILE || error "Failed to pull latest code"
AFTER_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")

if [ "$BEFORE_COMMIT" = "$AFTER_COMMIT" ]; then
    info "No new changes to deploy"
else
    success "Code updated successfully"
    if [ "$BEFORE_COMMIT" != "unknown" ] && [ "$AFTER_COMMIT" != "unknown" ]; then
        log "Changes:"
        git log --oneline $BEFORE_COMMIT..$AFTER_COMMIT | tee -a $LOGFILE
    fi
fi

# Update Python dependencies
info "Updating Python dependencies..."
sudo -u www-data venv/bin/pip install -r requirements.txt --upgrade --quiet || error "Failed to install dependencies"
success "Dependencies updated"

# Run database migrations
info "Running database migrations..."
sudo -u www-data venv/bin/python manage.py migrate --noinput || error "Failed to run migrations"
success "Migrations completed"

# Collect static files
info "Collecting static files..."
sudo -u www-data venv/bin/python manage.py collectstatic --noinput --clear || error "Failed to collect static files"
success "Static files collected"

# Restart application
info "Restarting application..."
systemctl restart chatbot || error "Failed to restart application"
sleep 3

# Check if service is running
if systemctl is-active --quiet chatbot; then
    success "Application restarted successfully"
else
    error "Application failed to start! Check logs: journalctl -u chatbot -n 50"
fi

# Health check
info "Performing health check..."
sleep 2
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://cb.hexbolttechnologies.in/health 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" = "200" ]; then
    success "Health check passed (HTTP $HEALTH_CHECK)"
else
    echo "${YELLOW}[WARNING]${NC} Health check returned HTTP $HEALTH_CHECK" | tee -a $LOGFILE
fi

# Cleanup old backups (keep last 10)
info "Cleaning up old backups..."
cd $BACKUP_DIR 2>/dev/null || mkdir -p $BACKUP_DIR
ls -t db_backup_*.sqlite3.gz 2>/dev/null | tail -n +11 | xargs -r rm 2>/dev/null || true
success "Old backups cleaned up"

# Final summary
log "=== Update completed successfully ==="
success "Application URL: https://cb.hexbolttechnologies.in"
info "View logs: journalctl -u chatbot -f"
info "Update log: $LOGFILE"

exit 0
