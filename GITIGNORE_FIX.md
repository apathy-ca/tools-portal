# Fix: Add Instance-Specific Files to .gitignore

## Problem
The nginx config files are instance-specific and keep causing git conflicts:
- `nginx-tools-ssl.conf` - Local SSL configuration
- `nginx-tools-ssl.conf.bak` - Backup files

These should not be tracked in the repository as they contain local paths, certificates, and server-specific settings.

## Solution
Add these files to .gitignore and remove them from tracking:

```bash
cd ~/tools-portal

# Add nginx configs to .gitignore
echo "" >> .gitignore
echo "# Instance-specific nginx configurations" >> .gitignore
echo "nginx-tools-ssl.conf" >> .gitignore
echo "nginx-tools.conf" >> .gitignore
echo "*.conf.bak" >> .gitignore

# Remove from git tracking but keep local files
git rm --cached nginx-tools-ssl.conf
git rm --cached nginx-tools.conf

# Clean up backup files
rm -f *.conf.bak

# Clean up submodule untracked content
cd tools/dns-by-eye
git clean -fd
cd ../..

# Now commit the .gitignore changes and submodule update
git add .gitignore
git add tools/dns-by-eye
git commit -m "Add nginx configs to .gitignore and update submodule with rate limiting removal"

# Push changes
git push origin main

# Deploy with clean state
sudo docker compose -f docker-compose-tools-ssl.yaml down
sudo docker compose -f docker-compose-tools-ssl.yaml up -d --build
```

## Benefits
- ✅ No more git conflicts with nginx configs
- ✅ Instance-specific configurations stay local
- ✅ Clean repository state
- ✅ Easier deployments and updates

## Files That Should Be Ignored
- `nginx-tools-ssl.conf` - SSL-specific nginx config
- `nginx-tools.conf` - Non-SSL nginx config  
- `*.conf.bak` - Any backup configuration files
- Local SSL certificates and keys
- Instance-specific environment files

This will prevent these deployment issues in the future.
