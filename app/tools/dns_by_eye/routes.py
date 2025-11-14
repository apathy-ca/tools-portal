"""
DNS By Eye - Routes
Flask blueprint routes for DNS By Eye tool.

Note: This is a wrapper that integrates the existing DNS By Eye Flask app
into the Tools Portal v2 plugin architecture. For a full rewrite, we would
refactor all the code from tools/dns-by-eye/app/main.py into this module.
"""
from flask import render_template, jsonify, request, current_app
from datetime import datetime
import sys
from pathlib import Path

from . import blueprint

# Add the DNS By Eye directory to Python path so we can import its modules
dns_by_eye_path = Path(__file__).parent.parent.parent.parent / 'tools' / 'dns-by-eye'
if str(dns_by_eye_path) not in sys.path:
    sys.path.insert(0, str(dns_by_eye_path))

# Import DNS By Eye core functionality
try:
    from app.main import (
        trace_delegation,
        check_glue_records,
        test_last_level_ns_references,
        is_valid_domain
    )
    dns_by_eye_available = True
except Exception as e:
    current_app.logger.error(f"Failed to import DNS By Eye modules: {e}")
    dns_by_eye_available = False


@blueprint.route('/')
def index():
    """DNS By Eye main page."""
    if not dns_by_eye_available:
        return "DNS By Eye module not available", 503
    return render_template('index.html')


@blueprint.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy' if dns_by_eye_available else 'unhealthy',
        'service': 'dns-by-eye',
        'version': '1.3.1',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@blueprint.route('/api/trace/<domain>')
def trace(domain):
    """Simple DNS trace for a domain."""
    if not dns_by_eye_available:
        return jsonify({'error': 'Service unavailable'}), 503

    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain'}), 400

    try:
        trace_data = trace_delegation(domain, verbose=True)
        return jsonify({
            'domain': domain,
            'trace': trace_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@blueprint.route('/api/delegation', methods=['POST'])
def delegation():
    """
    Full delegation analysis endpoint.

    Note: For v2, this is a simplified version. Full functionality
    is available in the original DNS By Eye tool.
    """
    if not dns_by_eye_available:
        return jsonify({'error': 'Service unavailable'}), 503

    data = request.get_json()
    domain = data.get('domain', '').strip()

    if not domain or not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain'}), 400

    try:
        # Perform DNS delegation analysis
        trace_data = trace_delegation(domain, verbose=True, debug=True)
        glue_data = check_glue_records(domain)

        return jsonify({
            'domain': domain,
            'trace': trace_data,
            'glue_records': glue_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        current_app.logger.error(f"Delegation analysis failed: {e}")
        return jsonify({'error': str(e)}), 500


# Note: For a complete v2 integration, we would need to port all routes:
# - /api/compare
# - /api/export/<domain>
# - /api/nameservers/<domain>
# - /api/debug
# - etc.
#
# For now, this provides basic functionality while we complete the v2 architecture.
