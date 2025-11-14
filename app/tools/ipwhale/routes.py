"""
IP Whale - Routes
Flask blueprint routes for IP Whale tool.
"""
from flask import render_template, jsonify, request, current_app, make_response
from datetime import datetime
import sys
from pathlib import Path

from . import blueprint

# Add IP Whale directory to Python path
ipwhale_path = Path(__file__).parent.parent.parent.parent / 'tools' / 'ipwhale'
if str(ipwhale_path) not in sys.path:
    sys.path.insert(0, str(ipwhale_path))

# Import IP Whale core functionality
try:
    from app.main import (
        get_client_ip,
        get_client_info,
        lookup_ptr,
        lookup_asn,
        is_valid_ipv4,
        is_valid_ipv6
    )
    ipwhale_available = True
except Exception as e:
    current_app.logger.error(f"Failed to import IP Whale modules: {e}")
    ipwhale_available = False


@blueprint.route('/')
def index():
    """IP Whale main page."""
    if not ipwhale_available:
        return "IP Whale module not available", 503

    # Get client info
    client_info = get_client_info()
    return render_template('index.html', **client_info)


@blueprint.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy' if ipwhale_available else 'unhealthy',
        'service': 'ipwhale',
        'version': '1.0.1',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@blueprint.route('/api/ip')
def api_ip():
    """Get client IP information (JSON)."""
    if not ipwhale_available:
        return jsonify({'error': 'Service unavailable'}), 503

    client_ip = get_client_ip()
    return jsonify({
        'ip': client_ip,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@blueprint.route('/api/full')
def api_full():
    """Get full client information including NAT detection."""
    if not ipwhale_available:
        return jsonify({'error': 'Service unavailable'}), 503

    info = get_client_info()
    return jsonify({
        **info,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


@blueprint.route('/api/4/ip')
def api_ipv4():
    """Get IPv4 address (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv4(client_ip):
        return client_ip
    return "No IPv4 address detected", 404


@blueprint.route('/api/6/ip')
def api_ipv6():
    """Get IPv6 address (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv6(client_ip):
        return client_ip
    return "No IPv6 address detected", 404


@blueprint.route('/api/4/ptr')
def api_ipv4_ptr():
    """Get IPv4 PTR record (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv4(client_ip):
        ptr = lookup_ptr(client_ip)
        return ptr if ptr != 'N/A' else "No PTR record found", (200 if ptr != 'N/A' else 404)
    return "No IPv4 address detected", 404


@blueprint.route('/api/6/ptr')
def api_ipv6_ptr():
    """Get IPv6 PTR record (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv6(client_ip):
        ptr = lookup_ptr(client_ip)
        return ptr if ptr != 'N/A' else "No PTR record found", (200 if ptr != 'N/A' else 404)
    return "No IPv6 address detected", 404


@blueprint.route('/api/4/asn')
def api_ipv4_asn():
    """Get IPv4 ASN information (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv4(client_ip):
        asn_info = lookup_asn(client_ip, version=4)
        if asn_info and asn_info != 'N/A':
            return asn_info
        return "No ASN information found", 404
    return "No IPv4 address detected", 404


@blueprint.route('/api/6/asn')
def api_ipv6_asn():
    """Get IPv6 ASN information (text for curl)."""
    if not ipwhale_available:
        return "Service unavailable", 503

    client_ip = get_client_ip()
    if is_valid_ipv6(client_ip):
        asn_info = lookup_asn(client_ip, version=6)
        if asn_info and asn_info != 'N/A':
            return asn_info
        return "No ASN information found", 404
    return "No IPv6 address detected", 404
