# Tools Portal with AI Integration - Deployment Guide

## Overview

This guide covers deploying the enhanced Tools Portal with integrated Symposium AI chat functionality.

## Quick Start

### 1. Environment Setup

Create environment file:
```bash
cp .env.example .env.ai
```

Edit `.env.ai` with your configuration:
```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret-key

# Symposium AI Integration
SYMPOSIUM_BACKEND_URL=http://symposium-backend:8000
SYMPOSIUM_AUTH_TOKEN=your-symposium-auth-token

# AI Features
AI_CHAT_ENABLED=true
ENABLE_FILE_UPLOAD=true
ENABLE_SAGE_SELECTION=true
ENABLE_MODEL_SELECTION=true

# Optional: External Symposium Backend
# SYMPOSIUM_BACKEND_URL=https://your-symposium-instance.com
```

### 2. Using Enhanced Components

To use the AI-enhanced version:

```bash
# Backup original files
cp app.py app_original.py
cp templates/index.html templates/index_original.html
cp config.py config_original.py
cp requirements.txt requirements_original.txt

# Use enhanced versions
cp app_enhanced.py app.py
cp templates/index_enhanced.html templates/index.html
cp config_enhanced.py config.py
cp requirements_enhanced.txt requirements.txt
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test Local Development

```bash
# Start with AI integration
python app.py
```

Access at: `http://localhost:5000`

## Docker Deployment

### Enhanced Dockerfile

Create `Dockerfile.ai`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories for logs and static files
RUN mkdir -p logs static/css static/js

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
```

### Enhanced Docker Compose

Create `docker-compose.ai.yml`:
```yaml
version: '3.8'

services:
  tools-portal-ai:
    build:
      context: .
      dockerfile: Dockerfile.ai
    container_name: tools-portal-ai
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - SYMPOSIUM_BACKEND_URL=http://symposium-backend:8000
      - SYMPOSIUM_AUTH_TOKEN=${SYMPOSIUM_AUTH_TOKEN}
      - AI_CHAT_ENABLED=true
    volumes:
      - ./static:/app/static
      - ./logs:/app/logs
    networks:
      - tools-network
      - symposium-network  # Connect to Symposium network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      - redis

  # Existing services (DNS By Eye, IP Whale, etc.)
  dns-by-eye:
    build:
      context: ./tools/dns-by-eye
      dockerfile: Dockerfile
    container_name: dns-by-eye
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - STATIC_URL_PATH=/dns-by-eye/static
    volumes:
      - ./tools/dns-by-eye/app/static/generated:/app/app/static/generated
    networks:
      - tools-network

  ipwhale:
    build:
      context: ./tools/ipwhale
      dockerfile: Dockerfile
    container_name: ipwhale
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - STATIC_URL_PATH=/ipwhale/static
    networks:
      - tools-network

  redis:
    image: redis:7-alpine
    container_name: tools-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - tools-network

  nginx:
    image: nginx:alpine
    container_name: tools-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-tools-ai.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - tools-portal-ai
      - dns-by-eye
      - ipwhale
    networks:
      - tools-network

volumes:
  redis_data:

networks:
  tools-network:
    driver: bridge
  symposium-network:
    external: true  # Connect to external Symposium network
```

### Enhanced Nginx Configuration

Create `nginx-tools-ai.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;

    # Upstream servers
    upstream tools-portal {
        server tools-portal-ai:5000;
    }

    upstream dns-by-eye {
        server dns-by-eye:5000;
    }

    upstream ipwhale {
        server ipwhale:5000;
    }

    server {
        listen 80;
        server_name localhost;

        # AI API endpoints (higher rate limits for chat)
        location /api/ai/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Main tools portal with AI integration
        location / {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # DNS By Eye tool
        location /dns-by-eye/ {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://dns-by-eye/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # IP Whale tool
        location /ipwhale/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://ipwhale/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=5 nodelay;
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            access_log off;
        }

        # Static files for tools portal
        location /static/ {
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Integration with Symposium

### Network Setup

If running alongside Symposium:

```bash
# Create shared network
docker network create symposium-network

# Start Symposium first
cd /path/to/symposium
docker-compose up -d

# Then start Tools Portal with AI
cd /path/to/tools-portal
docker-compose -f docker-compose.ai.yml up -d
```

### Environment Variables

```env
# Point to running Symposium instance
SYMPOSIUM_BACKEND_URL=http://symposium-backend:8000

# Or external Symposium instance
SYMPOSIUM_BACKEND_URL=https://your-symposium.example.com

# Authentication token (get from Symposium)
SYMPOSIUM_AUTH_TOKEN=your-actual-token
```

## Testing the Integration

### 1. Health Checks

```bash
# Check tools portal health
curl http://localhost/health

# Check AI integration health
curl http://localhost/api/ai/health

# Check detailed health
curl http://localhost/api/health/detailed
```

### 2. AI Chat Test

```bash
# Test AI chat endpoint
curl -X POST http://localhost/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, test message"}'

# Test sage listing
curl http://localhost/api/ai/sages
```

### 3. Web Interface

1. Open `http://localhost` in browser
2. Click "AI Assistant" button in bottom-right
3. Try sending a message
4. Test file upload functionality
5. Test sage selection

## Production Considerations

### Security

1. Set strong `SECRET_KEY`
2. Use HTTPS in production
3. Secure Symposium auth token
4. Enable rate limiting if needed
5. Configure CORS appropriately

### Performance

1. Use Redis for session storage
2. Enable gzip compression
3. Configure appropriate timeouts
4. Monitor resource usage

### Monitoring

1. Set up log aggregation
2. Monitor AI API response times
3. Track chat usage metrics
4. Set up health check alerts

## Troubleshooting

### AI Chat Not Working

1. Check Symposium backend connection
2. Verify auth token
3. Check network connectivity
4. Review browser console for errors

### File Upload Issues

1. Check file size limits
2. Verify file type restrictions
3. Check backend storage
4. Review upload logs

### Performance Issues

1. Monitor backend response times
2. Check database connections
3. Review memory usage
4. Analyze slow queries

## Rollback Plan

If needed, rollback to original version:

```bash
# Restore original files
cp app_original.py app.py
cp templates/index_original.html templates/index.html
cp config_original.py config.py
cp requirements_original.txt requirements.txt

# Restart services
docker-compose restart