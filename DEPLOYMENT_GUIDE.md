# DNS By Eye + Tools Portal Deployment Guide

This guide provides step-by-step instructions for deploying the integrated DNS By Eye and Tools Portal system.

## Quick Start (Production Deployment)

### Prerequisites
- Linux server with Docker and Docker Compose installed
- Domain name with DNS pointing to your server
- Ports 80 and 443 available
- Root or sudo access

### 1. Clone and Setup

```bash
# Clone the Tools Portal with DNS By Eye submodule
git clone --recursive https://github.com/apathy-ca/tools-portal.git
cd tools-portal

# Verify submodule was cloned
ls -la tools/dns-by-eye/
```

### 2. Deploy with SSL

```bash
# Clear any cached Docker builds (important for first deployment)
sudo docker system prune -a -f
sudo docker builder prune -a -f
sudo docker buildx prune -a -f 2>/dev/null || true

# Set up SSL certificates (replace with your domain and email)
./scripts/setup-ssl.sh your-domain.com admin@your-domain.com

# The script will automatically:
# - Clear Docker build cache
# - Update nginx-tools-ssl.conf with your domain
# - Generate SSL certificates
# - Deploy all services

# Check status
sudo docker compose -f docker compose-tools-ssl.yaml ps
```

### 4. Verify Deployment

```bash
# Check all services are running
sudo docker compose -f docker compose-tools-ssl.yaml ps

# Check logs if needed
sudo docker compose -f docker compose-tools-ssl.yaml logs

# Test endpoints
curl -I https://your-domain.com/
curl -I https://your-domain.com/dns-by-eye/
curl https://your-domain.com/api/health
curl https://your-domain.com/dns-by-eye/api/health
```

### 5. Access Your Deployment

- **Main Portal**: `https://your-domain.com/`
- **DNS By Eye**: `https://your-domain.com/dns-by-eye/`
- **Tools Portal API**: `https://your-domain.com/api/`
- **DNS By Eye API**: `https://your-domain.com/dns-by-eye/api/`

## Development Deployment (No SSL)

For local development or testing:

```bash
# Clone repository
git clone --recursive https://github.com/apathy-ca/tools-portal.git
cd tools-portal

# Deploy without SSL
sudo docker compose -f docker compose-tools.yaml up -d

# Access at:
# - Main Portal: http://localhost/
# - DNS By Eye: http://localhost/dns-by-eye/
```

## Architecture Overview

```
Internet
    │
    ▼
┌─────────────────┐
│   nginx         │  ← SSL termination, routing
│   (Port 443/80) │
└─────────────────┘
    │
    ├─── / ──────────────────┐
    │                        ▼
    │                ┌──────────────┐
    │                │ Tools Portal │  ← Landing page, tool registry
    │                │   (Flask)    │
    │                └──────────────┘
    │
    └─── /dns-by-eye/ ──────┐
                            ▼
                    ┌─────────────────┐
                    │   DNS By Eye    │  ← DNS analysis tool
                    │    (Flask)      │
                    └─────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Redis     │  ← Shared caching & rate limiting
                    │              │
                    └──────────────┘
```

## Service Details

### Tools Portal (Main Application)
- **Container**: `tools-portal`
- **Port**: 5000 (internal)
- **Purpose**: Landing page, tool registry, main navigation
- **Health Check**: `GET /health`

### DNS By Eye (Analysis Tool)
- **Container**: `dns-by-eye`
- **Port**: 5000 (internal)
- **Purpose**: DNS delegation analysis and visualization
- **Health Check**: `GET /api/health`

### Nginx (Reverse Proxy)
- **Container**: `tools-nginx`
- **Ports**: 80, 443 (external)
- **Purpose**: SSL termination, request routing, security headers
- **Features**: Rate limiting, gzip compression, security headers

### Redis (Caching)
- **Container**: `tools-redis`
- **Port**: 6379 (internal)
- **Purpose**: Shared caching and rate limiting storage
- **Persistence**: Data persisted to volume

### Certbot (SSL Management)
- **Container**: `tools-certbot`
- **Purpose**: Automatic SSL certificate renewal
- **Schedule**: Checks every 12 hours

### Cleanup Service
- **Container**: `tools-cleanup`
- **Purpose**: Removes old generated graph files
- **Schedule**: Runs daily, removes files older than 1 day

## Management Commands

### View Logs
```bash
# All services
sudo docker compose -f docker compose-tools-ssl.yaml logs

# Specific service
sudo docker compose -f docker compose-tools-ssl.yaml logs tools-portal
sudo docker compose -f docker compose-tools-ssl.yaml logs dns-by-eye
sudo docker compose -f docker compose-tools-ssl.yaml logs nginx

# Check nginx and certbot status (common restart issues)
sudo docker compose -f docker compose-tools-ssl.yaml logs nginx
sudo docker compose -f docker compose-tools-ssl.yaml logs certbot

# If nginx is restarting, check SSL certificate paths
sudo docker compose -f docker compose-tools-ssl.yaml exec nginx ls -la /etc/letsencrypt/live/
```

