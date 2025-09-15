# Bind IP Configuration for Tools Portal

## Problem

The `generate-compose.py` script was overwriting bind-ip settings with a default IP address every time it was run, causing configuration to be lost.

## Solution

The script has been enhanced to preserve bind-ip settings using a configuration file system.

## Configuration Methods

### Method 1: Using Configuration File (Recommended)

1. **Edit the `.tools-config` file** in the tools-portal directory:

```bash
# Tools Portal Configuration
# This file preserves settings between generate-compose.py runs

# Bind IP setting - uncomment and set your preferred IP
BIND_IP=192.168.1.100

# Example configurations:
# BIND_IP=10.0.0.50      # For virtual IP
# BIND_IP=192.168.1.100  # For specific network interface
# BIND_IP=127.0.0.1      # For localhost only
# Leave commented for all interfaces (0.0.0.0)
```

2. **Set your desired IP address**:
```bash
BIND_IP=YOUR_DESIRED_IP_HERE
```

3. **Run the script normally**:
```bash
python generate-compose.py
```

The script will automatically use the IP from the config file.

### Method 2: Command Line Override

You can override the config file setting using the command line:

```bash
python generate-compose.py --bind-ip 192.168.1.100
```

## Priority Order

The script uses this priority order for bind-ip settings:

1. **Command line argument** (`--bind-ip`) - highest priority
2. **Configuration file** (`.tools-config` with `BIND_IP=...`)
3. **Default** (all interfaces 0.0.0.0) - lowest priority

## Example Usage

### To avoid 192.168.14.24 being used:

1. **Set your preferred IP in `.tools-config`**:
```bash
BIND_IP=192.168.1.50
```

2. **Run the script**:
```bash
python generate-compose.py
```

3. **Verify the output**:
```
📁 Using bind IP from config file: 192.168.1.50
🔗 Binding services to IP (from config): 192.168.1.50
✅ Generated docker-compose-tools.yaml
✅ Generated docker-compose-tools-ssl.yaml

🔗 Services configured to bind to: 192.168.1.50
   Access your tools at: http://192.168.1.50/
```

### Generated Docker Compose Output

With bind IP configured, the nginx service will have:

```yaml
nginx:
  image: nginx:alpine
  container_name: tools-nginx
  restart: unless-stopped
  ports:
    - "192.168.1.50:80:80"     # Instead of just "80:80"
    - "192.168.1.50:443:443"   # For SSL version
```

## Benefits

- **Persistent configuration**: Your bind-ip setting is preserved across script runs
- **No more overwrites**: The script respects your configured IP
- **Flexible overrides**: Command line can still override when needed
- **Clear feedback**: The script tells you which IP source is being used

## Troubleshooting

### If the script ignores your config:

1. **Check the file format**:
   - Ensure no spaces around the `=` sign
   - Use format: `BIND_IP=192.168.1.100`
   - No quotes needed around the IP

2. **Check the file location**:
   - The `.tools-config` file must be in the `tools-portal` directory
   - Run the script from the `tools-portal` directory

3. **Verify IP format**:
   - Use valid IPv4 format: `192.168.1.100`
   - Script will validate and show error for invalid IPs

### If you see the old behavior:

Run this to regenerate with your preferred IP:
```bash
echo "BIND_IP=YOUR_IP_HERE" >> .tools-config
python generate-compose.py
```

## Configuration File Format

The `.tools-config` file supports:
- Comments (lines starting with `#`)
- Key-value pairs in `KEY=VALUE` format
- Blank lines (ignored)

Currently supported settings:
- `BIND_IP` - IP address to bind services to

Future settings can be added to this file as needed.