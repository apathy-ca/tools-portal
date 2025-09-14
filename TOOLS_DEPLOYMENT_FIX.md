# Tools Portal Docker IP Binding Fix

## Problem
Docker is trying to bind nginx to the wrong IP address (192.168.14.24 instead of 192.168.14.44).

## Solution
The `generate-compose.py` script supports binding to a specific IP address. You need to regenerate the Docker Compose files with the correct IP.

## Commands to Fix

1. **Stop current containers:**
   ```bash
   cd ~/Software/tools-portal
   sudo docker compose -f docker-compose-tools-ssl.yaml down
   ```

2. **Regenerate compose files with correct IP:**
   ```bash
   python generate-compose.py --bind-ip 192.168.14.44
   ```

3. **Restart with the updated configuration:**
   ```bash
   sudo docker compose -f docker-compose-tools-ssl.yaml up -d
   ```

## What This Does

The `--bind-ip` parameter in `generate-compose.py`:
- Modifies the nginx service port bindings from `"80:80"` to `"192.168.14.44:80:80"`
- Modifies the nginx service port bindings from `"443:443"` to `"192.168.14.44:443:443"`
- This ensures Docker binds nginx specifically to your server's correct IP address

## Verification

After running the commands, verify the fix:
```bash
sudo docker compose -f docker-compose-tools-ssl.yaml ps
```

All containers should show "Running" status without the port binding error.

## Why This Happened

The original `docker-compose-tools-ssl.yaml` was generated without specifying a bind IP, causing Docker to attempt automatic IP selection, which chose the wrong interface.