#!/bin/bash
set -e

echo "🔧 Tools Portal Submodule Fix Script"
echo "===================================="

# Ensure we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run from tools-portal directory"
    exit 1
fi

echo "⚠️  This script will fix the repository inconsistency by making both tools proper submodules."
echo "📋 Current state:"
echo "   - ipwhale: committed directly (not a submodule)"
echo "   - dns-by-eye: proper submodule but uninitialized"
echo ""
echo "🎯 After fix:"
echo "   - Both tools will be proper git submodules"
echo "   - Consistent behavior for all deployments"
echo ""

read -p "Do you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 1
fi

# Backup current state
echo "💾 Creating backup..."
cp -r tools tools-backup-$(date +%Y%m%d-%H%M%S)

# Step 1: Remove ipwhale from main repository
echo "🗑️  Removing ipwhale files from git tracking..."
git rm -r tools/ipwhale
git commit -m "Remove ipwhale files to convert to submodule"

# Step 2: Add ipwhale as proper submodule
echo "📦 Adding ipwhale as proper submodule..."
git submodule add https://github.com/apathy-ca/ipwhale.git tools/ipwhale
git commit -m "Add ipwhale as proper submodule"

# Step 3: Initialize dns-by-eye submodule
echo "📦 Initializing dns-by-eye submodule..."
git submodule update --init tools/dns-by-eye

# Step 4: Verify both submodules
echo "🔍 Verifying submodule status..."
git submodule status

# Step 5: Test the fix
echo "🧪 Testing the fix..."
if [ -f "tools/dns-by-eye/Dockerfile" ] && [ -f "tools/ipwhale/Dockerfile" ]; then
    echo "✅ Both tools have Dockerfiles"
else
    echo "❌ Missing Dockerfiles - something went wrong"
    exit 1
fi

# Step 6: Generate compose files to verify
echo "🐋 Testing Docker Compose generation..."
if python3 generate-compose.py; then
    echo "✅ Docker Compose generation successful"
else
    echo "❌ Docker Compose generation failed"
    exit 1
fi

echo ""
echo "🎉 Submodule fix completed successfully!"
echo ""
echo "📋 What was done:"
echo "   1. Removed ipwhale files from main repository"
echo "   2. Added ipwhale as proper submodule"
echo "   3. Initialized dns-by-eye submodule"
echo "   4. Verified both tools are working"
echo ""
echo "🚀 Next steps:"
echo "   1. Push changes: git push origin main"
echo "   2. Test fresh clone: git clone --recursive <repo-url>"
echo "   3. Update documentation if needed"
echo ""
echo "⚠️  Important: All future clones must use --recursive flag"
echo "   git clone --recursive https://github.com/apathy-ca/tools-portal.git"