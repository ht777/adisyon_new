# Restaurant Ordering System - Production Deployment Guide

## 🚀 Quick Deployment

### 1. System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), Windows Server 2019+, macOS
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 10GB+ available disk space
- **Network**: Stable internet connection for Docker images

### 2. Prerequisites Installation

#### Install Docker and Docker Compose

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
```

**CentOS/RHEL:**
```bash
# Install Docker
sudo yum install -y docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows:**
1. Download Docker Desktop from https://docker.com
2. Install and restart computer
3. Verify installation: `docker --version`

### 3. SSL Certificate Setup

#### Generate Self-Signed Certificates (Development)
```bash
# Linux/Mac
chmod +x generate-ssl.sh
./generate-ssl.sh

# Windows
./generate-ssl.bat
```

#### Production SSL Certificates
1. Purchase SSL certificate from trusted provider (Let's Encrypt, DigiCert, etc.)
2. Place certificate files in `ssl/` directory:
   - `ssl/cert.pem` - Your domain certificate
   - `ssl/key.pem` - Your private key
   - `ssl/chain.pem` - Certificate chain (optional)

### 4. Environment Configuration

#### Create Environment File
```bash
cp .env.example .env
```

#### Essential Configuration
Edit `.env` file with your settings:

```bash
# Database Configuration
DATABASE_URL=postgresql://restaurant_user:strong_password@db:5432/restaurant_db

# Security (CHANGE THESE!)
SECRET_KEY=your-super-secret-key-minimum-32-characters

# Application Settings
APP_NAME="Your Restaurant Name"
ENVIRONMENT=production
DEBUG=false

# Domain Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@your-domain.com
```

### 5. Docker Deployment

#### Initial Deployment
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Service Health Check
```bash
# Check API health
curl -f https://localhost/health

# Check database connection
docker-compose exec backend python -c "from models import get_session; db = next(get_session()); print('Database connected')"
```

### 6. Database Initialization

#### Run Database Setup
```bash
# Initialize database with sample data
docker-compose exec backend python init_db.py
```

#### Verify Default Admin
- Username: `admin`
- Password: `admin123`
- **IMPORTANT**: Change password immediately!

### 7. Nginx Configuration

#### Domain Setup
Edit `nginx.conf` and replace `localhost` with your domain:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of configuration
}
```

#### Restart Nginx
```bash
docker-compose restart nginx
```

### 8. Firewall Configuration

#### Ubuntu/Debian (UFW)
```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

#### CentOS/RHEL (firewalld)
```bash
# Add HTTP/HTTPS services
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload firewall
sudo firewall-cmd --reload
```

### 9. Backup Configuration

#### Automated Backups
Create backup script `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/restaurant"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U restaurant_user restaurant_db > $BACKUP_DIR/db_backup_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz frontend/static/uploads/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

#### Schedule Backups
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh >> /var/log/restaurant_backup.log 2>&1
```

### 10. Monitoring Setup

#### System Monitoring
Install monitoring tools:

```bash
# Install monitoring tools
sudo apt-get install htop iotop nethogs

# Install log monitoring
sudo apt-get install logwatch
```

#### Application Monitoring
Monitor application health:

```bash
# Create monitoring script
#!/bin/bash
# health_check.sh

HEALTH_URL="https://your-domain.com/health"
EMAIL="admin@your-domain.com"

if ! curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "Restaurant system is down" | mail -s "ALERT: System Down" $EMAIL
fi
```

### 11. Security Hardening

#### System Security
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install fail2ban
sudo apt-get install fail2ban

# Configure fail2ban for nginx
sudo tee /etc/fail2ban/jail.local << EOF
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600
EOF

# Restart fail2ban
sudo systemctl restart fail2ban
```

#### Docker Security
```bash
# Run containers as non-root user
# Update docker-compose.yml to use specific user IDs

# Limit container resources
# Add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
```

### 12. Performance Optimization

#### Database Optimization
```bash
# PostgreSQL optimization
docker-compose exec db psql -U restaurant_user -d restaurant_db -c "
-- Optimize for restaurant workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
"
```

#### Nginx Optimization
```nginx
# Add to nginx.conf
worker_processes auto;
worker_connections 1024;

http {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Cache static files
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 13. Maintenance Commands

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f nginx
docker-compose logs -f db
```

#### Update System
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

#### Database Maintenance
```bash
# Connect to database
docker-compose exec db psql -U restaurant_user -d restaurant_db

# Check database size
SELECT pg_size_pretty(pg_database_size('restaurant_db'));

# Vacuum and analyze
VACUUM FULL ANALYZE;
```

### 14. Troubleshooting

#### Common Issues

**1. Port Already in Use**
```bash
# Find process using port 80
sudo lsof -i :80

# Kill process or change port in docker-compose.yml
```

**2. Database Connection Failed**
```bash
# Check database container
docker-compose logs db

# Restart database
docker-compose restart db

# Check connection string in .env
```

**3. SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Regenerate certificates
./generate-ssl.sh
```

**4. Permission Denied**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x *.sh
```

### 15. Rollback Procedure

#### Quick Rollback
```bash
# Stop all services
docker-compose down

# Restore from backup (if available)
docker-compose exec -T db psql -U restaurant_user restaurant_db < backup.sql

# Restart services
docker-compose up -d
```

#### Complete Rollback
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove images
docker image rm restaurant-ordering-system_backend
docker image rm postgres:15-alpine
docker image rm nginx:alpine

# Start fresh deployment
docker-compose up -d
```

### 16. Support and Maintenance

#### Regular Maintenance Tasks
- [ ] Daily: Check system health endpoint
- [ ] Weekly: Review logs and performance
- [ ] Monthly: Update system packages
- [ ] Monthly: Verify backup integrity
- [ ] Quarterly: Review security settings

#### Emergency Contacts
- System Administrator: admin@your-domain.com
- Technical Support: support@your-domain.com
- Emergency Phone: +1-XXX-XXX-XXXX

---

**🎉 Congratulations! Your Restaurant Ordering System is now deployed and ready for production use!**

For additional support, refer to the README.md file or create an issue in the repository.