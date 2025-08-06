#!/bin/bash

# DNS By Eye SSL Troubleshooting Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DOMAIN=${1:-""}

echo -e "${BLUE}DNS By Eye SSL Troubleshooting${NC}"
echo "=================================="

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Usage: $0 <domain>${NC}"
    echo "Example: $0 tools.apathy.ca"
    exit 1
fi

echo -e "${YELLOW}Troubleshooting SSL setup for: $DOMAIN${NC}"
echo ""

# Check if domain resolves to this server
echo -e "${BLUE}1. Checking DNS resolution...${NC}"
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "Unable to determine")
echo "Domain $DOMAIN resolves to: $DOMAIN_IP"
echo "This server's public IP: $SERVER_IP"

if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
    echo -e "${GREEN}✓ DNS resolution looks correct${NC}"
else
    echo -e "${RED}✗ DNS resolution issue - domain doesn't point to this server${NC}"
fi
echo ""

# Check if port 80 is accessible
echo -e "${BLUE}2. Checking HTTP accessibility...${NC}"
if curl -I -m 10 http://$DOMAIN 2>/dev/null | head -n1; then
    echo -e "${GREEN}✓ HTTP (port 80) is accessible${NC}"
else
    echo -e "${RED}✗ HTTP (port 80) is not accessible${NC}"
    echo "This could be due to:"
    echo "- Firewall blocking port 80"
    echo "- Services not running"
    echo "- DNS not pointing to this server"
fi
echo ""

# Check Docker services status
echo -e "${BLUE}3. Checking Docker services...${NC}"
if docker compose -f docker-compose.ssl.yaml ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Some Docker services are running${NC}"
    docker compose -f docker-compose.ssl.yaml ps
else
    echo -e "${RED}✗ No Docker services appear to be running${NC}"
    echo "Try: docker compose -f docker-compose.ssl.yaml up -d"
fi
echo ""

# Check nginx configuration
echo -e "${BLUE}4. Checking nginx configuration...${NC}"
if docker compose -f docker-compose.ssl.yaml exec nginx nginx -t 2>/dev/null; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has errors${NC}"
    docker compose -f docker-compose.ssl.yaml exec nginx nginx -t
fi
echo ""

# Check if certificates exist
echo -e "${BLUE}5. Checking SSL certificates...${NC}"
if docker compose -f docker-compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/ 2>/dev/null; then
    echo -e "${GREEN}✓ SSL certificates exist for $DOMAIN${NC}"
    docker compose -f docker-compose.ssl.yaml run --rm certbot certbot certificates
else
    echo -e "${RED}✗ No SSL certificates found for $DOMAIN${NC}"
    echo "You need to generate certificates first"
fi
echo ""

# Check HTTPS accessibility
echo -e "${BLUE}6. Checking HTTPS accessibility...${NC}"
if curl -I -m 10 https://$DOMAIN 2>/dev/null | head -n1; then
    echo -e "${GREEN}✓ HTTPS (port 443) is accessible${NC}"
else
    echo -e "${RED}✗ HTTPS (port 443) is not accessible${NC}"
    echo "This could be due to:"
    echo "- No SSL certificates"
    echo "- Nginx not configured for SSL"
    echo "- Firewall blocking port 443"
fi
echo ""

# Show recent logs
echo -e "${BLUE}7. Recent service logs...${NC}"
echo -e "${YELLOW}Nginx logs:${NC}"
docker compose -f docker-compose.ssl.yaml logs --tail=10 nginx 2>/dev/null || echo "Nginx not running"
echo ""
echo -e "${YELLOW}Certbot logs:${NC}"
docker compose -f docker-compose.ssl.yaml logs --tail=10 certbot 2>/dev/null || echo "Certbot not running"
echo ""

# Recommendations
echo -e "${BLUE}8. Recommendations:${NC}"
echo ""
if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${RED}• Fix DNS: Point $DOMAIN to $SERVER_IP${NC}"
fi

if ! curl -I -m 10 http://$DOMAIN >/dev/null 2>&1; then
    echo -e "${RED}• Check firewall: Ensure ports 80 and 443 are open${NC}"
    echo -e "${RED}• Start services: docker compose -f docker-compose.ssl.yaml up -d${NC}"
fi

if ! docker compose -f docker-compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/ >/dev/null 2>&1; then
    echo -e "${RED}• Generate certificates: ./setup-ssl.sh $DOMAIN your-email@domain.com${NC}"
fi

echo ""
echo -e "${BLUE}Manual certificate generation (if setup script fails):${NC}"
echo "docker compose -f docker-compose.ssl.yaml run --rm certbot certonly \\"
echo "  --webroot --webroot-path=/var/www/certbot \\"
echo "  --email your-email@domain.com --agree-tos --no-eff-email \\"
echo "  -d $DOMAIN"
echo ""
echo -e "${BLUE}Force certificate renewal:${NC}"
echo "docker compose -f docker-compose.ssl.yaml run --rm certbot renew --force-renewal"
