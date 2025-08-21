#!/bin/bash
set -e

echo "🚀 Tools Portal Deployment Script"
echo "================================="

# Ensure we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run from tools-portal directory"
    exit 1
fi

# Initialize submodules if they exist
if [ -f ".gitmodules" ]; then
    echo "📦 Initializing git submodules..."
    git submodule update --init --recursive
    echo "✅ Submodules initialized"
else
    echo "ℹ️  No submodules found"
fi

# Verify tools are available
echo "🔍 Verifying tools..."
tool_count=0
for tool in tools/*/; do
    if [ -d "$tool" ]; then
        tool_name=$(basename "$tool")
        if [ -f "${tool}Dockerfile" ]; then
            echo "✅ Found: $tool_name (with Dockerfile)"
            ((tool_count++))
        else
            echo "⚠️  Warning: $tool_name missing Dockerfile - will be skipped"
        fi
    fi
done

if [ $tool_count -eq 0 ]; then
    echo "❌ No tools with Dockerfiles found!"
    echo "💡 Make sure submodules are properly initialized"
    exit 1
fi

# Generate compose files
echo "🐋 Generating Docker Compose configuration..."
if python3 generate-compose.py; then
    echo "✅ Docker Compose files generated successfully"
else
    echo "❌ Failed to generate Docker Compose files"
    exit 1
fi

echo ""
echo "🎉 Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "   For development: docker-compose -f docker-compose-tools.yaml up --build"
echo "   For production:  docker-compose -f docker-compose-tools-ssl.yaml up --build"
echo ""
echo "⚠️  For SSL deployment, make sure to:"
echo "   1. Update nginx-tools-ssl.conf with your domain"
echo "   2. Run ./scripts/setup-ssl.sh your-domain.com your-email@domain.com"
echo ""