# HabitStack Deployment Guide

Complete guide for deploying HabitStack on a Linux server with Nginx + Gunicorn.

## 🚀 Quick Setup Overview

1. **Application**: Flask app running on Gunicorn
2. **Web Server**: Nginx reverse proxy
3. **Database**: SQLite (auto-created)
4. **Process Manager**: systemd service
5. **Port**: Gunicorn on 8000, Nginx on 80/443

---

## 📋 Prerequisites

- Linux server (Ubuntu/Debian recommended)
- Python 3.8+ installed
- Nginx already running
- Domain/subdomain pointing to your server
- sudo/root access

---

## 📦 1. Server Setup

### Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install python3 python3-pip python3-venv git -y

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Create Application User
```bash
# Create dedicated user for the app
sudo useradd --system --shell /bin/bash --home /opt/habitstack habitstack
sudo mkdir -p /opt/habitstack
sudo chown habitstack:habitstack /opt/habitstack
```

---

## 📁 2. Application Deployment

### Clone and Setup Application
```bash
# Switch to app user
sudo -u habitstack -i

# Navigate to home directory
cd /opt/habitstack

# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/habitstack.git .

# Install dependencies
uv sync

# Create production environment file
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF

# Set permissions
chmod 600 .env
```

### Test Application
```bash
# Test the application works
uv run python app.py

# Should see: Running on http://127.0.0.1:8000
# Press Ctrl+C to stop
```

---

## 🔧 3. Gunicorn Configuration

### Install Gunicorn
```bash
# Add gunicorn to dependencies
uv add gunicorn
```

### Create Gunicorn Configuration
```bash
# Create gunicorn config file
cat > /opt/habitstack/gunicorn.conf.py << 'EOF'
# Gunicorn configuration for HabitStack

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many requests (prevents memory leaks)
preload_app = True

# Logging
accesslog = "/opt/habitstack/logs/access.log"
errorlog = "/opt/habitstack/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "habitstack"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
worker_tmp_dir = "/dev/shm"
tmp_upload_dir = None
EOF

# Create logs directory
mkdir -p /opt/habitstack/logs
```

### Create WSGI Entry Point
```bash
# Create wsgi.py file
cat > /opt/habitstack/wsgi.py << 'EOF'
#!/usr/bin/env python3
"""
WSGI entry point for HabitStack production deployment
"""

import os
import sys

# Add the application directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
from app import app

# Initialize database on startup
from app import init_db
init_db()

if __name__ == "__main__":
    app.run()
EOF

chmod +x /opt/habitstack/wsgi.py
```

---

## ⚙️ 4. Systemd Service Configuration

### Create Service File
```bash
# Exit from habitstack user
exit

# Create systemd service file
sudo tee /etc/systemd/system/habitstack.service > /dev/null << 'EOF'
[Unit]
Description=HabitStack Flask Application
After=network.target

[Service]
Type=notify
User=habitstack
Group=habitstack
WorkingDirectory=/opt/habitstack
Environment=PATH=/opt/habitstack/.venv/bin
ExecStart=/opt/habitstack/.venv/bin/gunicorn --config /opt/habitstack/gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/habitstack
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start Service
```bash
# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable habitstack.service
sudo systemctl start habitstack.service

# Check service status
sudo systemctl status habitstack.service

# View logs
sudo journalctl -u habitstack.service -f
```

---

## 🌐 5. Nginx Configuration

### Create Nginx Site Configuration
```bash
# Create nginx site configuration
sudo tee /etc/nginx/sites-available/habitstack << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Logs
    access_log /var/log/nginx/habitstack_access.log;
    error_log /var/log/nginx/habitstack_error.log;
    
    # Handle requests containing 'habitstack'
    location /habitstack {
        # Remove trailing slash if present
        rewrite ^/habitstack/(.*)$ /habitstack/$1;
        
        # Proxy to Gunicorn
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Handle root redirect to habitstack
    location = / {
        return 301 /habitstack/;
    }
    
    # Static files (if you add them later)
    location /habitstack/static {
        alias /opt/habitstack/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|db)$ {
        deny all;
    }
}
EOF
```

### Enable Site and Restart Nginx
```bash
# Enable the site
sudo ln -sf /etc/nginx/sites-available/habitstack /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

