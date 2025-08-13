#!/usr/bin/env python3
"""
Dynamic Docker Compose Generator for Tools Portal
Automatically detects available tool submodules and generates appropriate docker-compose configuration.
"""

import os
import sys
import yaml
import json
from pathlib import Path

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
        }
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
    return {
        'tools-portal': {
            'build': {
                'context': '.',
                'dockerfile': 'Dockerfile'
            },
            'container_name': 'tools-portal',
            'restart': 'unless-stopped',
            'environment': ['FLASK_ENV=production'],
            'volumes': ['./static:/app/static'],
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

def generate_nginx_service(detected_tools, ssl=False):
    """Generate nginx service configuration."""
    depends_on = ['tools-portal'] + detected_tools
    
    if ssl:
        return {
            'image': 'nginx:alpine',
            'container_name': 'tools-nginx',
            'restart': 'unless-stopped',
            'ports': ['80:80', '443:443'],
            'volumes': [
                './nginx-tools-ssl.conf:/etc/nginx/nginx.conf:ro',
                './ssl:/etc/nginx/ssl:ro',
                'certbot_conf:/etc/letsencrypt',
                'certbot_www:/var/www/certbot'
            ],
            'depends_on': depends_on,
            'networks': ['tools-network'],
            'command': '"/bin/sh -c \'while :; do sleep 6h & wait $${!}; nginx -s reload; done & nginx -g "daemon off;"\'"',
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
            'ports': ['80:80'],
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

def generate_compose_file(ssl=False):
    """Generate complete docker-compose configuration."""
    print(f"🔧 Generating docker-compose configuration (SSL: {ssl})...")
    
    detected_tools = detect_tools()
    
    if not detected_tools:
        print("⚠️  No tools detected - generating minimal configuration")
    
    # Start with base configuration
    compose = {
        'version': '3.8',
        'services': generate_base_services()
    }
    
    # Add detected tools
    for tool in detected_tools:
        compose['services'][tool] = get_tool_config(tool)
    
    # Add nginx
    compose['services']['nginx'] = generate_nginx_service(detected_tools, ssl)
    
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

def main():
    """Main function."""
    print("🐋 Tools Portal - Dynamic Docker Compose Generator")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: Please run this script from the tools-portal directory")
        sys.exit(1)
    
    # Generate both configurations
    for ssl in [False, True]:
        suffix = '-ssl' if ssl else ''
        filename = f'docker-compose-tools{suffix}.yaml'
        
        compose_config = generate_compose_file(ssl)
        
        # Write the file
        with open(filename, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Generated {filename}")
    
    print("\n🎉 Docker Compose files generated successfully!")
    print("\n📋 Usage:")
    print("   Standard:  docker-compose -f docker-compose-tools.yaml up --build")
    print("   With SSL:  docker-compose -f docker-compose-tools-ssl.yaml up --build")
    print("\n💡 To add/remove tools:")
    print("   1. Add/remove git submodules in tools/ directory")
    print("   2. Run this script to regenerate compose files")
    print("   3. Restart with docker-compose")

if __name__ == '__main__':
    main()
