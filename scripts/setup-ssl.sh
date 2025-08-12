#!/bin/bash

# Tools Portal SSL Setup Script
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
    echo -e "${BLUE}Tools Portal SSL Setup${NC}"
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
    echo "  - Git submodules initialized (git submodule update --init --recursive)"
}

# Check arguments
if [ $# -lt 1 ]; then
    usage
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-""}

echo -e "${GREEN}Tools Portal SSL Setup${NC}"
echo "================================"
echo -e "${YELLOW}Setting up SSL for domain: $DOMAIN${NC}"

# Validate domain format
if ! [[ $DOMAIN =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$ ]]; then
    echo -e "${RED}Error: Invalid domain format${NC}"
    exit 1
fi

# Check if domain resolves to this server
echo -e "${BLUE}Checking DNS resolution...${NC}"
DOMAIN_IPV4=$(dig +short $DOMAIN A | tail -n1)
DOMAIN_IPV6=$(dig +short $DOMAIN AAAA | tail -n1)
SERVER_IPV4=$(curl -s -4 ifconfig.me 2>/dev/null || curl -s -4 ipinfo.io/ip 2>/dev/null || echo "")
SERVER_IPV6=$(curl -s -6 ifconfig.me 2>/dev/null || curl -s -6 ipinfo.io/ip 2>/dev/null || echo "")

# Check if domain has any IP records
if [ -z "$DOMAIN_IPV4" ] && [ -z "$DOMAIN_IPV6" ]; then
    echo -e "${RED}Warning: Domain $DOMAIN does not resolve to any IP address${NC}"
    echo "Please ensure your domain points to this server before continuing."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Check if domain resolves to this server (IPv4 or IPv6)
    MATCH_FOUND=false
    
    if [ -n "$DOMAIN_IPV4" ] && [ -n "$SERVER_IPV4" ] && [ "$DOMAIN_IPV4" = "$SERVER_IPV4" ]; then
        echo -e "${GREEN}✓ Domain resolves to this server's IPv4 address ($DOMAIN_IPV4)${NC}"
        MATCH_FOUND=true
    fi
    
    if [ -n "$DOMAIN_IPV6" ] && [ -n "$SERVER_IPV6" ] && [ "$DOMAIN_IPV6" = "$SERVER_IPV6" ]; then
        echo -e "${GREEN}✓ Domain resolves to this server's IPv6 address ($DOMAIN_IPV6)${NC}"
        MATCH_FOUND=true
    fi
    
    if [ "$MATCH_FOUND" = false ]; then
        echo -e "${YELLOW}Warning: Domain DNS records don't match this server's IP addresses${NC}"
        [ -n "$DOMAIN_IPV4" ] && echo "  Domain IPv4: $DOMAIN_IPV4"
        [ -n "$DOMAIN_IPV6" ] && echo "  Domain IPv6: $DOMAIN_IPV6"
        [ -n "$SERVER_IPV4" ] && echo "  Server IPv4: $SERVER_IPV4"
        [ -n "$SERVER_IPV6" ] && echo "  Server IPv6: $SERVER_IPV6"
        echo "SSL certificate generation may fail if domain doesn't point to this server."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Stop existing services and clear Docker cache
echo -e "${BLUE}Stopping existing services...${NC}"
docker compose -f docker-compose-tools-ssl.yaml down 2>/dev/null || true

echo -e "${BLUE}Clearing Docker build cache and removing existing images...${NC}"
docker system prune -a -f
docker builder prune -a -f
docker buildx prune -a -f 2>/dev/null || true

# Remove any existing images for this project
docker images | grep -E "(tools-portal|dns-by-eye)" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Clear any Docker Compose cache
docker compose -f docker-compose-tools-ssl.yaml down --rmi all --volumes --remove-orphans 2>/dev/null || true

# Check if nginx configuration exists and update domain
echo -e "${BLUE}Updating nginx configuration for domain: $DOMAIN${NC}"
if [ ! -f "nginx-tools-ssl.conf" ]; then
    echo -e "${RED}Error: nginx-tools-ssl.conf not found!${NC}"
    echo "Please ensure you're running this script from the tools-portal directory."
    exit 1
fi

# Update the domain in the nginx configuration
sed -i.bak "s/server_name [^;]*/server_name $DOMAIN/g" nginx-tools-ssl.conf
echo -e "${GREEN}✓ Updated nginx configuration with domain: $DOMAIN${NC}"

# Generate SSL certificate
echo -e "${BLUE}Generating SSL certificate...${NC}"
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL"
else
    EMAIL_ARG="--register-unsafely-without-email"
fi

docker compose -f docker-compose-tools-ssl.yaml run --rm -p 80:80 certbot certonly \
    --standalone \
    $EMAIL_ARG \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN

# Check if certificate was created
echo -e "${BLUE}Verifying certificate was created...${NC}"
if docker compose -f docker-compose-tools-ssl.yaml run --rm --entrypoint="" certbot test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
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
docker compose -f docker-compose-tools-ssl.yaml build --no-cache
docker compose -f docker-compose-tools-ssl.yaml up -d

# Wait for services to start
sleep 15

# Test the setup
echo -e "${BLUE}Testing SSL setup...${NC}"
if curl -I -m 10 https://$DOMAIN 2>/dev/null | grep -q "200 OK"; then
    echo -e "${GREEN}✓ HTTPS is working correctly!${NC}"
else
    echo -e "${YELLOW}Warning: HTTPS test failed, but services are running${NC}"
    echo "Check the logs: docker compose -f docker-compose-tools-ssl.yaml logs"
fi

echo -e "${GREEN}SSL setup complete!${NC}"
echo ""
echo "Your Tools Portal instance is now available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo "DNS By Eye is available at:"
echo -e "${GREEN}https://$DOMAIN/dns-by-eye/${NC}"
echo ""
echo "Management commands:"
echo "  View logs:      docker compose -f docker-compose-tools-ssl.yaml logs -f"
echo "  Restart:        docker compose -f docker-compose-tools-ssl.yaml restart"
echo "  Stop:           docker compose -f docker-compose-tools-ssl.yaml down"
echo "  Renew certs:    docker compose -f docker-compose-tools-ssl.yaml run --rm certbot renew"
echo ""
echo "Certificate auto-renewal is configured to run every 12 hours."
