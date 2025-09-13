#!/bin/bash

# DNS By Eye Troubleshooting Script
# Comprehensive diagnostics for deployment issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}DNS By Eye Troubleshooting${NC}"
    echo "Usage: $0 [domain]"
    echo ""
    echo "Arguments:"
    echo "  domain    Your domain name (optional, for SSL checks)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Basic troubleshooting"
    echo "  $0 example.com        # Include SSL/domain checks"
    echo ""
    echo "This script will check:"
    echo "  - Docker services status"
    echo "  - Port accessibility"
    echo "  - Configuration files"
    echo "  - SSL certificates (if domain provided)"
    echo "  - Recent logs"
}

DOMAIN=${1:-""}

echo -e "${BLUE}DNS By Eye Troubleshooting${NC}"
echo "=================================="

if [ -n "$DOMAIN" ]; then
    echo -e "${YELLOW}Troubleshooting for domain: $DOMAIN${NC}"
else
    echo -e "${YELLOW}Basic troubleshooting (no domain specified)${NC}"
fi
echo ""

# Check Docker installation
echo -e "${BLUE}1. Checking Docker installation...${NC}"
if command -v docker >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    docker --version
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Docker Compose is installed${NC}"
        docker compose version
    else
        echo -e "${RED}✗ Docker Compose not found${NC}"
        echo "Install with: sudo apt-get install docker compose-plugin"
    fi
else
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi
echo ""

# Check if domain resolves (if provided)
if [ -n "$DOMAIN" ]; then
    echo -e "${BLUE}2. Checking DNS resolution...${NC}"
    if command -v dig >/dev/null 2>&1; then
        DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
        SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to determine")
        
        if [ -n "$DOMAIN_IP" ]; then
            echo "Domain $DOMAIN resolves to: $DOMAIN_IP"
            echo "This server's public IP: $SERVER_IP"
            
            if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
                echo -e "${GREEN}✓ DNS resolution looks correct${NC}"
            else
                echo -e "${RED}✗ DNS resolution issue - domain doesn't point to this server${NC}"
            fi
        else
            echo -e "${RED}✗ Domain $DOMAIN does not resolve${NC}"
        fi
    else
        echo -e "${YELLOW}Warning: dig command not found, skipping DNS check${NC}"
        echo "Install with: sudo apt-get install dnsutils"
    fi
    echo ""
fi

# Check port accessibility
echo -e "${BLUE}3. Checking port accessibility...${NC}"
if command -v netstat >/dev/null 2>&1; then
    echo "Ports currently in use:"
    netstat -tlnp | grep -E ':80|:443|:5000' || echo "No services found on ports 80, 443, or 5000"
else
    echo -e "${YELLOW}Warning: netstat not found, cannot check port usage${NC}"
fi

# Test HTTP accessibility
if [ -n "$DOMAIN" ]; then
    echo "Testing HTTP accessibility..."
    if curl -I -m 10 http://$DOMAIN 2>/dev/null | head -n1; then
        echo -e "${GREEN}✓ HTTP (port 80) is accessible${NC}"
    else
        echo -e "${RED}✗ HTTP (port 80) is not accessible${NC}"
        echo "This could be due to:"
        echo "- Firewall blocking port 80"
        echo "- Services not running"
        echo "- DNS not pointing to this server"
    fi
fi
echo ""

# Check Docker services status
echo -e "${BLUE}4. Checking Docker services...${NC}"
if [ -f "docker compose.yaml" ]; then
    echo "Basic Docker Compose services:"
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓ Some basic services are running${NC}"
        docker compose ps
    else
        echo -e "${RED}✗ No basic services appear to be running${NC}"
        echo "Try: docker compose up -d"
    fi
    echo ""
fi

if [ -f "docker compose.ssl.yaml" ]; then
    echo "SSL Docker Compose services:"
    if docker compose -f docker compose.ssl.yaml ps 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✓ Some SSL services are running${NC}"
        docker compose -f docker compose.ssl.yaml ps
    else
        echo -e "${RED}✗ No SSL services appear to be running${NC}"
        echo "Try: docker compose -f docker compose.ssl.yaml up -d"
    fi
    echo ""
fi

# Check configuration files
echo -e "${BLUE}5. Checking configuration files...${NC}"
config_files=("nginx.conf" "nginx-http.conf" "docker compose.yaml" "docker compose.ssl.yaml")
for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${YELLOW}- $file not found${NC}"
    fi
done
echo ""

# Check nginx configuration (if running)
echo -e "${BLUE}6. Checking nginx configuration...${NC}"
if docker compose -f docker compose.ssl.yaml ps nginx 2>/dev/null | grep -q "Up"; then
    if docker compose -f docker compose.ssl.yaml exec nginx nginx -t 2>/dev/null; then
        echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}✗ Nginx configuration has errors${NC}"
        docker compose -f docker compose.ssl.yaml exec nginx nginx -t
    fi