---

## 🔒 6. SSL Configuration (Optional but Recommended)

### Install Certbot
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace your-domain.com)
sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## 📊 7. Monitoring and Maintenance

### Log Management
```bash
# View application logs
sudo tail -f /opt/habitstack/logs/access.log
sudo tail -f /opt/habitstack/logs/error.log

# View systemd logs
sudo journalctl -u habitstack.service -f

# View nginx logs
sudo tail -f /var/log/nginx/habitstack_access.log
sudo tail -f /var/log/nginx/habitstack_error.log
```

### Service Management Commands
```bash
# Restart application
sudo systemctl restart habitstack.service

# Reload application (graceful restart)
sudo systemctl reload habitstack.service

# Check status
sudo systemctl status habitstack.service

# View resource usage
sudo systemctl show habitstack.service --property=MemoryCurrent,CPUUsageNSec
```

### Database Backup
```bash
# Create backup script
sudo tee /opt/habitstack/backup.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/habitstack/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
cp /opt/habitstack/habitstack.db "$BACKUP_DIR/habitstack_$DATE.db"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "habitstack_*.db" -mtime +7 -delete
EOF

sudo chmod +x /opt/habitstack/backup.sh
sudo chown habitstack:habitstack /opt/habitstack/backup.sh

# Add to crontab (daily backup at 2 AM)
echo "0 2 * * * /opt/habitstack/backup.sh" | sudo crontab -u habitstack -
```

---

## 🔧 8. Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
sudo journalctl -u habitstack.service -n 50
sudo systemctl status habitstack.service

# Check permissions
sudo ls -la /opt/habitstack/
sudo -u habitstack test -r /opt/habitstack/wsgi.py
```

**Nginx 502 Bad Gateway:**
```bash
# Check if gunicorn is running
sudo netstat -tlnp | grep :8000
sudo systemctl status habitstack.service

# Check nginx error logs
sudo tail -f /var/log/nginx/habitstack_error.log
```

**Application errors:**
```bash
# Check application logs
sudo tail -f /opt/habitstack/logs/error.log

# Test application manually
sudo -u habitstack -i
cd /opt/habitstack
uv run gunicorn --bind 127.0.0.1:8000 wsgi:app
```

### Performance Tuning

**Increase workers for higher traffic:**
```bash
# Edit gunicorn config
sudo nano /opt/habitstack/gunicorn.conf.py

# Change workers based on: (2 x CPU cores) + 1
# For 2 CPU cores: workers = 5
# For 4 CPU cores: workers = 9

# Restart service
sudo systemctl restart habitstack.service
```

---

## ✅ 9. Deployment Checklist

- [ ] Server dependencies installed
- [ ] Application user created
- [ ] Code deployed and tested
- [ ] Environment variables configured
- [ ] Gunicorn service running
- [ ] Nginx configuration active
- [ ] SSL certificate installed (optional)
- [ ] Firewall configured (ports 80, 443)
- [ ] Backup script scheduled
- [ ] Monitoring logs working

---

## 🌍 10. Access Your Application

Once everything is configured:

- **HTTP**: `http://your-domain.com/habitstack/`
- **HTTPS**: `https://your-domain.com/habitstack/`
- **Health Check**: `http://your-domain.com/health`

The application will be accessible at any URL containing `/habitstack` and will automatically redirect the root domain to `/habitstack/`.

---

## 📝 Notes

- Replace `your-domain.com` with your actual domain
- The application runs on port 8000 internally
- SQLite database is automatically created on first run
- All routes are prefixed with `/habitstack/` as configured
- Static files are served by Nginx for better performance
- The setup includes security headers and basic hardening

For any issues, check the logs and ensure all services are running properly!