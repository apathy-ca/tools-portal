# Deployment Update Guide: Single Tool → Multi-Tool Architecture

## Current Status
✅ **Tools Portal** is deployed and working at https://tools.apathy.ca/
❌ **DNS By Eye tool** returns 404 at https://tools.apathy.ca/dns-by-eye/

## Issue
The live deployment is running the new Tools Portal landing page but hasn't been updated to use the new multi-tool architecture with separate services for each tool.

## Solution: Deploy Multi-Tool Architecture

### Option 1: Quick Fix - Update Existing Deployment

If you want to keep the current single-container approach temporarily:

1. **Update the main app.py to include DNS By Eye routing**:

```python
# Add to app.py
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect
import subprocess
import sys
import os

# Add DNS By Eye routes
@app.route('/dns-by-eye/')
@app.route('/dns-by-eye/<path:path>')
def dns_by_eye_proxy(path=''):
    """Proxy requests to DNS By Eye tool"""
    # For now, redirect to the old DNS By Eye until microservices are deployed
    if path == '':
        # Serve DNS By Eye from tools directory
        sys.path.insert(0, 'tools/dns-by-eye')
        from app.main import app as dns_app
        return dns_app.test_client().get('/').data.decode()
    else:
        # Handle API and other routes
        return redirect(f'/{path}')
```

### Option 2: Full Multi-Tool Deployment (Recommended)

Deploy the complete microservices architecture:

```bash
# On your server, update to the new architecture
cd /path/to/your/deployment
git pull origin main

# Stop current deployment
docker compose down

# Deploy new multi-tool architecture
docker compose -f docker-compose-tools.yaml up -d --build

# Check status
docker compose -f docker-compose-tools.yaml ps
```

### Option 3: Gradual Migration

1. **Keep current deployment running**
2. **Deploy new architecture on different ports**
3. **Update nginx to route between old and new**
4. **Switch over when ready**

```bash
# Deploy new architecture on different ports
docker compose -f docker-compose-tools.yaml up -d

# Update nginx to route:
# / → Tools Portal (new)
# /dns-by-eye/ → DNS By Eye service (new)
# /legacy/ → Old DNS By Eye (fallback)
```

## Expected Result After Fix

✅ **Tools Portal**: https://tools.apathy.ca/ (working)
✅ **DNS By Eye**: https://tools.apathy.ca/dns-by-eye/ (will work)
✅ **API**: https://tools.apathy.ca/api/tools (will work)

## Verification Commands

```bash
# Test Tools Portal
curl https://tools.apathy.ca/

# Test DNS By Eye (should work after fix)
curl https://tools.apathy.ca/dns-by-eye/

# Test API
curl https://tools.apathy.ca/api/tools
```

## Architecture Comparison

### Before (Single Tool):
```
[Nginx] → [Single DNS By Eye Container]
```

### After (Multi-Tool):
```
[Nginx] → [Tools Portal Container] (/)
       → [DNS By Eye Container] (/dns-by-eye/)
       → [Future Tool Containers] (/tool-name/)
```

The new architecture is ready - it just needs to be deployed to replace the current single-container setup.
