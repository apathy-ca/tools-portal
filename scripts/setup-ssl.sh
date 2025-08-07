#!/bin/bash

# DNS By Eye SSL Setup Script
# Generic SSL setup for any domain using Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}DNS By Eye SSL Setup${NC}"
    echo "Usage: $0 <domain> [email]"
    echo ""
    echo "Arguments:"
    echo "  domain    Your domain name (e.g., example.com)"
    echo "  email     Email for Let's Encrypt notifications (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 example.com admin@example.com"
    echo "  $0 example.com"
    echo ""
    echo "Prerequisites:"
    echo "  - Domain must point to this server"
    echo "  - Ports 80 and 443 must be open"
    echo "  - Docker and docker-compose must be installed"
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}

echo -e "${GREEN}DNS By Eye SSL Setup${NC}"
echo "================================"
echo -e "${YELLOW}Setting up SSL for domain: $DOMAIN${NC}"

# Validate domain format
if ! [[ $DOMAIN =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
    echo -e "${RED}Error: Invalid domain format${NC}"
    exit 1
fi

# Check if domain resolves to this server
echo -e "${BLUE}Checking DNS resolution...${NC}"
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "Unable to determine")

if [ -z "$DOMAIN_IP" ]; then
    echo -e "${RED}Warning: Domain $DOMAIN does not resolve to any IP${NC}"
    echo "Please ensure your domain points to this server before continuing."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
elif [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${YELLOW}Warning: Domain resolves to $DOMAIN_IP but server IP is $SERVER_IP${NC}"
    echo "SSL certificate generation may fail if domain doesn't point to this server."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ DNS resolution looks correct${NC}"
fi

# Stop existing services
echo -e "${BLUE}Stopping existing services...${NC}"
docker compose -f docker-compose.ssl.yaml down 2>/dev/null || true

# Create nginx configuration for SSL
echo -e "${BLUE}Creating SSL nginx configuration...${NC}"
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:5000;
    }

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=general:10m rate=30r/s;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        
        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        # Redirect all other traffic to HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name $DOMAIN;

        # SSL configuration
        ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
        
        # SSL security settings
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Serve static files directly from nginx
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            try_files \$uri \$uri/ =404;
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://web;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # API-specific headers
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        }

        # Main application
        location / {
            limit_req zone=general burst=50 nodelay;
            
            proxy_pass http://web;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
EOF

# Generate SSL certificate
echo -e "${BLUE}Generating SSL certificate...${NC}"
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL"
else
    EMAIL_ARG="--register-unsafely-without-email"
fi

docker compose -f docker-compose.ssl.yaml run --rm -p 80:80 certbot certonly \
    --standalone \
    $EMAIL_ARG \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN

# Check if certificate was created
if docker compose -f docker-compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    echo -e "${GREEN}✓ SSL certificate generated successfully!${NC}"
else
    echo -e "${RED}✗ SSL certificate generation failed!${NC}"
    echo "Common issues:"
    echo "- Domain doesn't point to this server"
    echo "- Port 80 is blocked by firewall"
    echo "- Another service is using port 80"
    exit 1
fi

# Start all services
echo -e "${BLUE}Starting all services with SSL...${NC}"
docker compose -f docker-compose.ssl.yaml up -d

# Wait for services to start
sleep 15

# Test the setup
echo -e "${BLUE}Testing SSL setup...${NC}"
if curl -I -m 10 https://$DOMAIN 2>/dev/null | grep -q "200 OK"; then
    echo -e "${GREEN}✓ HTTPS is working correctly!${NC}"
else
    echo -e "${YELLOW}Warning: HTTPS test failed, but services are running${NC}"
    echo "Check the logs: docker compose -f docker-compose.ssl.yaml logs"
fi

echo -e "${GREEN}SSL setup complete!${NC}"
echo ""
echo "Your DNS By Eye instance is now available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo ""
echo "Management commands:"
echo "  View logs:      docker compose -f docker-compose.ssl.yaml logs -f"
echo "  Restart:        docker compose -f docker-compose.ssl.yaml restart"
echo "  Stop:           docker compose -f docker-compose.ssl.yaml down"
echo "  Renew certs:    docker compose -f docker-compose.ssl.yaml run --rm certbot renew"
echo ""
echo "Certificate auto-renewal is configured to run every 12 hours."
