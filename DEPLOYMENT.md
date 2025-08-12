# Tools Portal Deployment Guide

This guide explains how to deploy the new multi-tool architecture with DNS By Eye as the first tool.

## 🏗️ Architecture Overview

The Tools Portal uses a microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │  Tools Portal   │    │   DNS By Eye    │
│   (Port 80)     │────│   (Port 5000)   │    │   (Port 5000)   │
│                 │    │                 │    │                 │
│ Routes:         │    │ Routes:         │    │ Routes:         │
│ /               │────│ /               │    │ /api/delegation │
│ /dns-by-eye/    │────┼─────────────────┼────│ /api/trace/     │
│ /api/tools      │────│ /api/tools      │    │ /               │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to repository
git clone https://github.com/apathy-ca/dns_by_eye.git
cd dns_by_eye

# Start all services
docker compose -f docker-compose-tools.yaml up -d

# Check status
docker compose -f docker-compose-tools.yaml ps

# View logs
docker compose -f docker-compose-tools.yaml logs -f
```

**Access Points:**
- **Tools Portal**: http://localhost/
- **DNS By Eye**: http://localhost/dns-by-eye/
- **API**: http://localhost/api/tools

### Option 2: Development Mode

```bash
# Start Tools Portal
pip install -r requirements.txt
python app.py &

# Start DNS By Eye (in another terminal)
cd tools/dns-by-eye
pip install -r requirements.txt
python app/main.py --port 5001 &

# Configure nginx to route between services
# (See nginx-tools.conf for configuration)
```

## 📁 Directory Structure

```
dns_by_eye/                     # Root repository
├── app.py                      # Main tools portal application
├── templates/                  # Portal templates
│   ├── index.html             # Landing page
│   ├── 404.html               # Error pages
│   └── 500.html
├── static/                     # Portal static files
├── requirements.txt            # Portal dependencies
├── Dockerfile                  # Portal container
├── nginx-tools.conf           # Nginx routing configuration
├── docker-compose-tools.yaml  # Multi-service deployment
└── tools/                     # Individual tools
    └── dns-by-eye/            # DNS By Eye tool
        ├── app/               # DNS By Eye application
        ├── requirements.txt   # Tool-specific dependencies
        ├── Dockerfile         # Tool container
        └── README.md          # Tool documentation
```

## 🔧 Configuration

### Adding New Tools

1. **Create tool directory**: `tools/new-tool/`
2. **Add tool to registry** in `app.py`:

```python
TOOLS = {
    'dns-by-eye': { ... },
    'new-tool': {
        'name': 'New Tool',
        'description': 'Tool description',
        'version': '1.0.0',
        'url': '/new-tool/',
        'icon': '🔧',
        'category': 'System Administration',
        'status': 'stable',
        'features': ['Feature 1', 'Feature 2'],
        'tags': ['tag1', 'tag2']
    }
}
```

3. **Update nginx configuration** in `nginx-tools.conf`:

```nginx
upstream new_tool {
    server new-tool:5000;
}

location /new-tool/ {
    rewrite ^/new-tool/(.*)$ /$1 break;
    proxy_pass http://new_tool;
    # ... proxy headers
}
```

4. **Add service to docker-compose-tools.yaml**:

```yaml
services:
  new-tool:
    build:
      context: ./tools/new-tool
    container_name: new-tool
    restart: unless-stopped
    networks:
      - tools-network
```

### Environment Variables

**Tools Portal**:
- `FLASK_ENV`: production/development
- `PORT`: Server port (default: 5000)

**DNS By Eye**:
- `DNS_TIMEOUT`: Query timeout (default: 3s)
- `RATELIMIT_DEFAULT`: Rate limit (default: "100 per day")

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build and start all services
docker compose -f docker-compose-tools.yaml up -d --build

# Scale individual services if needed
docker compose -f docker-compose-tools.yaml up -d --scale dns-by-eye=2

# Update a specific service
docker compose -f docker-compose-tools.yaml up -d --build tools-portal

# Monitor resource usage
docker stats
```

### SSL/HTTPS Setup

For production with SSL certificates:

