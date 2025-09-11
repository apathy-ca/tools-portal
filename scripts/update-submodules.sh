#!/bin/bash

# Update Submodules to Latest Script
# This script updates all submodules to their latest commits on their tracked branches

echo "🔄 Updating submodules to latest versions..."

# Update all submodules to their latest remote commits
git submodule update --remote

# Check if there are any changes to commit
if git diff --quiet --exit-code; then
    echo "✅ All submodules are already up to date!"
else
    echo "📝 Submodule updates detected. Committing changes..."
    
    # Add the submodule updates
    git add .
    
    # Create a commit message with details
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    git commit -m "Update submodules to latest versions - $TIMESTAMP

- dns-by-eye: $(cd tools/dns-by-eye && git log -1 --oneline)
- ipwhale: $(cd tools/ipwhale && git log -1 --oneline)

Auto-updated by update-submodules.sh"
    
    echo "✅ Submodule updates committed!"
    echo ""
    echo "🚀 To push these changes, run:"
    echo "   git push"
fi

echo ""
echo "📋 Current submodule status:"
git submodule status