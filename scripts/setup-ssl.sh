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
    echo "Usage: $0 <domain> [email] [bind-ip]"
    echo ""
    echo "Arguments:"
    echo "  domain    Your domain name (e.g., example.com)"
    echo "  email     Email for Let's Encrypt notifications (optional)"
    echo "  bind-ip   Specific IP address to bind services to (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 example.com admin@example.com"
    echo "  $0 example.com admin@example.com 192.168.1.100"
    echo "  $0 example.com \"\" 10.0.0.50"
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
BIND_IP=${3:-""}

echo -e "${GREEN}Tools Portal SSL Setup${NC}"
echo "================================"
echo -e "${YELLOW}Setting up SSL for domain: $DOMAIN${NC}"
if [ -n "$BIND_IP" ]; then
    echo -e "${YELLOW}Binding services to IP: $BIND_IP${NC}"
fi

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

# Stop existing services
echo -e "${BLUE}Stopping existing services...${NC}"
docker compose -f docker-compose-tools-ssl.yaml down 2>/dev/null || true

# Only remove project-specific images if they exist
echo -e "${BLUE}Cleaning up project images...${NC}"
docker images | grep -E "(tools-portal|dns-by-eye)" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Set Docker to use legacy builder (more reliable for our setup)
echo -e "${BLUE}Configuring Docker builder...${NC}"
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

# Update submodules to latest commits
echo -e "${BLUE}Updating submodules to latest commits...${NC}"
git submodule update --remote --force 2>/dev/null || git submodule update --init --recursive

# Generate nginx configuration with proper domain
echo -e "${BLUE}Generating nginx configuration for domain: $DOMAIN${NC}"
if [ -f "generate-compose.py" ]; then
    echo -e "${BLUE}Regenerating configuration files with detected tools...${NC}"
    if [ -n "$BIND_IP" ]; then
        python3 generate-compose.py --bind-ip "$BIND_IP" 2>/dev/null || python generate-compose.py --bind-ip "$BIND_IP" 2>/dev/null || {
            echo -e "${YELLOW}Warning: Could not run generate-compose.py with bind-ip, using existing files${NC}"
        }
    else
        python3 generate-compose.py 2>/dev/null || python generate-compose.py 2>/dev/null || {
            echo -e "${YELLOW}Warning: Could not run generate-compose.py, using existing files${NC}"
        }
    fi
    
    # Update domain in the generated nginx config
    if [ -f "nginx-tools-ssl.conf" ]; then
        sed -i.bak "s/server_name [^;]*/server_name $DOMAIN/g" nginx-tools-ssl.conf
        sed -i "s|/etc/letsencrypt/live/[^/]*/|/etc/letsencrypt/live/$DOMAIN/|g" nginx-tools-ssl.conf
        echo -e "${GREEN}✓ Updated nginx configuration with domain: $DOMAIN${NC}"
    else
        echo -e "${RED}Error: nginx-tools-ssl.conf not found after generation!${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: generate-compose.py not found, checking for existing nginx config...${NC}"
    if [ ! -f "nginx-tools-ssl.conf" ]; then
        echo -e "${RED}Error: nginx-tools-ssl.conf not found!${NC}"
        echo "Please ensure you're running this script from the tools-portal directory."
        exit 1
    fi
    
    # Update the domain in the existing nginx configuration
    sed -i.bak "s/server_name [^;]*/server_name $DOMAIN/g" nginx-tools-ssl.conf
    sed -i "s|/etc/letsencrypt/live/[^/]*/|/etc/letsencrypt/live/$DOMAIN/|g" nginx-tools-ssl.conf
    echo -e "${GREEN}✓ Updated nginx configuration with domain: $DOMAIN${NC}"
fi

# Generate SSL certificate
echo -e "${BLUE}Generating SSL certificate...${NC}"
if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL"
else
    EMAIL_ARG="--register-unsafely-without-email"
fi

# Try to generate SSL certificate
CERT_RESULT=0
docker compose -f docker-compose-tools-ssl.yaml run --rm -p 80:80 --entrypoint="" certbot \
    certbot certonly \
    --standalone \
    $EMAIL_ARG \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN || CERT_RESULT=$?

# Check if certificate was created or already exists
echo -e "${BLUE}Verifying certificate status...${NC}"
if docker compose -f docker-compose-tools-ssl.yaml run --rm --entrypoint="" certbot test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    echo -e "${GREEN}✓ SSL certificate is available!${NC}"
elif [ $CERT_RESULT -ne 0 ]; then
    echo -e "${YELLOW}⚠ SSL certificate generation failed (exit code: $CERT_RESULT)${NC}"
    echo "This could be due to:"
    echo "- Let's Encrypt rate limiting (too many certificates issued recently)"
    echo "- Domain doesn't point to this server"
    echo "- Port 80 is blocked by firewall"
    echo "- Another service is using port 80"
    echo ""
    echo "You can:"
    echo "1. Wait for rate limit to reset (up to 7 days)"
    echo "2. Use existing certificates if available"
    echo "3. Deploy without SSL using docker-compose-tools.yaml"
    echo ""
    read -p "Continue with deployment anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled. You can retry later or use non-SSL deployment."
        exit 1
    fi
    echo -e "${YELLOW}Continuing deployment without new SSL certificate...${NC}"
