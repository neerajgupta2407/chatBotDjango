# Terraform Deployment for Django Chatbot on DigitalOcean

This directory contains Terraform configuration files to deploy the Django Chatbot application on DigitalOcean infrastructure.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Post-Deployment](#post-deployment)
- [Management](#management)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)
- [Clean Up](#clean-up)

---

## Overview

This Terraform configuration automatically provisions and configures:

- **DigitalOcean Droplet** (Ubuntu 22.04) with configurable size
- **Cloud Firewall** with security rules (SSH, HTTP, HTTPS)
- **Automated Bootstrap** via cloud-init script
- **Complete Django Setup** including Nginx, Gunicorn, systemd
- **SQLite Database** (no external database needed)
- **SSL-Ready** with certbot pre-installed
- **Project Organization** with DigitalOcean Projects

### Infrastructure Components

```
┌─────────────────────────────────────────┐
│     DigitalOcean Cloud Firewall         │
│  (Ports: 22, 80, 443)                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Ubuntu 22.04 Droplet             │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  Nginx (Port 80/443)           │     │
│  └──────────┬─────────────────────┘     │
│             │                            │
│  ┌──────────▼─────────────────────┐     │
│  │  Gunicorn (Port 8000)          │     │
│  │  - Django Application          │     │
│  │  - REST API                    │     │
│  │  - Chatbot Widget              │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  SQLite Database               │     │
│  │  (db.sqlite3)                  │     │
│  └────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Install Terraform

**macOS:**
```bash
brew install terraform
```

**Linux:**
```bash
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Windows:**
Download from [terraform.io/downloads](https://www.terraform.io/downloads)

**Verify installation:**
```bash
terraform version
```

### 2. DigitalOcean Account & API Token

1. Create a DigitalOcean account at [digitalocean.com](https://www.digitalocean.com/)
2. Generate an API token:
   - Go to [API Tokens](https://cloud.digitalocean.com/account/api/tokens)
   - Click **Generate New Token**
   - Name: `terraform-chatbot`
   - Scopes: **Read & Write**
   - Copy the token (you won't see it again!)

### 3. SSH Key Setup

**Option A: Use existing SSH keys** (recommended)
```bash
# Check if you have SSH keys
ls ~/.ssh/id_rsa.pub

# If not, generate a new key pair
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Add your SSH public key to DigitalOcean:
# Go to: https://cloud.digitalocean.com/account/security
# Click "Add SSH Key" and paste contents of:
cat ~/.ssh/id_rsa.pub
```

**Option B: Let Terraform upload your key** (easier)
- Just specify the path in `terraform.tfvars`

### 4. API Keys for AI Providers

Get your API keys:
- **Anthropic (Claude):** [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI (GPT):** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Quick Start

### Step 1: Navigate to Terraform Directory

```bash
cd terraform
```

### Step 2: Configure Variables

```bash
# Copy the example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit the configuration file
nano terraform.tfvars
```

**Required variables to configure:**
```hcl
do_token          = "dop_v1_your_token_here"
anthropic_api_key = "sk-ant-your_key_here"
openai_api_key    = "sk-your_key_here"
```

### Step 3: Initialize Terraform

```bash
terraform init
```

This will:
- Download the DigitalOcean provider plugin
- Initialize the backend
- Prepare the working directory

### Step 4: Preview Changes

```bash
terraform plan
```

Review the infrastructure that will be created.

### Step 5: Deploy

```bash
terraform apply
```

Type `yes` when prompted. Deployment takes **5-10 minutes**.

### Step 6: Get Connection Details

```bash
terraform output
```

You'll see:
- Server IP address
- SSH connection command
- Application URLs
- Next steps

---

## Configuration

### Essential Variables

Edit `terraform.tfvars`:

```hcl
# DigitalOcean API Token (required)
do_token = "dop_v1_abc123..."

# AI Provider Keys (required)
anthropic_api_key = "sk-ant-..."
openai_api_key    = "sk-..."

# Droplet Configuration
droplet_region = "nyc3"        # Closest to your users
droplet_size   = "s-2vcpu-4gb" # Recommended for production

# Domain Configuration (optional)
domain_name = "chatbot.example.com"

# Security
allowed_ssh_ips = ["YOUR.IP.ADDRESS/32"]  # Restrict SSH access
```

### Available Regions

Choose the region closest to your users:

| Region Code | Location | Latency (from US East) |
|-------------|----------|------------------------|
| `nyc1`, `nyc3` | New York | Best for US East |
| `sfo3` | San Francisco | Best for US West |
| `tor1` | Toronto | Best for Canada |
| `lon1` | London | Best for UK/Europe |
| `fra1` | Frankfurt | Best for EU Central |
| `ams3` | Amsterdam | Best for EU West |
| `sgp1` | Singapore | Best for Asia |
| `blr1` | Bangalore | Best for India |

### Droplet Sizes & Pricing

| Size | vCPUs | RAM | Storage | Price/Month |
|------|-------|-----|---------|-------------|
| `s-1vcpu-1gb` | 1 | 1GB | 25GB | $6 |
| `s-2vcpu-2gb` | 2 | 2GB | 50GB | $12 |
| `s-2vcpu-4gb` | 2 | 4GB | 80GB | $24 (recommended) |
| `s-4vcpu-8gb` | 4 | 8GB | 160GB | $48 |

**Recommendation:** Use `s-2vcpu-4gb` for production.

---

## Deployment

### Full Deployment Process

```bash
cd terraform

# 1. Initialize (first time only)
terraform init

# 2. Validate configuration
terraform validate

# 3. Preview changes
terraform plan

# 4. Deploy infrastructure
terraform apply

# 5. Save outputs
terraform output > deployment_info.txt
```

### What Happens During Deployment

1. **Terraform provisions resources** (~1 min)
   - Creates droplet
   - Sets up firewall
   - Uploads SSH keys
   - Assigns to project

2. **Cloud-init runs bootstrap script** (~5-8 min)
   - Updates system packages
   - Installs Python, Nginx, dependencies
   - Clones GitHub repository
   - Creates Python virtual environment
   - Installs Python packages
   - Configures environment variables
   - Runs Django migrations
   - Collects static files
   - Sets up systemd service
   - Configures Nginx
   - Starts services

3. **Services start automatically**
   - Django app runs on port 8000
   - Nginx proxies on port 80
   - Application is live!

### Monitor Bootstrap Progress

```bash
# Get server IP from terraform output
terraform output ipv4_address

# SSH into server
ssh root@<ip-address>

# Watch bootstrap log in real-time
tail -f /var/log/cloud-init-output.log

# Or check custom log
tail -f /var/log/chatbot-bootstrap.log
```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Get server IP
IP=$(terraform output -raw ipv4_address)

# Test health endpoint
curl http://$IP/health

# Expected response: {"status":"healthy"}
```

### 2. Create Django Superuser

```bash
# SSH into server
ssh root@$(terraform output -raw ipv4_address)

# Create superuser
cd /var/www/chatbot
sudo -u www-data venv/bin/python manage.py createsuperuser

# Follow prompts to create admin account
```

### 3. Access Django Admin

```bash
# Get admin URL
echo "Admin URL: $(terraform output -raw admin_url)"

# Open in browser and login with superuser credentials
```

### 4. Configure Domain (Optional)

**If you have a domain:**

1. **Add DNS A Record:**
   ```
   Type: A
   Name: chatbot (or @)
   Value: <server-ip-from-terraform-output>
   TTL: 300
   ```

2. **Wait for DNS propagation** (5-30 minutes)
   ```bash
   # Check DNS propagation
   dig chatbot.example.com +short
   ```

3. **Update terraform.tfvars:**
   ```hcl
   domain_name = "chatbot.example.com"
   ```

4. **Re-apply Terraform:**
   ```bash
   terraform apply
   ```

### 5. Setup SSL Certificate

```bash
# SSH into server
ssh root@$(terraform output -raw ipv4_address)

# Run certbot (replace with your domain)
certbot --nginx -d chatbot.example.com

# Follow prompts:
# - Enter email for renewal notifications
# - Agree to terms
# - Choose redirect (option 2)

# Test SSL renewal
certbot renew --dry-run
```

### 6. Configure CORS (if needed)

Update `terraform.tfvars`:
```hcl
allowed_origins = "https://yourdomain.com,https://www.yourdomain.com"
```

Re-apply:
```bash
terraform apply
```

---

## Management

### Common Operations

**View Infrastructure Status:**
```bash
terraform show
```

**Update Application Code:**
```bash
ssh root@$(terraform output -raw ipv4_address)
/usr/local/bin/update-chatbot
```

**View Application Logs:**
```bash
ssh root@$(terraform output -raw ipv4_address)
journalctl -u chatbot -f
```

**Restart Application:**
```bash
ssh root@$(terraform output -raw ipv4_address)
systemctl restart chatbot
```

**Backup Database:**
```bash
ssh root@$(terraform output -raw ipv4_address)
/usr/local/bin/backup-chatbot
```

**Scale Droplet:**
```bash
# Edit terraform.tfvars
droplet_size = "s-4vcpu-8gb"

# Apply changes (requires restart)
terraform apply
```

### Update Terraform Configuration

```bash
# 1. Make changes to .tf files or terraform.tfvars

# 2. Preview changes
terraform plan

# 3. Apply changes
terraform apply

# Note: Some changes (like droplet size) require recreation
```

### Backup State File

```bash
# Backup Terraform state (important!)
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d)

# Store securely (state contains sensitive data)
```

---

## Troubleshooting

### Bootstrap Script Failed

```bash
# SSH into server
ssh root@$(terraform output -raw ipv4_address)

# Check bootstrap logs
tail -100 /var/log/cloud-init-output.log
tail -100 /var/log/chatbot-bootstrap.log

# Check service status
systemctl status chatbot
systemctl status nginx

# Manually re-run parts of bootstrap
cd /var/www/chatbot
sudo -u www-data venv/bin/python manage.py migrate
sudo systemctl restart chatbot
```

### Service Not Starting

```bash
# Check Gunicorn errors
journalctl -u chatbot -n 50 --no-pager

# Check Nginx errors
tail -f /var/log/nginx/chatbot_error.log

# Test Gunicorn manually
cd /var/www/chatbot
sudo -u www-data venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Can't Connect via SSH

```bash
# Check firewall rules
terraform show | grep allowed_ssh_ips

# If you locked yourself out, update terraform.tfvars:
allowed_ssh_ips = []  # Allow all

# Re-apply
terraform apply
```

### Health Check Fails

```bash
# SSH into server
ssh root@$(terraform output -raw ipv4_address)

# Check if service is running
systemctl status chatbot

# Check if port is listening
netstat -tlnp | grep 8000

# Check environment variables
cat /var/www/chatbot/.env

# Test locally
curl http://localhost:8000/health
```

### Terraform State Issues

```bash
# Refresh state from actual infrastructure
terraform refresh

# If state is corrupted, restore from backup
cp terraform.tfstate.backup.YYYYMMDD terraform.tfstate
```

---

## Cost Estimation

### Monthly Costs (DigitalOcean)

**Basic Setup (Development):**
- Droplet (s-2vcpu-2gb): **$12/month**
- Bandwidth (1TB included): **$0**
- **Total: ~$12/month**

**Recommended Setup (Production):**
- Droplet (s-2vcpu-4gb): **$24/month**
- Automated Backups (20%): **$5/month**
- **Total: ~$29/month**

**High-Traffic Setup:**
- Droplet (s-4vcpu-8gb): **$48/month**
- Automated Backups: **$10/month**
- Load Balancer (if needed): **$12/month**
- **Total: ~$70/month**

**Additional Costs:**
- AI API Usage (Anthropic/OpenAI): Pay per token
- Domain name: ~$12/year
- SSL Certificate: Free (Let's Encrypt)

### Cost Optimization Tips

1. **Start small** - Begin with `s-2vcpu-2gb` and scale up if needed
2. **Use backups wisely** - Enable only for production
3. **Monitor usage** - Check DigitalOcean billing dashboard
4. **Destroy unused environments** - Don't forget dev/staging droplets

---

## Clean Up

### Destroy Infrastructure

**Warning:** This will permanently delete all resources!

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy infrastructure
terraform destroy

# Type 'yes' to confirm

# Remove local files
rm -rf .terraform/
rm terraform.tfstate*
```

### Partial Clean Up

To keep some resources:

```bash
# Remove specific resource
terraform destroy -target=digitalocean_droplet.chatbot

# Re-create later
terraform apply
```

---

## Advanced Topics

### Remote State Backend

For team collaboration, store state remotely:

```hcl
# In main.tf, uncomment backend block:
backend "s3" {
  endpoint                    = "nyc3.digitaloceanspaces.com"
  key                         = "terraform/chatbot.tfstate"
  bucket                      = "your-terraform-state-bucket"
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
}
```

### Multiple Environments

```bash
# Create workspace for staging
terraform workspace new staging

# Switch to staging
terraform workspace select staging

# Deploy staging with different vars
terraform apply -var-file=staging.tfvars
```

### CI/CD Integration

```yaml
# .github/workflows/terraform.yml
name: Deploy with Terraform
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: hashicorp/setup-terraform@v2
      - name: Terraform Init
        run: terraform init
      - name: Terraform Apply
        run: terraform apply -auto-approve
        env:
          TF_VAR_do_token: ${{ secrets.DO_TOKEN }}
```

---

## File Structure

```
terraform/
├── main.tf                    # Provider and backend configuration
├── variables.tf               # Input variable definitions
├── droplet.tf                 # Droplet resource configuration
├── firewall.tf                # Firewall and security rules
├── ssh_keys.tf                # SSH key management
├── outputs.tf                 # Output values
├── user_data.sh               # Bootstrap script (cloud-init)
├── terraform.tfvars.example   # Example configuration
├── terraform.tfvars           # Your configuration (git-ignored)
└── .terraform/                # Terraform plugins (git-ignored)
```

---

## Support & Resources

### Documentation
- **Terraform:** [terraform.io/docs](https://www.terraform.io/docs)
- **DigitalOcean Provider:** [registry.terraform.io/providers/digitalocean/digitalocean](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)
- **DigitalOcean API:** [docs.digitalocean.com/reference/api](https://docs.digitalocean.com/reference/api/)

### Community
- **Project Issues:** [GitHub Issues](https://github.com/neerajgupta2407/chatBotDjango/issues)
- **Terraform Community:** [discuss.hashicorp.com](https://discuss.hashicorp.com/c/terraform-core)
- **DigitalOcean Community:** [digitalocean.com/community](https://www.digitalocean.com/community)

---

## Security Best Practices

1. **Never commit `terraform.tfvars`** - Contains secrets
2. **Restrict SSH access** - Use `allowed_ssh_ips`
3. **Use strong API keys** - Rotate regularly
4. **Enable backups** - For production environments
5. **Setup SSL immediately** - Use Let's Encrypt
6. **Monitor logs** - Check for suspicious activity
7. **Keep packages updated** - Run `apt update && apt upgrade` regularly
8. **Use firewall** - Already configured in Terraform
9. **Backup Terraform state** - Contains sensitive data
10. **Use DigitalOcean Spaces** - For remote state storage

---

## License

See LICENSE file in repository root.

---

## Changelog

### v1.0.0 (2025-10-10)
- Initial Terraform configuration
- DigitalOcean provider setup
- Automated bootstrap with cloud-init
- Nginx and Gunicorn configuration
- SQLite database support
- SSL-ready with certbot
- Comprehensive documentation
