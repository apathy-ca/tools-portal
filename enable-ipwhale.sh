#!/bin/bash
# IPWhale Enablement Script for Tools-Portal
# This script enables IPWhale in an already-built tools-portal system

set -e

echo "🐋 IPWhale Enablement Script"
echo "=============================="

# Check if we're in the tools-portal directory
if [ ! -f "docker-compose-tools.yaml" ]; then
    echo "❌ Error: Please run this script from the tools-portal directory"
    exit 1
fi

echo "📋 Checking current setup..."

# Check if IPWhale submodule exists
if [ ! -d "tools/ipwhale" ]; then
    echo "⚠️  IPWhale submodule not found. Setting up..."
    
    # Add IPWhale as submodule
    git submodule add https://github.com/apathy-ca/ipwhale.git tools/ipwhale
    git submodule init
    git submodule update --recursive --remote
    
    echo "✅ IPWhale submodule added successfully"
else
    echo "✅ IPWhale submodule already exists"
    
    # Update submodule to latest
    echo "🔄 Updating IPWhale to latest version..."
    git submodule update --remote tools/ipwhale
fi

# Check if IPWhale is configured in app.py
if grep -q "ipwhale" app.py; then
    echo "✅ IPWhale already configured in app.py"
else
    echo "⚠️  IPWhale not found in app.py configuration"
    echo "   Please ensure IPWhale is added to the TOOLS registry in app.py"
fi

# Check if IPWhale is in docker-compose
if grep -q "ipwhale:" docker-compose-tools.yaml; then
    echo "✅ IPWhale already configured in docker-compose-tools.yaml"
else
    echo "⚠️  IPWhale not found in docker-compose-tools.yaml"
    echo "   Please ensure IPWhale service is defined in docker-compose-tools.yaml"
fi

echo ""
echo "🚀 Starting IPWhale deployment..."

# Build and start IPWhale
echo "🔨 Building IPWhale container..."
docker compose -f docker-compose-tools.yaml build ipwhale

echo "🏃 Starting IPWhale service..."
docker compose -f docker-compose-tools.yaml up -d ipwhale

# Wait a moment for startup
echo "⏳ Waiting for IPWhale to start..."
sleep 5

# Test IPWhale health
echo "🏥 Testing IPWhale health..."
if curl -f -s http://localhost/ipwhale/api/health > /dev/null 2>&1; then
    echo "✅ IPWhale is healthy and responding"
else
    echo "⚠️  IPWhale health check failed - checking container logs..."
    docker logs ipwhale --tail 20
fi

echo ""
echo "🎉 IPWhale Enablement Complete!"
echo ""
echo "📍 Access Points:"
echo "   Web Interface: http://localhost/ipwhale/"
echo "   API Health:    http://localhost/ipwhale/api/health"
echo "   IPv4 API:      http://localhost/ipwhale/api/4/ip"
echo "   Full API:      http://localhost/ipwhale/api/full"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:     docker logs ipwhale"
echo "   Restart:       docker compose -f docker-compose-tools.yaml restart ipwhale"
echo "   Update:        git submodule update --remote tools/ipwhale && docker compose -f docker-compose-tools.yaml up --build ipwhale"
echo ""
echo "📚 For more information, see IPWHALE_DEPLOYMENT_GUIDE.md"