elif docker compose ps nginx 2>/dev/null | grep -q "Up"; then
    if docker compose exec nginx nginx -t 2>/dev/null; then
        echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}✗ Nginx configuration has errors${NC}"
        docker compose exec nginx nginx -t
    fi
else
    echo -e "${YELLOW}- Nginx is not running${NC}"
fi
echo ""

# Check SSL certificates (if domain provided)
if [ -n "$DOMAIN" ]; then
    echo -e "${BLUE}7. Checking SSL certificates...${NC}"
    if docker compose -f docker compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/ 2>/dev/null; then
        echo -e "${GREEN}✓ SSL certificates exist for $DOMAIN${NC}"
        echo "Certificate details:"
        docker compose -f docker compose.ssl.yaml run --rm certbot certbot certificates 2>/dev/null | grep -A 10 "$DOMAIN" || true
    else
        echo -e "${RED}✗ No SSL certificates found for $DOMAIN${NC}"
        echo "Generate certificates with: ./scripts/setup-ssl.sh $DOMAIN"
    fi
    echo ""

    # Check HTTPS accessibility
    echo -e "${BLUE}8. Checking HTTPS accessibility...${NC}"
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
fi

# Show recent logs
echo -e "${BLUE}9. Recent service logs...${NC}"
echo -e "${YELLOW}Web application logs:${NC}"
if docker compose -f docker compose.ssl.yaml ps web 2>/dev/null | grep -q "Up"; then
    docker compose -f docker compose.ssl.yaml logs --tail=10 web 2>/dev/null || echo "No SSL web logs available"
elif docker compose ps web 2>/dev/null | grep -q "Up"; then
    docker compose logs --tail=10 web 2>/dev/null || echo "No basic web logs available"
else
    echo "Web service not running"
fi
echo ""

echo -e "${YELLOW}Nginx logs:${NC}"
if docker compose -f docker compose.ssl.yaml ps nginx 2>/dev/null | grep -q "Up"; then
    docker compose -f docker compose.ssl.yaml logs --tail=10 nginx 2>/dev/null || echo "No SSL nginx logs available"
elif docker compose ps nginx 2>/dev/null | grep -q "Up"; then
    docker compose logs --tail=10 nginx 2>/dev/null || echo "No basic nginx logs available"
else
    echo "Nginx service not running"
fi
echo ""

if [ -n "$DOMAIN" ]; then
    echo -e "${YELLOW}Certbot logs:${NC}"
    docker compose -f docker compose.ssl.yaml logs --tail=10 certbot 2>/dev/null || echo "No certbot logs available"
    echo ""
fi

# Recommendations
echo -e "${BLUE}10. Recommendations:${NC}"
echo ""

# Check if services are running
if ! docker compose ps 2>/dev/null | grep -q "Up" && ! docker compose -f docker compose.ssl.yaml ps 2>/dev/null | grep -q "Up"; then
    echo -e "${RED}• Start services:${NC}"
    echo "  Basic: docker compose up -d"
    echo "  SSL:   docker compose -f docker compose.ssl.yaml up -d"
fi

# DNS recommendations
if [ -n "$DOMAIN" ] && [ -n "$DOMAIN_IP" ] && [ -n "$SERVER_IP" ] && [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${RED}• Fix DNS: Point $DOMAIN to $SERVER_IP${NC}"
fi

# Port accessibility recommendations
if [ -n "$DOMAIN" ] && ! curl -I -m 10 http://$DOMAIN >/dev/null 2>&1; then
    echo -e "${RED}• Check firewall: Ensure ports 80 and 443 are open${NC}"
    echo "  Ubuntu/Debian: sudo ufw allow 80 && sudo ufw allow 443"
    echo "  CentOS/RHEL:   sudo firewall-cmd --permanent --add-port=80/tcp --add-port=443/tcp && sudo firewall-cmd --reload"
fi

# SSL recommendations
if [ -n "$DOMAIN" ] && ! docker compose -f docker compose.ssl.yaml run --rm certbot ls /etc/letsencrypt/live/$DOMAIN/ >/dev/null 2>&1; then
    echo -e "${RED}• Generate SSL certificates:${NC}"
    echo "  ./scripts/setup-ssl.sh $DOMAIN your-email@domain.com"
fi

echo ""
echo -e "${BLUE}Quick commands:${NC}"
echo "  View all logs:     docker compose -f docker compose.ssl.yaml logs -f"
echo "  Restart services:  docker compose -f docker compose.ssl.yaml restart"
echo "  Stop services:     docker compose -f docker compose.ssl.yaml down"
echo "  Rebuild:           docker compose -f docker compose.ssl.yaml up --build -d"

if [ -n "$DOMAIN" ]; then
    echo "  Renew SSL:         docker compose -f docker compose.ssl.yaml run --rm certbot renew --force-renewal"
fi

echo ""
echo -e "${GREEN}Troubleshooting complete!${NC}"
