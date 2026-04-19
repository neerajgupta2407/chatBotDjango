#!/bin/bash

# Django Chatbot Deployment Script
# This script automates the initial deployment of the Django chatbot application
# Run as: ./deploy.sh

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration variables - UPDATE THESE
PROJECT_DIR="/var/www/chatbot"
PROJECT_NAME="chatBotDjango"
GIT_REPO="git@github.com:neerajgupta2407/chatBotDjango.git"
PYTHON_VERSION="python3.10"
DB_NAME="chatbot_db"
DB_USER="chatbot_user"
DB_PASSWORD="${CHATBOT_DB_PASSWORD:-flKNVB5uxehxdtZZmCagxAkRTAMArmQ}"
DOMAIN="cb.hexbolttechnologies.in"  # CHANGE THIS
SERVER_USER="www-data"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Django Chatbot Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Update system packages
echo -e "\n${YELLOW}[1/12] Updating system packages...${NC}"
apt update && apt upgrade -y

# Step 2: Install dependencies
echo -e "\n${YELLOW}[2/12] Installing system dependencies...${NC}"
apt install -y python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib \
    nginx \
    git \
    build-essential \
    libpq-dev \
    curl

# Step 3: Create project directory
echo -e "\n${YELLOW}[3/12] Creating project directory...${NC}"
mkdir -p $PROJECT_DIR
mkdir -p /var/log/gunicorn
mkdir -p /var/run/gunicorn
chown -R $SERVER_USER:$SERVER_USER $PROJECT_DIR
chown -R $SERVER_USER:$SERVER_USER /var/log/gunicorn
chown -R $SERVER_USER:$SERVER_USER /var/run/gunicorn

# Step 4: Clone repository
echo -e "\n${YELLOW}[4/12] Cloning repository...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd $PROJECT_DIR
    sudo -u $SERVER_USER git pull
else
    sudo -u $SERVER_USER git clone $GIT_REPO $PROJECT_DIR
    cd $PROJECT_DIR
fi

# Step 5: Create virtual environment
echo -e "\n${YELLOW}[5/12] Creating Python virtual environment...${NC}"
sudo -u $SERVER_USER $PYTHON_VERSION -m venv venv

# Step 6: Install Python dependencies
echo -e "\n${YELLOW}[6/12] Installing Python dependencies...${NC}"
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/pip install -r requirements.txt
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/pip install gunicorn psycopg2-binary

# Step 7: Setup PostgreSQL database
echo -e "\n${YELLOW}[7/12] Setting up PostgreSQL database...${NC}"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Step 8: Create .env file
echo -e "\n${YELLOW}[8/12] Creating .env file...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Copying .env.production to .env..."
    sudo -u $SERVER_USER cp $PROJECT_DIR/.env.production $PROJECT_DIR/.env
    echo -e "${RED}IMPORTANT: Edit $PROJECT_DIR/.env with your actual values!${NC}"
else
    echo ".env file already exists, skipping..."
fi

# Step 9: Run Django migrations and collect static files
echo -e "\n${YELLOW}[9/12] Running Django migrations and collecting static files...${NC}"
cd $PROJECT_DIR
export DJANGO_SETTINGS_MODULE=config.settings.production
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/python manage.py migrate
sudo -u $SERVER_USER $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput

# Step 10: Setup systemd service
echo -e "\n${YELLOW}[10/12] Setting up systemd service...${NC}"
cp $PROJECT_DIR/deployment/systemd/chatbot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable chatbot
systemctl restart chatbot
sleep 2
systemctl status chatbot --no-pager

# Step 11: Setup Nginx
echo -e "\n${YELLOW}[11/12] Setting up Nginx...${NC}"
cp $PROJECT_DIR/deployment/nginx/chatbot.conf /etc/nginx/sites-available/chatbot
cp $PROJECT_DIR/deployment/nginx/chatbot_common.conf /etc/nginx/sites-available/chatbot_common.conf

# Update Nginx config with actual domain
sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/sites-available/chatbot

# Enable site
ln -sf /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# Step 12: Final checks
echo -e "\n${YELLOW}[12/12] Running final checks...${NC}"
echo "Checking if Gunicorn is running..."
if systemctl is-active --quiet chatbot; then
    echo -e "${GREEN}✓ Chatbot service is running${NC}"
else
    echo -e "${RED}✗ Chatbot service is not running${NC}"
fi

echo "Checking if Nginx is running..."
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx is not running${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit $PROJECT_DIR/.env with your actual configuration"
echo "2. Update SECRET_KEY, DATABASE_URL, API keys, etc."
echo "3. Restart the service: sudo systemctl restart chatbot"
echo "4. Create Django superuser: cd $PROJECT_DIR && sudo -u $SERVER_USER venv/bin/python manage.py createsuperuser"
echo "5. Configure DNS to point to this server"
echo "6. Optional: Setup SSL with Let's Encrypt"
echo ""
echo "Logs:"
echo "  - Application: journalctl -u chatbot -f"
echo "  - Nginx access: tail -f /var/log/nginx/chatbot_access.log"
echo "  - Nginx error: tail -f /var/log/nginx/chatbot_error.log"
echo ""
echo "Health check: http://$DOMAIN/health"
echo "Admin panel: http://$DOMAIN/admin"
