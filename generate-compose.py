#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Docker Compose Generator for Tools Portal
Automatically detects available tool submodules and generates appropriate docker compose configuration.
"""

import os
import sys
import yaml
import json
import argparse
from pathlib import Path
import re

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def read_config_file():
    """Read configuration from .tools-config file."""
    config_file = Path('.tools-config')
    config = {}
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line.startswith('#') or not line:
                        continue
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Warning: Could not read .tools-config file: {e}")
    
    return config

def detect_tools():
    """Detect available tools based on submodule presence."""
    tools_dir = Path("tools")
    detected_tools = []
    
    if not tools_dir.exists():
        print("⚠️  Tools directory not found")
        return detected_tools
    
    # Check for each potential tool
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith('.'):
            # Check if it has a Dockerfile (indicates it's a deployable tool)
            dockerfile_path = tool_path / "Dockerfile"
            if dockerfile_path.exists():
                detected_tools.append(tool_path.name)
                print(f"✅ Detected tool: {tool_path.name}")
            else:
                print(f"⚠️  Directory {tool_path.name} found but no Dockerfile - skipping")
    
    return detected_tools

def get_tool_config(tool_name):
    """Get configuration for a specific tool."""
    configs = {
        'dns-by-eye': {
            'build': {
                'context': './tools/dns-by-eye',
                'dockerfile': 'Dockerfile'
            },
            'container_name': 'dns-by-eye',
            'restart': 'unless-stopped',
            'environment': [
                'FLASK_ENV=production',
                'STATIC_URL_PATH=/dns-by-eye/static'
            ],
            'volumes': [
                './tools/dns-by-eye/app/static/generated:/app/app/static/generated'
            ],
            'networks': ['tools-network'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', 'http://localhost:5000/api/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        },
        'ipwhale': {
            'build': {
                'context': './tools/ipwhale',
                'dockerfile': 'Dockerfile'
            },
            'container_name': 'ipwhale',
            'restart': 'unless-stopped',
            'environment': [
                'FLASK_ENV=production',
                'STATIC_URL_PATH=/ipwhale/static'
            ],
            'networks': ['tools-network'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', 'http://localhost:5000/api/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        },
    }

    return configs.get(tool_name, {
        'build': {
            'context': f'./tools/{tool_name}',
            'dockerfile': 'Dockerfile'
        },
        'container_name': tool_name,
        'restart': 'unless-stopped',
        'environment': [
            'FLASK_ENV=production',
            f'STATIC_URL_PATH=/{tool_name}/static'
        ],
        'networks': ['tools-network'],
        'healthcheck': {
            'test': ['CMD', 'curl', '-f', 'http://localhost:5000/api/health'],
            'interval': '30s',
            'timeout': '10s',
            'retries': 3
        }
    })

def generate_base_services():
    """Generate base services that are always present."""
    # Check if Redis should be exposed externally
    redis_ports = []
    if os.environ.get('REDIS_EXPOSE_PORT', 'true').lower() == 'true':
        redis_ports = ['${REDIS_EXTERNAL_PORT:-6379}:6379']
    
    return {
        'tools-portal': {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile'
            },
            'container_name': 'tools-portal',
            'restart': 'unless-stopped',
            'environment': [
                'FLASK_ENV=production',
                'REDIS_HOST=redis',
                'REDIS_PORT=6379',
                'REDIS_DB=1'
            ],
            'volumes': [
                './static:/app/static',
                './tools:/app/tools:ro'  # Mount tools directory as read-only for dynamic discovery
            ],
            'networks': ['tools-network'],
            'healthcheck': {
                'test': ['CMD', 'curl', '-f', 'http://localhost:5000/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        },
        'redis': {
            'image': 'redis:7-alpine',
            'container_name': 'tools-redis',
            'restart': 'unless-stopped',
            'command': 'redis-server --appendonly yes',
            'ports': redis_ports,
            'volumes': ['redis_data:/data'],
            'networks': ['tools-network'],
            'healthcheck': {
                'test': ['CMD', 'redis-cli', 'ping'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }
    }

def generate_nginx_service(detected_tools, ssl=False, bind_ip=None):
    """Generate nginx service configuration."""
    depends_on = ['tools-portal'] + detected_tools
    
    # Format port bindings based on whether bind_ip is specified
    if bind_ip:
        http_port = f'{bind_ip}:80:80'
        https_port = f'{bind_ip}:443:443'
    else:
        http_port = '80:80'
        https_port = '443:443'
    
    if ssl:
        return {
            'image': 'nginx:alpine',
            'container_name': 'tools-nginx',
            'restart': 'unless-stopped',
            'ports': [http_port, https_port],
            'volumes': [
                './nginx-tools-ssl.conf:/etc/nginx/nginx.conf:ro',
                './ssl:/etc/nginx/ssl:ro',
                'certbot_conf:/etc/letsencrypt',
                'certbot_www:/var/www/certbot'
            ],
            'depends_on': depends_on,
            'networks': ['tools-network'],
            'command': '/bin/sh -c "while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g \'daemon off;\'"',
            'healthcheck': {
                'test': ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }
    else:
        return {
            'image': 'nginx:alpine',
            'container_name': 'tools-nginx',
            'restart': 'unless-stopped',
            'ports': [http_port],
            'volumes': ['./nginx-tools.conf:/etc/nginx/conf.d/default.conf:ro'],
            'depends_on': depends_on,
            'networks': ['tools-network'],
            'healthcheck': {
                'test': ['CMD', 'wget', '--quiet', '--tries=1', '--spider', 'http://localhost/health'],
                'interval': '30s',
                'timeout': '10s',
                'retries': 3
            }
        }

def generate_cleanup_service(detected_tools):
    """Generate cleanup service for tools that need it."""
    cleanup_volumes = []
    cleanup_commands = []
    
    for tool in detected_tools:
        if tool == 'dns-by-eye':
            cleanup_volumes.append('./tools/dns-by-eye/app/static/generated:/cleanup/dns-by-eye')
            cleanup_commands.extend([
                'find /cleanup/dns-by-eye -name "*.png" -type f -mtime +7 -delete 2>/dev/null || true',
                'find /cleanup/dns-by-eye -name "*.svg" -type f -mtime +7 -delete 2>/dev/null || true'
            ])
    
    if not cleanup_volumes:
        return None
    
    command = f'''sh -c '
        while true; do
          echo "Cleaning up generated files older than 7 days..."
          {"; ".join(cleanup_commands)}
          echo "Cleanup completed. Sleeping for 24 hours..."
          sleep 86400
        done
      ' '''
    
    return {
        'image': 'alpine:latest',
        'container_name': 'tools-cleanup',
        'restart': 'unless-stopped',
        'volumes': cleanup_volumes,
        'command': command,
        'networks': ['tools-network']
    }

def generate_ssl_services():
    """Generate SSL-related services."""
    return {
        'certbot': {
            'image': 'certbot/certbot',
            'container_name': 'tools-certbot',
            'restart': 'unless-stopped',
            'volumes': [
                'certbot_conf:/etc/letsencrypt',
                'certbot_www:/var/www/certbot'
            ],
            'networks': ['tools-network'],
            'entrypoint': '"/bin/sh"',
            'command': '''
              -c "
                while true; do
                  echo 'Certbot renewal check...'
                  certbot renew --quiet --no-self-upgrade
                  echo 'Next renewal check in 12 hours...'
                  sleep 43200
                done
              "
            '''
        }
    }

def generate_compose_file(ssl=False, bind_ip=None):
    """Generate complete docker compose configuration."""
    print(f"🔧 Generating docker compose configuration (SSL: {ssl}, Bind IP: {bind_ip or 'all interfaces'})...")
    
    detected_tools = detect_tools()
    
    if not detected_tools:
        print("⚠️  No tools detected - generating minimal configuration")
    
    # Start with base configuration
    compose = {
        'services': generate_base_services()
    }
    
    # Add detected tools
    for tool in detected_tools:
        compose['services'][tool] = get_tool_config(tool)
    
    # Add nginx
    compose['services']['nginx'] = generate_nginx_service(detected_tools, ssl, bind_ip)
    
    # Add cleanup service if needed
    cleanup_service = generate_cleanup_service(detected_tools)
    if cleanup_service:
        compose['services']['cleanup'] = cleanup_service
    
    # Add SSL services if needed
    if ssl:
        compose['services'].update(generate_ssl_services())
    
    # Add volumes
    volumes = ['redis_data']
    if ssl:
        volumes.extend(['certbot_conf', 'certbot_www'])
    
    compose['volumes'] = {vol: None for vol in volumes}
    
    # Add networks
    compose['networks'] = {
        'tools-network': {
            'driver': 'bridge'
        }
    }
    
    return compose

def detect_ssl_domain():
    """Detect existing SSL domain from nginx config or certificates."""
    # Check if nginx config exists and extract domain
    if os.path.exists('nginx-tools-ssl.conf'):
        try:
            with open('nginx-tools-ssl.conf', 'r') as f:
                content = f.read()
                # Look for server_name directive
                import re
                match = re.search(r'server_name\s+([^;]+);', content)
                if match:
                    domain = match.group(1).strip()
                    if domain != 'localhost' and domain != 'your-domain.com' and domain != '_':
                        print(f"🔍 Detected existing SSL domain: {domain}")
                        return domain
        except Exception as e:
            print(f"⚠️  Could not read existing nginx config: {e}")
    
    # Check for existing SSL certificates
    try:
        import subprocess
        result = subprocess.run(['docker', 'compose', '-f', 'docker-compose-tools-ssl.yaml', 'run', '--rm', '--entrypoint=', 'certbot', 'ls', '/etc/letsencrypt/live/'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line and not line.startswith('README') and '.' in line:
                    print(f"🔍 Detected existing SSL certificate for: {line}")
                    return line
    except Exception as e:
        print(f"⚠️  Could not check existing certificates: {e}")
    
    return None

def generate_nginx_config(detected_tools, ssl=False, domain="localhost"):
    """Generate nginx configuration file."""
    
    # If SSL is enabled, try to detect existing domain configuration
    if ssl and domain in ["localhost", "your-domain.com"]:
        detected_domain = detect_ssl_domain()
        if detected_domain:
            domain = detected_domain
            print(f"✅ Using detected SSL domain: {domain}")
        else:
            print(f"⚠️  No existing SSL domain detected, using placeholder: {domain}")
    
    # Base nginx config
    config = f"""events {{
    worker_connections 1024;
}}

