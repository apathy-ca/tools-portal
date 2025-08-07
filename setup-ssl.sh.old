#!/bin/bash

# DNS By Eye SSL Setup Script
# This script helps set up SSL certificates using Let's Encrypt

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}DNS By Eye SSL Setup${NC}"
echo "================================"

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Domain name is required${NC}"
    echo "Usage: $0 <your-domain.com> [email@example.com]"
    echo "Example: $0 tools.apathy.ca admin@apathy.ca"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}

echo -e "${YELLOW}Setting up SSL for domain: $DOMAIN${NC}"

# Update nginx.conf with the actual domain
echo "Updating nginx.conf with domain: $DOMAIN"
sed -i "s/YOUR_DOMAIN/$DOMAIN/g" nginx.conf

# Create initial nginx config without SSL for certificate generation
echo "Creating temporary nginx config for certificate generation..."
cat > nginx-temp.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:5000;
    }

    server {
        listen 80;
        server_name $DOMAIN;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
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

# Start services without SSL first
echo "Starting services for certificate generation..."
cp nginx-temp.conf nginx.conf
docker compose -f docker-compose.ssl.yaml up -d web redis nginx

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Create a test file for ACME challenge verification
echo "Creating test file for ACME challenge verification..."
docker compose -f docker-compose.ssl.yaml exec nginx mkdir -p /var/www/certbot/.well-known/acme-challenge
docker compose -f docker-compose.ssl.yaml exec nginx sh -c 'echo "test-challenge-file" > /var/www/certbot/.well-known/acme-challenge/test'

# Generate SSL certificate
echo "Generating SSL certificate..."
echo "Testing domain accessibility..."
echo "Testing basic HTTP access..."
curl -I http://$DOMAIN/ || echo "Warning: Basic HTTP access failed"
echo "Testing ACME challenge path..."
curl -I http://$DOMAIN/.well-known/acme-challenge/test || echo "Warning: ACME challenge path not accessible"

# Remove any existing certificates first
echo "Cleaning up any existing certificates..."
docker compose -f docker-compose.ssl.yaml run --rm certbot delete --cert-name $DOMAIN --non-interactive || true

if [ -n "$EMAIL" ]; then
    echo "Requesting certificate with email: $EMAIL"
    docker compose -f docker-compose.ssl.yaml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        --verbose \
        --expand \
        -d $DOMAIN
else
    echo "Requesting certificate without email (not recommended)"
    docker compose -f docker-compose.ssl.yaml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --register-unsafely-without-email \
        --agree-tos \
        --non-interactive \
        --verbose \
        --expand \
        -d $DOMAIN
fi

# Check if certificate was created
echo "Checking if certificate was generated..."
if docker compose -f docker-compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    echo -e "${GREEN}Certificate generated successfully!${NC}"
else
    echo -e "${RED}Certificate generation failed!${NC}"
    echo "Checking certbot logs..."
    docker compose -f docker-compose.ssl.yaml logs certbot
    echo -e "${RED}Please check that:${NC}"
    echo "1. Domain $DOMAIN points to this server"
    echo "2. Port 80 is accessible from the internet"
    echo "3. No firewall is blocking the connection"
    echo "4. Try running: curl -I http://$DOMAIN"
    exit 1
fi

# Restore the full nginx config with SSL
echo "Restoring full nginx configuration with SSL..."
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
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

        # Static files with caching
        location /static/ {
            proxy_pass http://web;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # Cache static files
            expires 1y;
            add_header Cache-Control "public, immutable";
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

# Restart nginx with SSL configuration
echo "Restarting nginx with SSL configuration..."
docker compose -f docker-compose.ssl.yaml restart nginx

# Start certbot for automatic renewal
echo "Starting certbot for automatic certificate renewal..."
docker compose -f docker-compose.ssl.yaml up -d certbot

# Clean up
rm -f nginx-temp.conf

echo -e "${GREEN}SSL setup complete!${NC}"
echo "Your DNS By Eye instance is now available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo ""
echo "All services are running as daemons (in the background)."
echo "Certificate will be automatically renewed every 12 hours."
echo ""
echo -e "${YELLOW}Management Commands:${NC}"
echo "Check status:           docker compose -f docker-compose.ssl.yaml ps"
echo "View logs:              docker compose -f docker-compose.ssl.yaml logs -f"
echo "Check certificate:      docker compose -f docker-compose.ssl.yaml exec certbot certbot certificates"
echo "Stop services:          docker compose -f docker-compose.ssl.yaml down"
echo "Restart services:       docker compose -f docker-compose.ssl.yaml restart"
echo ""
echo -e "${GREEN}Setup completed successfully! Services are running in daemon mode.${NC}"
