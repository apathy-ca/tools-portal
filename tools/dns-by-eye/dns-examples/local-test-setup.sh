#!/bin/bash

# Local DNS Test Setup for DNS By Eye
# This sets up a local BIND server for testing without affecting production DNS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}DNS By Eye Local Test Setup${NC}"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Install BIND if not present
if ! command -v named &> /dev/null; then
    echo -e "${BLUE}Installing BIND9...${NC}"
    apt-get update
    apt-get install -y bind9 bind9utils bind9-doc
fi

# Create zones directory
mkdir -p /etc/bind/zones

# Copy zone files
echo -e "${BLUE}Setting up test zones...${NC}"
cp apathy.ca.zone /etc/bind/zones/
cp test.apathy.ca.zone /etc/bind/zones/
chown bind:bind /etc/bind/zones/*.zone

# Backup original configuration
cp /etc/bind/named.conf.local /etc/bind/named.conf.local.backup

# Add our zones to configuration
echo -e "${BLUE}Adding zones to BIND configuration...${NC}"
cat >> /etc/bind/named.conf.local << 'EOF'

// DNS By Eye Test Zones
zone "apathy.ca" {
    type master;
    file "/etc/bind/zones/apathy.ca.zone";
    allow-query { any; };
    allow-transfer { any; };
    notify yes;
};

zone "test.apathy.ca" {
    type master;
    file "/etc/bind/zones/test.apathy.ca.zone";
    allow-query { any; };
    allow-transfer { any; };
    notify yes;
};
EOF

# Check configuration
echo -e "${BLUE}Checking BIND configuration...${NC}"
named-checkconf

echo -e "${BLUE}Checking zone files...${NC}"
named-checkzone apathy.ca /etc/bind/zones/apathy.ca.zone
named-checkzone test.apathy.ca /etc/bind/zones/test.apathy.ca.zone

# Restart BIND
echo -e "${BLUE}Restarting BIND9...${NC}"
systemctl restart bind9
systemctl enable bind9

# Test the setup
echo -e "${BLUE}Testing local DNS setup...${NC}"
sleep 2

echo "Testing apathy.ca NS records:"
dig @localhost apathy.ca NS +short

echo "Testing test.apathy.ca NS records:"
dig @localhost test.apathy.ca NS +short

echo "Testing test.apathy.ca A record:"
dig @localhost test.apathy.ca A +short

echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To test with DNS By Eye:"
echo "1. Use 'localhost' or '127.0.0.1' as the DNS server"
echo "2. Query 'test.apathy.ca' to see the broken delegation issues"
echo ""
echo "Example URLs:"
echo "- https://tools.apathy.ca/?domains=test.apathy.ca&dns_server=127.0.0.1"
echo "- https://tools.apathy.ca/?domains=test.apathy.ca&dns_server=127.0.0.1&verbose=true"
echo ""
echo "To cleanup:"
echo "sudo systemctl stop bind9"
echo "sudo cp /etc/bind/named.conf.local.backup /etc/bind/named.conf.local"
echo "sudo rm /etc/bind/zones/apathy.ca.zone /etc/bind/zones/test.apathy.ca.zone"
