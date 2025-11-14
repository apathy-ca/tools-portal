"""
IP Whale - Tool Plugin
IP address information with IPv4/IPv6, PTR, ASN, and NAT detection.
"""
from flask import Blueprint

# Create blueprint
blueprint = Blueprint(
    'ipwhale',
    __name__,
    template_folder='../../../../tools/ipwhale/app/templates',
    static_folder='../../../../tools/ipwhale/app/static',
    static_url_path='/static'
)

# Tool metadata
TOOL_INFO = {
    'name': 'IP Whale',
    'description': 'IP address information with IPv4/IPv6 detection, PTR records, ASN lookup, and NAT detection',
    'version': '1.0.1',
    'icon': '🐋',
    'category': 'DNS & Networking',
    'status': 'stable',
    'features': [
        'IPv4 and IPv6 detection',
        'PTR (reverse DNS) record lookup',
        'ASN (Autonomous System Number) information',
        'NAT/proxy detection',
        'Remote port detection',
        'Curl-friendly text endpoints',
        'JSON API for programmatic access'
    ],
    'tags': ['ip', 'networking', 'asn', 'ptr', 'nat-detection', 'ipv4', 'ipv6']
}

# Import routes
from . import routes
