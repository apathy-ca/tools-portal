#!/bin/bash

# Fix Current DNS By Eye Setup
# This script fixes the logo issue and generates SSL certificates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN="tools.apathy.ca"
EMAIL="james@apathy.ca"

echo -e "${GREEN}Fixing DNS By Eye Setup${NC}"
echo "================================"

# Step 1: Stop current services
echo "Stopping current services..."
sudo docker compose -f docker-compose.ssl.yaml down || true

# Step 2: Use HTTP-only config temporarily to fix logo
echo "Setting up HTTP-only configuration to fix logo..."
cp nginx-http.conf nginx.conf

# Step 3: Start services with HTTP-only config
echo "Starting services with HTTP-only config..."
sudo docker compose -f docker-compose.ssl.yaml up -d web redis nginx

# Wait for services to start
sleep 10

# Step 4: Test logo loading
echo "Testing logo loading..."
if curl -I http://$DOMAIN/static/logo.svg | grep -q "200 OK"; then
    echo -e "${GREEN}✓ Logo is now loading properly${NC}"
else
    echo -e "${RED}✗ Logo still not loading${NC}"
fi

# Step 5: Generate SSL certificates using standalone mode
echo "Stopping nginx for certificate generation..."
sudo docker compose -f docker-compose.ssl.yaml stop nginx

echo "Generating SSL certificates..."
sudo docker compose -f docker-compose.ssl.yaml run --rm -p 80:80 certbot certonly \
    --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN

# Step 6: Create proper SSL nginx config
echo "Creating SSL nginx configuration..."
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

# Step 7: Start all services with SSL
echo "Starting all services with SSL..."
sudo docker compose -f docker-compose.ssl.yaml up -d

# Step 8: Test everything
sleep 15

echo "Testing HTTP redirect..."
curl -I http://$DOMAIN/ | head -n 5

echo "Testing HTTPS..."
curl -I https://$DOMAIN/ | head -n 5

echo "Testing logo over HTTPS..."
curl -I https://$DOMAIN/static/logo.svg | head -n 5

echo -e "${GREEN}Setup complete!${NC}"
echo "Your DNS By Eye instance should now be available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo ""
echo "The logo should now load properly and SSL should work."
