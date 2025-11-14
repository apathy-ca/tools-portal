"""
Tools Portal v2 - Plugin Discovery
Auto-discovers and registers tool blueprints.
"""
import importlib
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def discover_tools(app):
    """
    Auto-discover and register tool plugins.

    Scans the app/tools/ directory for tool modules and registers
    their blueprints automatically. Each tool should have:
    - __init__.py with TOOL_INFO dict and blueprint object
    - routes.py for defining routes

    Args:
        app: Flask application instance

    Returns:
        dict: Dictionary of discovered tools {tool_name: TOOL_INFO}
    """
    tools = {}
    tools_dir = Path(__file__).parent

    logger.info(f"Scanning for tools in: {tools_dir}")

    for item in tools_dir.iterdir():
        # Skip private directories and __pycache__
        if not item.is_dir() or item.name.startswith('_'):
            continue

        tool_name = item.name

        try:
            # Import the tool module
            tool_module = importlib.import_module(f'app.tools.{tool_name}')

            # Check for required attributes
            if not hasattr(tool_module, 'TOOL_INFO'):
                logger.warning(f"Tool '{tool_name}' missing TOOL_INFO - skipping")
                continue

            if not hasattr(tool_module, 'blueprint'):
                logger.warning(f"Tool '{tool_name}' missing blueprint - skipping")
                continue

            # Register the blueprint
            url_prefix = f'/{tool_name}'
            app.register_blueprint(tool_module.blueprint, url_prefix=url_prefix)

            # Store tool info
            tool_info = tool_module.TOOL_INFO.copy()
            tool_info['url'] = url_prefix
            tools[tool_name] = tool_info

            logger.info(f"✓ Registered tool: {tool_name} at {url_prefix}")

        except Exception as e:
            logger.error(f"✗ Failed to load tool '{tool_name}': {e}")
            continue

    logger.info(f"Discovered {len(tools)} tools")
    return tools


def get_tool_categories(tools: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """
    Extract unique categories from tools.

    Args:
        tools: Dictionary of tools

    Returns:
        dict: Category information
    """
    categories = {}

    # Default category metadata
    default_categories = {
        'DNS & Networking': {
            'icon': '🌐',
            'description': 'DNS analysis, network diagnostics, and connectivity tools'
        },
        'Security': {
            'icon': '🔒',
            'description': 'Security analysis and scanning tools'
        },
        'Utilities': {
            'icon': '🔧',
            'description': 'General purpose utilities'
        },
        'System': {
            'icon': '⚙️',
            'description': 'System administration and monitoring'
        },
    }

    # Collect categories from tools
    for tool_info in tools.values():
        category = tool_info.get('category', 'Utilities')
        if category not in categories:
            categories[category] = default_categories.get(category, {
                'icon': '📦',
                'description': f'{category} tools'
            })

    return categories