### Restart Services
```bash
# All services
sudo docker compose -f docker compose-tools-ssl.yaml restart

# Specific service
sudo docker compose -f docker compose-tools-ssl.yaml restart dns-by-eye
```

### Update Deployment
```bash
# Pull latest changes
git pull origin main
git submodule update --remote

# Rebuild and restart
sudo docker compose -f docker compose-tools-ssl.yaml up -d --build
```

### SSL Certificate Management
```bash
# Check certificate status
sudo docker compose -f docker compose-tools-ssl.yaml exec certbot certbot certificates

# Manual renewal (automatic renewal runs every 12 hours)
sudo docker compose -f docker compose-tools-ssl.yaml exec certbot certbot renew
```

### Backup Important Data
```bash
# SSL certificates
sudo cp -r /var/lib/docker/volumes/tools-portal_certbot_conf/_data /backup/ssl-certs/

# Configuration files
cp docker compose-tools-ssl.yaml nginx-tools-ssl.conf /backup/config/

# Redis data (if needed)
sudo cp -r /var/lib/docker/volumes/tools-portal_redis_data/_data /backup/redis/
```

## Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check logs
   sudo docker compose -f docker compose-tools-ssl.yaml logs
   
   # Check if ports are available
   sudo netstat -tlnp | grep -E ':80|:443'
   ```

2. **SSL certificate issues**
   ```bash
   # Run troubleshooting script
   ./scripts/troubleshoot.sh your-domain.com
   
   # Check certificate status
   sudo docker compose -f docker compose-tools-ssl.yaml exec certbot certbot certificates
   ```

3. **DNS By Eye not accessible**
   ```bash
   # Check if submodule is properly initialized
   ls -la tools/dns-by-eye/
   
   # If empty, initialize submodules
   git submodule update --init --recursive
   ```

4. **Redis connection issues**
   ```bash
   # Check Redis status
   sudo docker compose -f docker compose-tools-ssl.yaml exec redis redis-cli ping
   
   # Check Redis logs
   sudo docker compose -f docker compose-tools-ssl.yaml logs redis
   ```

### Health Checks

```bash
# Tools Portal health
curl https://your-domain.com/health

# DNS By Eye health
curl https://your-domain.com/dns-by-eye/api/health

# Test DNS analysis
curl -X POST "https://your-domain.com/dns-by-eye/api/delegation" \
     -H "Content-Type: application/json" \
     -d '{"domain": "google.com", "verbose": false}'
```

## Security Considerations

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Regular Maintenance
- SSL certificates auto-renew every 12 hours
- Generated files auto-cleanup daily
- Monitor logs for unusual activity
- Keep Docker images updated

### Rate Limiting
- API endpoints: 10 requests/second
- General endpoints: 30 requests/second
- Configured in nginx and application layers

## Performance Optimization

### Resource Requirements
- **Minimum**: 1 CPU, 1GB RAM, 10GB disk
- **Recommended**: 2 CPU, 2GB RAM, 20GB disk
- **High Traffic**: 4 CPU, 4GB RAM, 50GB disk

### Monitoring
```bash
# Resource usage
sudo docker stats

# Disk usage
df -h
sudo docker system df

# Clean up unused resources
sudo docker system prune -f
```

## Adding New Tools

To add additional tools to the platform:

1. **Add as submodule**:
   ```bash
   git submodule add https://github.com/your-org/your-tool.git tools/your-tool
   ```

2. **Update docker compose.yaml**:
   ```yaml
   your-tool:
     build: ./tools/your-tool
     container_name: your-tool
     restart: unless-stopped
     networks:
       - tools-network
     depends_on:
       - redis
   ```

3. **Update nginx configuration**:
   ```nginx
   location /your-tool/ {
       proxy_pass http://your_tool;
       # ... standard proxy headers
   }
   ```

4. **Update tool registry** in `app.py`

5. **Deploy**:
   ```bash
   sudo docker compose -f docker compose-tools-ssl.yaml up -d --build
   ```

## Support

- **Tools Portal Issues**: [GitHub Issues](https://github.com/apathy-ca/tools-portal/issues)
- **DNS By Eye Issues**: [GitHub Issues](https://github.com/apathy-ca/dns_by_eye/issues)
- **Documentation**: README files in each repository
- **Live Demo**: [https://tools.apathy.ca](https://tools.apathy.ca)

---

**Deployment Complete!** Your integrated DNS By Eye and Tools Portal system is now running with SSL, monitoring, and automatic maintenance.
