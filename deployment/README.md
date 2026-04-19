# Deployment Configuration Files

This directory contains all the necessary configuration files and scripts for deploying the Django Chatbot application to a production server.

## Directory Structure

```
deployment/
├── README.md                    # This file
├── QUICKSTART.md               # Quick deployment guide
├── nginx/                      # Nginx configuration files
│   ├── chatbot.conf           # Main Nginx server configuration
│   └── chatbot_common.conf    # Common configuration (included by main)
├── systemd/                    # Systemd service files
│   └── chatbot.service        # Service definition for auto-start
└── scripts/                    # Deployment automation scripts
    ├── deploy.sh              # Initial deployment script
    ├── update.sh              # Update and restart script
    └── backup.sh              # Database backup script
```

## Files Overview

### Nginx Configuration

**`nginx/chatbot.conf`**
- Main Nginx server configuration
- HTTP and HTTPS server blocks
- SSL certificate configuration (commented, activate after Let's Encrypt)
- Includes common configuration

**`nginx/chatbot_common.conf`**
- Location blocks for static files, media, API endpoints
- CORS headers configuration
- Proxy settings for Gunicorn
- Security headers

**Installation:**
```bash
sudo cp nginx/chatbot.conf /etc/nginx/sites-available/chatbot
sudo cp nginx/chatbot_common.conf /etc/nginx/sites-available/chatbot_common.conf
sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
```

### Systemd Service

**`systemd/chatbot.service`**
- Systemd service definition for auto-starting the application
- Configures Gunicorn to run as a Unix socket
- Automatic restart on failure
- Security hardening options

**Installation:**
```bash
sudo cp systemd/chatbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatbot
sudo systemctl start chatbot
```

### Deployment Scripts

**`scripts/deploy.sh`**
- Automated initial deployment script
- Installs all system dependencies
- Sets up Python environment
- Creates PostgreSQL database
- Configures Nginx and systemd
- Run with: `sudo bash scripts/deploy.sh`

**`scripts/update.sh`**
- Updates the application with latest code from Git
- Installs/updates Python dependencies
- Runs database migrations
- Collects static files
- Restarts the service
- Run with: `sudo bash scripts/update.sh`

**`scripts/backup.sh`**
- Creates database backups with timestamp
- Compresses backups to save space
- Backs up media files
- Cleans up old backups (retention: 30 days)
- Run with: `sudo bash scripts/backup.sh`
- For automatic backups: `0 2 * * * /var/www/chatbot/deployment/scripts/backup.sh`

## Configuration Files in Project Root

**`gunicorn_config.py`**
- Gunicorn WSGI server configuration
- Worker processes, timeouts, logging
- Located in project root: `/var/www/chatbot/gunicorn_config.py`

**`.env.production`**
- Production environment variables template
- Copy to `.env` and customize
- Contains database URL, API keys, security settings

## Quick Start

For first-time deployment:
1. Read `QUICKSTART.md` for step-by-step instructions
2. Edit variables in `scripts/deploy.sh`
3. Run: `sudo bash scripts/deploy.sh`
4. Configure `.env` file
5. Restart service: `sudo systemctl restart chatbot`

## Documentation

- **QUICKSTART.md** - 5-minute deployment guide
- **../DEPLOYMENT.md** - Complete deployment documentation
- **../CLAUDE.md** - Project architecture and development guide
- **../README.md** - Project overview

## Support

For issues or questions:
- GitHub Issues: https://github.com/neerajgupta2407/chatBotDjango/issues
- See troubleshooting section in DEPLOYMENT.md
