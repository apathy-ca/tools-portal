#!/usr/bin/env python3
"""
Simple Tools Portal Deployment Script
Automatically detects available tools and provides deployment instructions.
"""

import os
import sys
from pathlib import Path
from dynamic_tools import detect_available_tools, get_tool_categories

def main():
    """Main deployment function."""
    print("🚀 Tools Portal - Dynamic Deployment")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: Please run this script from the tools-portal directory")
        sys.exit(1)
    
    # Detect available tools
    print("🔍 Detecting available tools...")
    tools = detect_available_tools()
    categories = get_tool_categories(tools)
    
    if not tools:
        print("⚠️  No tools detected!")
        print("   Make sure you have tool submodules in the tools/ directory")
        print("   Each tool should have a Dockerfile to be detected")
        return
    
    print(f"\n✅ Detected {len(tools)} tools:")
    for tool_name, config in tools.items():
        print(f"   • {config['name']} ({tool_name}) - {config['description']}")
    
    print(f"\n📂 Categories: {', '.join(categories.keys())}")
    
    print("\n🐋 Docker Deployment:")
    print("   The existing docker compose files will work with detected tools.")
    print("   To deploy all detected tools:")
    print("   ")
    print("   docker compose -f docker compose-tools.yaml up --build")
    print("   ")
    print("   Or with SSL:")
    print("   docker compose -f docker compose-tools-ssl.yaml up --build")
    
    print("\n💡 To add/remove tools:")
    print("   1. Add/remove git submodules in tools/ directory:")
    print("      git submodule add https://github.com/user/tool.git tools/tool-name")
    print("      git submodule deinit tools/tool-name && git rm tools/tool-name")
    print("   ")
    print("   2. Restart the deployment:")
    print("      docker compose -f docker compose-tools.yaml down")
    print("      docker compose -f docker compose-tools.yaml up --build")
    
    print("\n🌐 Access Points (after deployment):")
    print("   • Tools Portal: http://localhost/")
    for tool_name, config in tools.items():
        print(f"   • {config['name']}: http://localhost{config['url']}")
    
    print("\n🏥 Health Monitoring:")
    print("   • Portal Health: http://localhost/health")
    print("   • Detailed Health: http://localhost/api/health/detailed")
    for tool_name in tools.keys():
        print(f"   • {tool_name.title()} Health: http://localhost/{tool_name}/api/health")
    
    print(f"\n📊 Summary:")
    print(f"   • Tools detected: {len(tools)}")
    print(f"   • Categories: {len(categories)}")
    print(f"   • Ready for deployment: ✅")

if __name__ == '__main__':
    main()
