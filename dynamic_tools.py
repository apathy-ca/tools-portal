#!/usr/bin/env python3
"""
Dynamic Tool Detection for Tools Portal
Automatically detects and configures tools based on submodule presence.
"""

import os
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Any

def detect_available_tools() -> Dict[str, Dict[str, Any]]:
    """
    Detect available tools by scanning the tools directory for submodules.
    Returns a dictionary of tool configurations.
    """
    tools_dir = Path("tools")
    detected_tools = {}
    
    if not tools_dir.exists():
        print("⚠️  Tools directory not found")
        return detected_tools
    
    # Scan for tool directories
    for tool_path in tools_dir.iterdir():
        if tool_path.is_dir() and not tool_path.name.startswith('.'):
            tool_name = tool_path.name
            
            # Check if it has a Dockerfile (indicates it's a deployable tool)
            dockerfile_path = tool_path / "Dockerfile"
            if not dockerfile_path.exists():
                continue
            
            # Try to load tool configuration
            tool_config = load_tool_config(tool_name, tool_path)
            if tool_config:
                detected_tools[tool_name] = tool_config
                print(f"✅ Registered tool: {tool_name}")
    
    return detected_tools

def load_tool_config(tool_name: str, tool_path: Path) -> Dict[str, Any]:
    """
    Load configuration for a specific tool.
    First tries to load from tool's config.py, then falls back to defaults.
    """
    # Default configurations for known tools
    default_configs = {
        'dns-by-eye': {
            'name': 'DNS By Eye',
            'description': 'DNS delegation visualizer with health scoring and glue record analysis',
            'version': '1.3.0',
            'url': '/dns-by-eye/',
            'icon': '🔍',
            'category': 'DNS & Networking',
            'status': 'stable',
            'features': [
                'DNS delegation tracing',
                'Visual graph generation',
                'Health score calculation',
                'Glue record validation',
                'Multi-domain comparison',
                'Export capabilities'
            ],
            'tags': ['dns', 'networking', 'visualization', 'debugging']
        },
        'ipwhale': {
            'name': 'IP Whale',
            'description': 'IP address information tool with IPv4/IPv6 detection, PTR records, ASN lookup, and NAT detection',
            'version': '1.0.0',
            'url': '/ipwhale/',
            'icon': '🐋',
            'category': 'DNS & Networking',
            'status': 'stable',
            'features': [
                'IPv4 and IPv6 detection',
                'PTR record lookup',
                'ASN information',
                'NAT detection',
                'Remote port detection',
                'Curl-friendly API endpoints'
            ],
            'tags': ['ip', 'networking', 'asn', 'ptr', 'nat-detection']
        }
    }
    
    # Try to load from tool's config.py
    config_path = tool_path / "config.py"
    tool_config = None
    
    if config_path.exists():
        try:
            spec = importlib.util.spec_from_file_location(f"{tool_name}_config", config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            # Look for TOOL_INFO in the config
            if hasattr(config_module, 'TOOL_INFO'):
                tool_config = config_module.TOOL_INFO
                print(f"📋 Loaded config from {tool_name}/config.py")
        except Exception as e:
            print(f"⚠️  Failed to load config from {tool_name}/config.py: {e}")
    
    # Fall back to default config or generate one
    if not tool_config:
        if tool_name in default_configs:
            tool_config = default_configs[tool_name]
            print(f"📋 Using default config for {tool_name}")
        else:
            # Generate basic config
            tool_config = generate_basic_config(tool_name)
            print(f"📋 Generated basic config for {tool_name}")
    
    return tool_config

def generate_basic_config(tool_name: str) -> Dict[str, Any]:
    """Generate a basic configuration for an unknown tool."""
    return {
        'name': tool_name.replace('-', ' ').replace('_', ' ').title(),
        'description': f'{tool_name} - Automatically detected tool',
        'version': '1.0.0',
        'url': f'/{tool_name}/',
        'icon': '🔧',
        'category': 'Utilities',
        'status': 'detected',
        'features': ['Automatically detected tool'],
        'tags': ['tool', 'utility']
    }

def get_tool_categories(tools: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """Extract and organize tool categories."""
    categories = {}
    
    # Default categories
    default_categories = {
        'DNS & Networking': {
            'icon': '🌐',
            'description': 'Tools for DNS analysis, network diagnostics, and connectivity testing'
        },
        'Security': {
            'icon': '🔒',
            'description': 'Security analysis, vulnerability scanning, and penetration testing tools'
        },
        'System Administration': {
            'icon': '⚙️',
            'description': 'Server management, monitoring, and system diagnostic utilities'
        },
        'Development': {
            'icon': '💻',
            'description': 'Developer tools, code analysis, and debugging utilities'
        },
        'Utilities': {
            'icon': '🔧',
            'description': 'General purpose utilities and helper tools'
        },
        'Gaming & Entertainment': {
            'icon': '🎮',
            'description': 'Gaming tools, character generators, and entertainment utilities'
        }
    }
    
    # Add categories from detected tools
    for tool_config in tools.values():
        category = tool_config.get('category', 'Utilities')
        if category not in categories:
            if category in default_categories:
                categories[category] = default_categories[category]
            else:
                categories[category] = {
                    'icon': '📦',
                    'description': f'{category} tools and utilities'
                }
    
    return categories

def check_tool_health(tool_name: str) -> Dict[str, Any]:
    """
    Check if a tool's health endpoint is responding.
    This can be used for dynamic health monitoring.
    """
    import requests
    
    try:
        response = requests.get(f'http://{tool_name}:5000/api/health', timeout=5)
        return {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds(),
            'status_code': response.status_code
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def generate_nginx_config(tools: List[str]) -> str:
    """Generate nginx configuration for detected tools."""
    config_lines = []
    
    # Add upstream blocks
    for tool in tools:
        config_lines.append(f"""
upstream {tool} {{
    server {tool}:5000;
}}""")
    
    # Add location blocks
    location_blocks = []
    for tool in tools:
        location_blocks.append(f"""
    # {tool.replace('-', ' ').title()} routing
    location /{tool}/ {{
        proxy_pass http://{tool}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Remove /{tool} prefix when forwarding
        rewrite ^/{tool}/(.*)$ /$1 break;
    }}""")
    
    full_config = f"""
# Auto-generated nginx configuration for Tools Portal
{chr(10).join(config_lines)}

upstream tools-portal {{
    server tools-portal:5000;
}}

server {{
    listen 80;
    server_name localhost;
{chr(10).join(location_blocks)}

    # Tools Portal routing (catch-all)
    location / {{
        proxy_pass http://tools-portal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    
    return full_config

def save_detected_tools_info(tools: Dict[str, Dict[str, Any]]) -> None:
    """Save detected tools information to a JSON file for reference."""
    tools_info = {
        'detected_at': str(Path.cwd()),
        'tool_count': len(tools),
        'tools': tools
    }
    
    with open('detected_tools.json', 'w') as f:
        json.dump(tools_info, f, indent=2)
    
    print(f"💾 Saved tool information to detected_tools.json")

if __name__ == '__main__':
    """Test the dynamic tool detection."""
    print("🔍 Testing Dynamic Tool Detection")
    print("=" * 40)
    
    tools = detect_available_tools()
    categories = get_tool_categories(tools)
    
    print(f"\n📊 Summary:")
    print(f"   Detected tools: {len(tools)}")
    print(f"   Categories: {len(categories)}")
    
    if tools:
        print(f"\n🔧 Detected Tools:")
        for tool_name, config in tools.items():
            print(f"   • {config['name']} ({tool_name}) - {config['description']}")
    
    save_detected_tools_info(tools)
