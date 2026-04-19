# Quick Start Deployment Guide

Fast track deployment for Django Chatbot on your server with login credentials: `ssh chatbot`

## 🚀 5-Minute Deployment

### 1. Connect to Server
```bash
ssh chatbot
```

### 2. Clone Repository
```bash
cd /tmp
git clone https://github.com/neerajgupta2407/chatBotDjango.git
cd chatBotDjango
```

### 3. Edit Configuration
```bash
# Edit these values in the deployment script
nano deployment/scripts/deploy.sh
```

**Update these variables:**
```bash
PROJECT_DIR="/var/www/chatbot"           # Where to install
DB_PASSWORD="your_secure_password"       # Database password (change this!)
DOMAIN="your-domain.com"                 # Your domain name
SERVER_USER="www-data"                   # System user (usually www-data)
```

### 4. Run Deployment Script
```bash
sudo bash deployment/scripts/deploy.sh
```

The script will:
- ✓ Install all dependencies (Python, PostgreSQL, Nginx)
- ✓ Clone the repository to `/var/www/chatbot`
- ✓ Set up Python virtual environment
- ✓ Create PostgreSQL database and user
- ✓ Configure systemd service for auto-start
- ✓ Set up Nginx reverse proxy

### 5. Configure Environment Variables
```bash
# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Edit .env file
sudo nano /var/www/chatbot/.env
```

**Essential variables to update:**
```env
SECRET_KEY=<paste-generated-key-here>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,server-ip
ALLOWED_ORIGINS=https://your-domain.com
DATABASE_URL=postgresql://chatbot_user:your_secure_password@localhost:5432/chatbot_db
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. Restart Service
```bash
sudo systemctl restart chatbot
```

### 7. Create Admin User
```bash
cd /var/www/chatbot
sudo -u www-data venv/bin/python manage.py createsuperuser
```

### 8. Verify Deployment
```bash
# Check service status
sudo systemctl status chatbot

# Test health endpoint
curl http://localhost/health

# View logs
sudo journalctl -u chatbot -f
```

## 🎉 Done!

Your chatbot is now running at:
- **Application**: `http://your-domain.com`
- **Admin Panel**: `http://your-domain.com/admin`
- **API**: `http://your-domain.com/api/`
- **Health Check**: `http://your-domain.com/health`

---

## 🔧 Common Next Steps

### Setup SSL (HTTPS)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Setup Automatic Backups (Daily at 2 AM)
```bash
sudo crontab -e
# Add this line:
0 2 * * * /var/www/chatbot/deployment/scripts/backup.sh
```

### Update Application
```bash
sudo bash /var/www/chatbot/deployment/scripts/update.sh
```

### View Logs
```bash
# Application logs
sudo journalctl -u chatbot -f

# Nginx logs
sudo tail -f /var/log/nginx/chatbot_access.log
sudo tail -f /var/log/nginx/chatbot_error.log
```

---

## 🆘 Troubleshooting

### Service won't start?
```bash
# Check logs for errors
sudo journalctl -u chatbot -xe

# Verify .env is configured
cat /var/www/chatbot/.env

# Check database connection
sudo -u postgres psql -c "SELECT 1;"
```

### Nginx 502 error?
```bash
# Ensure chatbot service is running
sudo systemctl status chatbot

# Check socket file exists
ls -la /var/run/gunicorn/chatbot.sock

# Restart both services
sudo systemctl restart chatbot
sudo systemctl restart nginx
```

### Can't connect to database?
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
sudo -u postgres psql -l | grep chatbot
```

---

## 📚 Full Documentation

For detailed instructions, see:
- **DEPLOYMENT.md** - Complete deployment guide
- **CLAUDE.md** - Project architecture and development
- **README.md** - Project overview

## 📞 Support

Issues? Visit: https://github.com/neerajgupta2407/chatBotDjango/issues
