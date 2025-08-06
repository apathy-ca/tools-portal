#!/bin/bash

# Simple SSL Fix Script for DNS By Eye

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DOMAIN=${1:-"tools.apathy.ca"}
EMAIL=${2:-"james@apathy.ca"}

echo -e "${GREEN}DNS By Eye SSL Fix${NC}"
echo "================================"

echo -e "${YELLOW}Fixing SSL for domain: $DOMAIN${NC}"

# Stop all services
echo "Stopping all services..."
sudo docker compose -f docker-compose.ssl.yaml down || true

# Remove all volumes to start fresh
echo "Cleaning up volumes..."
sudo docker volume rm dns_by_eye_certbot_conf dns_by_eye_certbot_www dns_by_eye_generated_files dns_by_eye_redis_data || true

# Create a simple nginx config for certificate generation
echo "Creating simple nginx config..."
cat > nginx-simple.conf << EOF
events {
    worker_connections 1024;
}

http {
    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
            try_files \$uri \$uri/ =404;
        }
        
        location / {
            return 200 'SSL Setup in Progress';
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Copy the simple config
cp nginx-simple.conf nginx.conf

# Start only nginx for certificate generation
echo "Starting nginx for certificate generation..."
sudo docker compose -f docker-compose.ssl.yaml up -d nginx

# Wait for nginx to start
sleep 10

# Test if nginx is responding
echo "Testing nginx..."
curl -I http://$DOMAIN/ || echo "Warning: nginx not responding"

# Generate certificate using standalone mode first
echo "Generating certificate using standalone mode..."
sudo docker compose -f docker-compose.ssl.yaml down nginx

# Use standalone mode to avoid nginx conflicts
sudo docker compose -f docker-compose.ssl.yaml run --rm -p 80:80 certbot certonly \
    --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN

# Check if certificate was created
if sudo docker compose -f docker-compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    echo -e "${GREEN}Certificate generated successfully!${NC}"
else
    echo -e "${RED}Certificate generation failed!${NC}"
    exit 1
fi

# Now create the full SSL nginx config
echo "Creating full SSL nginx config..."
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:5000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
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

        # Main application
        location / {
            proxy_pass http://web;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF

# Start all services
echo "Starting all services with SSL..."
sudo docker compose -f docker-compose.ssl.yaml up -d

# Clean up
rm -f nginx-simple.conf

echo -e "${GREEN}SSL fix complete!${NC}"
echo "Your DNS By Eye instance should now be available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo ""
echo "Test the connection:"
echo "curl -I https://$DOMAIN"