fi

# Start all services
echo -e "${BLUE}Starting all services with SSL...${NC}"
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f docker-compose-tools-ssl.yaml build --no-cache
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f docker-compose-tools-ssl.yaml up -d

# Wait for services to start and check health
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 10

# Check if nginx is running and has loaded SSL certificates
echo -e "${BLUE}Checking nginx SSL configuration...${NC}"
NGINX_RUNNING=false
SSL_CERT_LOADED=false

for i in {1..6}; do
    if docker compose -f docker-compose-tools-ssl.yaml ps nginx | grep -q "Up"; then
        NGINX_RUNNING=true
        echo -e "${GREEN}✓ Nginx is running${NC}"
        break
    fi
    echo "Waiting for nginx to start... ($i/6)"
    sleep 5
done

if [ "$NGINX_RUNNING" = false ]; then
    echo -e "${RED}✗ Nginx failed to start${NC}"
    echo "Check nginx logs: docker compose -f docker-compose-tools-ssl.yaml logs nginx"
    exit 1
fi

# Check if SSL certificate files exist
if docker compose -f docker-compose-tools-ssl.yaml exec nginx test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem 2>/dev/null; then
    SSL_CERT_LOADED=true
    echo -e "${GREEN}✓ SSL certificate files are accessible to nginx${NC}"
else
    echo -e "${YELLOW}⚠ SSL certificate files not found or not accessible${NC}"
fi

# Test the setup with better error handling
echo -e "${BLUE}Testing HTTPS connectivity...${NC}"
HTTPS_TEST_RESULT=""
HTTP_STATUS=""

# Try HTTPS test with more detailed output
HTTPS_TEST_RESULT=$(curl -I -m 15 -k https://$DOMAIN 2>&1)
HTTP_STATUS=$(echo "$HTTPS_TEST_RESULT" | head -n1 | grep -o "HTTP/[0-9.]* [0-9]*" | grep -o "[0-9]*$" || echo "")

if echo "$HTTPS_TEST_RESULT" | grep -q "200"; then
    echo -e "${GREEN}✓ HTTPS is working correctly! (Status: $HTTP_STATUS)${NC}"
elif echo "$HTTPS_TEST_RESULT" | grep -q "curl:"; then
    echo -e "${RED}✗ HTTPS connection failed${NC}"
    echo "Error details:"
    echo "$HTTPS_TEST_RESULT"
    echo ""
    echo "Common causes:"
    echo "- SSL certificate not properly loaded"
    echo "- Nginx configuration error"
    echo "- Firewall blocking port 443"
    echo "- Certificate validation issues"
    echo ""
    echo "Diagnostic commands:"
    echo "  Check nginx config: docker compose -f docker-compose-tools-ssl.yaml exec nginx nginx -t"
    echo "  Check certificate: docker compose -f docker-compose-tools-ssl.yaml exec nginx openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -text -noout"
    echo "  Check nginx logs: docker compose -f docker-compose-tools-ssl.yaml logs nginx"
else
    echo -e "${YELLOW}⚠ HTTPS test returned unexpected result (Status: $HTTP_STATUS)${NC}"
    echo "Response details:"
    echo "$HTTPS_TEST_RESULT"
fi

# Test HTTP to HTTPS redirect
echo -e "${BLUE}Testing HTTP to HTTPS redirect...${NC}"
HTTP_REDIRECT_RESULT=$(curl -I -m 10 http://$DOMAIN 2>&1)
if echo "$HTTP_REDIRECT_RESULT" | grep -q "301\|302"; then
    echo -e "${GREEN}✓ HTTP to HTTPS redirect is working${NC}"
else
    echo -e "${YELLOW}⚠ HTTP redirect test failed${NC}"
    echo "Response: $HTTP_REDIRECT_RESULT"
fi

echo -e "${GREEN}SSL setup complete!${NC}"
echo ""
echo "Your Tools Portal instance is now available at:"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo "Available tools:"
echo -e "${GREEN}https://$DOMAIN/dns-by-eye/${NC} - DNS By Eye"
echo -e "${GREEN}https://$DOMAIN/ipwhale/${NC} - IP Whale"
echo ""
echo "Management commands:"
echo "  View logs:      docker compose -f docker-compose-tools-ssl.yaml logs -f"
echo "  Restart:        docker compose -f docker-compose-tools-ssl.yaml restart"
echo "  Stop:           docker compose -f docker-compose-tools-ssl.yaml down"
echo "  Renew certs:    docker compose -f docker-compose-tools-ssl.yaml run --rm certbot renew"
echo ""
echo "Certificate auto-renewal is configured to run every 12 hours."
