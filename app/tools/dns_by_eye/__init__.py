"""
DNS By Eye - Tool Plugin
DNS delegation visualization and analysis tool.
"""
from flask import Blueprint

# Create blueprint
blueprint = Blueprint(
    'dns_by_eye',
    __name__,
    template_folder='../../../../tools/dns-by-eye/app/templates',
    static_folder='../../../../tools/dns-by-eye/app/static',
    static_url_path='/static'
)

# Tool metadata
TOOL_INFO = {
    'name': 'DNS By Eye',
    'description': 'DNS delegation visualization with health scoring and glue record analysis',
    'version': '1.3.1',
    'icon': '🔍',
    'category': 'DNS & Networking',
    'status': 'stable',
    'features': [
        'DNS delegation tracing',
        'Visual graph generation',
        'Health score calculation',
        'Glue record validation',
        'Multi-domain comparison',
        'Export capabilities (JSON, CSV)'
    ],
    'tags': ['dns', 'networking', 'visualization', 'debugging', 'nameservers']
}

# Import routes
from . import routes
