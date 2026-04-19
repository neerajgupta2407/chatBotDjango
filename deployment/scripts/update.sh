#!/bin/bash

# Django Chatbot Update Script
# This script pulls the latest code, updates dependencies, and restarts the service
# Run as: sudo ./update.sh

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables - UPDATE THESE
PROJECT_DIR="/var/www/chatbot"
SERVER_USER="www-data"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Django Chatbot Update Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Change to project directory
cd $PROJECT_DIR

# Step 1: Pull latest code
echo -e "\n${YELLOW}[1/7] Pulling latest code from repository...${NC}"
sudo -u $SERVER_USER git fetch origin
sudo -u $SERVER_USER git pull origin main

# Step 2: Update Python dependencies
echo -e "\n${YELLOW}[2/7] Updating Python dependencies...${NC}"
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/pip install -r requirements.txt --upgrade

# Step 3: Run database migrations
echo -e "\n${YELLOW}[3/7] Running database migrations...${NC}"
export DJANGO_SETTINGS_MODULE=config.settings.production
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/python manage.py migrate

# Step 4: Collect static files
echo -e "\n${YELLOW}[4/7] Collecting static files...${NC}"
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput

# Step 5: Clear any caches (if using cache)
echo -e "\n${YELLOW}[5/7] Clearing Django cache (if enabled)...${NC}"
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/python manage.py clear_cache 2>/dev/null || echo "No cache to clear"

# Step 6: Restart application service
echo -e "\n${YELLOW}[6/7] Restarting application service...${NC}"
systemctl restart chatbot
sleep 2

# Step 7: Verify service is running
echo -e "\n${YELLOW}[7/7] Verifying service status...${NC}"
if systemctl is-active --quiet chatbot; then
    echo -e "${GREEN}✓ Chatbot service is running successfully${NC}"
    systemctl status chatbot --no-pager --lines=5
else
    echo -e "${RED}✗ Chatbot service failed to start${NC}"
    echo "Check logs: journalctl -u chatbot -n 50"
    exit 1
fi

# Restart Nginx (optional, uncomment if needed)
# echo -e "\n${YELLOW}Restarting Nginx...${NC}"
# systemctl restart nginx

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application has been updated successfully."
echo ""
echo "Useful commands:"
echo "  - View logs: journalctl -u chatbot -f"
echo "  - Restart service: sudo systemctl restart chatbot"
echo "  - Check status: sudo systemctl status chatbot"
echo ""
