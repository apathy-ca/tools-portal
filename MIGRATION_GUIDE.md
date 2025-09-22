# Migration Guide: Generated Files Cleanup

## Issue
If you encounter this error when pulling updates:

```
error: Your local changes to the following files would be overwritten by merge:
        docker-compose-tools-ssl.yaml
        docker-compose-tools.yaml
Please commit your changes or stash them before you merge.
```

## Root Cause
These files were previously tracked in git but are now generated locally to prevent deployment conflicts. Your local repository still has the old tracked versions.

## Solution

### Option 1: Clean Reset (Recommended)
```bash
cd tools-portal
git reset --hard HEAD
git clean -fd
git pull
```

### Option 2: Manual Cleanup
```bash
cd tools-portal
git rm --cached docker-compose-tools.yaml docker-compose-tools-ssl.yaml 2>/dev/null || true
git rm --cached nginx-tools.conf nginx-tools-ssl.conf 2>/dev/null || true
rm -f docker-compose-tools*.yaml nginx-tools*.conf
git pull
```

### Option 3: Fresh Clone
```bash
# Backup any local changes first
cd ..
git clone --recurse-submodules https://github.com/apathy-ca/tools-portal.git tools-portal-new
cd tools-portal-new
```

## After Migration

1. **Generate configuration files**:
   ```bash
   py generate-compose.py
   ```

2. **Deploy as usual**:
   ```bash
   docker compose -f docker-compose-tools.yaml up -d
   ```

## What Changed

- **Before**: Docker-compose and nginx files were tracked in git
- **After**: These files are generated locally based on available tools
- **Benefit**: No more conflicts between different deployments

## Generated Files (Not in Git)
- `docker-compose-tools.yaml`
- `docker-compose-tools-ssl.yaml`
- `nginx-tools.conf`
- `nginx-tools-ssl.conf`

These files are automatically created by `generate-compose.py` and should not be committed to git.