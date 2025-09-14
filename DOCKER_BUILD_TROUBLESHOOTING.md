# Docker Build Troubleshooting Guide

## Current Issue: Setup-SSL Script Stuck in Build Loop

The `setup-ssl.sh` script appears to be stuck in a very long Docker build process, which is likely due to:

1. **Large dependency installation** - Multiple containers installing packages simultaneously
2. **Network congestion** - Downloading packages from Debian repositories
3. **Resource constraints** - Multiple builds competing for CPU/memory

## Immediate Solutions

### Option 1: Cancel and Use Non-SSL Build First
```bash
# Press Ctrl+C to cancel the current build
^C

# Use the regular (non-SSL) build first to test everything works
cd ~/Software/tools-portal
python generate-compose.py --bind-ip 192.168.14.44
sudo docker compose -f docker-compose-tools.yaml up -d

# Test if tools are working at http://192.168.14.44/
# Once confirmed working, then try SSL setup
```

### Option 2: Use Pre-built Images (if available)
```bash
# Pull pre-built images to avoid building from scratch
sudo docker compose -f docker-compose-tools-ssl.yaml pull || true

# Then try the build again
sudo docker compose -f docker-compose-tools-ssl.yaml up -d
```

### Option 3: Build One Service at a Time
```bash
# Build services individually to avoid resource contention
sudo docker compose -f docker-compose-tools-ssl.yaml build tools-portal
sudo docker compose -f docker-compose-tools-ssl.yaml build dns-by-eye
sudo docker compose -f docker-compose-tools-ssl.yaml build ipwhale
sudo docker compose -f docker-compose-tools-ssl.yaml build dnd-character-generator

# Then start all services
sudo docker compose -f docker-compose-tools-ssl.yaml up -d
```

## Why This Happens

1. **Multiple simultaneous builds** - 4+ containers building at once
2. **Package installation** - Each container installing curl, graphviz, and other dependencies
3. **Network bottleneck** - All containers downloading from Debian repos simultaneously
4. **Resource competition** - CPU and memory contention during builds

## Prevention for Future Builds

### 1. Use Docker BuildKit (faster builds)
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

### 2. Limit concurrent builds
```bash
# Build with limited parallelism
sudo docker compose -f docker-compose-tools-ssl.yaml up -d --build --parallel 2
```

### 3. Use .dockerignore files
Each tool should have a `.dockerignore` file to exclude unnecessary files from build context.

## Quick Test Commands

After any successful deployment:

```bash
# Test portal
curl -s http://192.168.14.44/health | jq

# Test DNS By Eye
curl -s http://192.168.14.44/dns-by-eye/api/health | jq

# Test IP Whale
curl -s http://192.168.14.44/ipwhale/api/health | jq

# Check all containers
sudo docker compose -f docker-compose-tools-ssl.yaml ps
```

## Recommendation

1. **Cancel the current build** (Ctrl+C)
2. **Try the non-SSL version first** to confirm the IP binding fix works
3. **Once confirmed working**, attempt SSL setup with one of the optimized approaches above

The IP binding issue should be resolved with the `--bind-ip 192.168.14.44` parameter regardless of whether you use SSL or not.