http {{
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;

    # Upstream servers
    upstream tools-portal {{
        server tools-portal:5000;
    }}
"""

    # Add upstream blocks for detected tools
    for tool in detected_tools:
        config += f"""
    upstream {tool} {{
        server {tool}:5000;
    }}
"""

    if ssl:
        # HTTP to HTTPS redirect
        config += f"""
    # HTTP to HTTPS redirect
    server {{
        listen 80;
        server_name {domain};
        
        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {{
            root /var/www/certbot;
        }}

        # Redirect all other traffic to HTTPS
        location / {{
            return 301 https://$server_name$request_uri;
        }}
    }}

    # HTTPS server
    server {{
        listen 443 ssl http2;
        server_name {domain};

        # SSL configuration
        ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
        
        # SSL security settings
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
"""
    else:
        # HTTP only server
        config += f"""
    # HTTP server
    server {{
        listen 80;
        server_name {domain};
"""

    # Main tools portal location
    config += """
        # Main tools portal
        location / {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Port $server_port;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
"""

    # Add location blocks for detected tools
    for tool in detected_tools:
        # Enhanced configuration for ALL tools with TCP session tracking
        config += f"""
        # {tool.replace('-', ' ').title()} tool - Enhanced with TCP session tracking
        location /{tool}/ {{
            limit_req zone={"api" if tool == "ipwhale" else "general"} burst=20 nodelay;
            proxy_pass http://{tool}/;
            proxy_set_header Host $host;
            
            # Standard proxy headers
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Port $server_port;
            
            # TCP session information (sanitized for security)
            proxy_set_header X-Client-IP $remote_addr;
            # Removed X-Client-Port, X-Server-IP, X-Server-Port, X-Connection-ID for security
            
            # Additional connection details (available to all tools)
            proxy_set_header X-Request-ID $request_id;
            proxy_set_header X-Nginx-Proxy "true";
            proxy_set_header X-Original-URI $request_uri;
            proxy_set_header X-Original-Method $request_method;
            
            # Connection settings
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            {"proxy_buffering off;" if tool == "ipwhale" else ""}
            {"proxy_request_buffering off;" if tool == "ipwhale" else ""}
        }}
"""

    # Common location blocks
    config += """
        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=5 nodelay;
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Port $server_port;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            access_log off;
        }

        # Static files for tools portal
        location /static/ {
            proxy_pass http://tools-portal;
            proxy_set_header Host $host;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
"""

    if ssl:
        config += """
        # Let's Encrypt challenge
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
"""

    config += """    }
}
"""

    return config

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Dynamic Docker Compose Generator for Tools Portal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate-compose.py                           # Generate for all interfaces
  python generate-compose.py --bind-ip 192.168.1.100  # Bind to specific IP
  python generate-compose.py --bind-ip 10.0.0.50      # Bind to virtual IP
        """
    )
    
    parser.add_argument(
        '--bind-ip',
        type=str,
        help='Specific IP address to bind the services to (e.g., 192.168.1.100). '
             'If not specified, services will bind to all interfaces (0.0.0.0).'
    )
    
    args = parser.parse_args()
    
    print("🐋 Tools Portal - Dynamic Docker Compose Generator")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: Please run this script from the tools-portal directory")
        sys.exit(1)
    
    # Read config file
    config = read_config_file()
    
    # Use bind_ip from command line, or fall back to config file
    bind_ip = args.bind_ip
    if not bind_ip and 'BIND_IP' in config:
        bind_ip = config['BIND_IP']
        print(f"📁 Using bind IP from config file: {bind_ip}")
    
    # Validate IP address if provided
    if bind_ip:
        import ipaddress
        try:
            ipaddress.ip_address(bind_ip)
            if args.bind_ip:
                print(f"🔗 Binding services to IP (from command line): {bind_ip}")
            else:
                print(f"🔗 Binding services to IP (from config): {bind_ip}")
        except ValueError:
            print(f"❌ Error: Invalid IP address '{bind_ip}'")
            sys.exit(1)
    else:
        print("🔗 Binding services to all interfaces (0.0.0.0)")
        print("💡 Tip: Set BIND_IP in .tools-config or use --bind-ip to bind to a specific IP")
    
    detected_tools = detect_tools()
    
    # Generate both configurations
    for ssl in [False, True]:
        suffix = '-ssl' if ssl else ''
        compose_filename = f'docker-compose-tools{suffix}.yaml'
        nginx_filename = f'nginx-tools{suffix}.conf'
        
        # Generate docker compose file
        compose_config = generate_compose_file(ssl, bind_ip)
        with open(compose_filename, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Generated {compose_filename}")
        
        # Generate nginx config file
        # Use a default domain - this should be updated by deployment scripts
        default_domain = "localhost" if not ssl else "your-domain.com"
        nginx_config = generate_nginx_config(detected_tools, ssl, default_domain)
        with open(nginx_filename, 'w') as f:
            f.write(nginx_config)
        print(f"✅ Generated {nginx_filename}")
    
    print("\n🎉 Docker Compose and Nginx files generated successfully!")
    
    if bind_ip:
        print(f"\n🔗 Services configured to bind to: {bind_ip}")
        print(f"   Access your tools at: http://{bind_ip}/")
    else:
        print("\n🔗 Services configured to bind to all interfaces")
        print("   Access your tools at: http://localhost/ or http://YOUR_IP/")
    
    print("\n📋 Usage:")
    print("   Standard:  docker compose -f docker-compose-tools.yaml up --build")
    print("   With SSL:  docker compose -f docker-compose-tools-ssl.yaml up --build")
    print("\n💡 To avoid port conflicts:")
    print("   Use --bind-ip to bind to a specific IP (e.g., --bind-ip 192.168.14.100)")
    print("   This prevents conflicts with other services on the same ports")
    print("\n⚠️  Important:")
    print("   - Update nginx-tools-ssl.conf with your actual domain name")
    print("   - Ensure SSL certificates are properly configured")
    print("\n💡 To add/remove tools:")
    print("   1. Add/remove git submodules in tools/ directory")
    print("   2. Run this script to regenerate compose and nginx files")
    print("   3. Restart with docker compose")

if __name__ == '__main__':
    main()