```bash
# Copy SSL configuration
cp docker-compose-tools.yaml docker-compose-tools-ssl.yaml

# Add SSL configuration to nginx service
# Update nginx-tools.conf with SSL settings
# Mount certificate volumes

# Deploy with SSL
docker compose -f docker-compose-tools-ssl.yaml up -d
```

## 🔍 Monitoring & Maintenance

### Health Checks

All services include health checks:

```bash
# Check service health
curl http://localhost/health                    # Tools Portal
curl http://localhost/dns-by-eye/api/health    # DNS By Eye

# Docker health status
docker compose -f docker-compose-tools.yaml ps
```

### Log Management

```bash
# View all logs
docker compose -f docker-compose-tools.yaml logs -f

# View specific service logs
docker compose -f docker-compose-tools.yaml logs -f tools-portal
docker compose -f docker-compose-tools.yaml logs -f dns-by-eye
docker compose -f docker-compose-tools.yaml logs -f nginx

# Log rotation (add to docker-compose)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Cleanup

```bash
# Clean up generated files (automated via cleanup service)
docker compose -f docker-compose-tools.yaml exec cleanup sh

# Manual cleanup
find ./tools/dns-by-eye/app/static/generated -name "*.png" -mtime +1 -delete

# Remove unused Docker resources
docker system prune -f
docker volume prune -f
```

## 🚨 Troubleshooting

### Common Issues

**1. Tool not accessible (404 errors)**
```bash
# Check nginx routing
docker compose -f docker-compose-tools.yaml logs nginx

# Verify service is running
docker compose -f docker-compose-tools.yaml ps

# Test direct service access
curl http://localhost:5000/  # Tools Portal
curl http://localhost:5001/  # DNS By Eye (if running separately)
```

**2. Service won't start**
```bash
# Check service logs
docker compose -f docker-compose-tools.yaml logs [service-name]

# Verify dependencies
docker compose -f docker-compose-tools.yaml exec [service-name] pip list

# Check port conflicts
netstat -tulpn | grep :5000
```

**3. Performance issues**
```bash
# Monitor resource usage
docker stats

# Check Redis cache
docker compose -f docker-compose-tools.yaml exec redis redis-cli info

# Scale services
docker compose -f docker-compose-tools.yaml up -d --scale dns-by-eye=3
```

### Debug Mode

Enable debug mode for development:

```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run with debug logging
docker compose -f docker-compose-tools.yaml up --build
```

## 📊 Performance Optimization

### Nginx Optimization

```nginx
# Add to nginx-tools.conf
worker_processes auto;
worker_connections 1024;

# Enable caching
location ~* \.(png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Compress responses
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

### Redis Caching

```python
# Configure in tools
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://redis:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
}
```

## 🔐 Security

### Production Security Checklist

- [ ] Use HTTPS with valid certificates
- [ ] Configure rate limiting
- [ ] Set up proper firewall rules
- [ ] Use non-root containers
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement proper CORS policies

### Security Headers

Already configured in nginx-tools.conf:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale DNS By Eye instances
docker compose -f docker-compose-tools.yaml up -d --scale dns-by-eye=3

# Add load balancing to nginx-tools.conf
upstream dns_by_eye {
    server dns-by-eye_1:5000;
    server dns-by-eye_2:5000;
    server dns-by-eye_3:5000;
}
```

### Vertical Scaling

```yaml
# Add resource limits to docker-compose-tools.yaml
services:
  dns-by-eye:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🔄 Updates & Migrations

### Updating Tools

```bash
# Update specific tool
cd tools/dns-by-eye
git pull origin main
docker compose -f ../../docker-compose-tools.yaml up -d --build dns-by-eye

# Update portal
git pull origin main
docker compose -f docker-compose-tools.yaml up -d --build tools-portal
```

### Database Migrations

For tools that require databases:

```bash
# Run migrations
docker compose -f docker-compose-tools.yaml exec [service] python manage.py migrate

# Backup before updates
docker compose -f docker-compose-tools.yaml exec postgres pg_dump -U user db > backup.sql
```

This deployment guide provides comprehensive instructions for setting up, maintaining, and scaling the Tools Portal architecture.
