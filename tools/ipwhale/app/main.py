# -*- coding: utf-8 -*-
"""
IPWhale - IP Address Information Tool
Inspired by ipquail.com and ipchicken.com functionality
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, make_response
import socket
import dns.resolver
import dns.reversename
import re
import time
import json
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import traceback
import os
from config import Config

# Enhanced error classes
class IPWhaleError(Exception):
    """Base class for IPWhale-related errors"""
    pass

class DNSLookupError(IPWhaleError):
    """DNS lookup failed"""
    pass

class ASNLookupError(IPWhaleError):
    """ASN lookup failed"""
    pass

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except DNSLookupError as e:
            app.logger.warning(f"DNS lookup failed for {request.url}: {str(e)}")
            return jsonify({
                'error': 'DNS_LOOKUP_FAILED',
                'message': 'DNS lookup failed',
                'details': str(e)
            }), 502
        except ASNLookupError as e:
            app.logger.warning(f"ASN lookup failed for {request.url}: {str(e)}")
            return jsonify({
                'error': 'ASN_LOOKUP_FAILED',
                'message': 'ASN lookup failed',
                'details': str(e)
            }), 502
        except Exception as e:
            app.logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'error': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'request_id': request.headers.get('X-Request-ID', 'unknown')
            }), 500
    return decorated_function

# Configure static URL path based on environment
static_url_path = os.environ.get('STATIC_URL_PATH', '/static')
app = Flask(__name__, static_folder="static", static_url_path=static_url_path)
app.config.from_object(Config)

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        delay=True
    )
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    app.logger.info('IPWhale startup')

# Configure DNS resolver
resolver = dns.resolver.Resolver()
resolver.timeout = Config.DNS_TIMEOUT
resolver.lifetime = Config.DNS_LIFETIME

# Input validation constants
IPV4_REGEX = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
IPV6_REGEX = re.compile(r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$')

def is_valid_ipv4(ip):
    """Validate IPv4 address format."""
    return bool(IPV4_REGEX.match(ip))

def is_valid_ipv6(ip):
    """Validate IPv6 address format."""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except socket.error:
        return False

def get_client_ip():
    """Get the real client IP address, handling proxies and load balancers."""
    # Check for common proxy headers
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        # Take the first IP in the chain (original client)
        client_ip = forwarded_ips.split(',')[0].strip()
        return client_ip
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to remote_addr
    return request.remote_addr

def get_client_info():
    """Get comprehensive client information including IP, port, and browser details."""
    client_ip = get_client_ip()
    remote_port = request.environ.get('REMOTE_PORT', 'Unknown')
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Detect if we're behind NAT by comparing different IP sources
    remote_addr = request.remote_addr
    forwarded_for = request.headers.get('X-Forwarded-For')
    real_ip = request.headers.get('X-Real-IP')
    
    nat_detected = False
    nat_info = {}
    
    if forwarded_for or real_ip:
        nat_detected = True
        nat_info = {
            'detected': True,
            'remote_addr': remote_addr,
            'forwarded_for': forwarded_for,
            'real_ip': real_ip,
            'explanation': 'Client is behind NAT/proxy - multiple IP addresses detected'
        }
    
    return {
        'ip': client_ip,
        'remote_port': remote_port,
        'user_agent': user_agent,
        'nat_detection': nat_info if nat_detected else {'detected': False}
    }

def lookup_ptr_record(ip):
    """Lookup PTR record for an IP address."""
    try:
        if is_valid_ipv4(ip):
            reverse_name = dns.reversename.from_address(ip)
        elif is_valid_ipv6(ip):
            reverse_name = dns.reversename.from_address(ip)
        else:
            return None
        
        ptr_records = resolver.resolve(reverse_name, 'PTR')
        return [r.to_text().rstrip('.') for r in ptr_records]
    except Exception as e:
        app.logger.debug(f"PTR lookup failed for {ip}: {str(e)}")
        return None

def lookup_asn(ip):
    """Lookup ASN information for an IP address using DNS-based lookups."""
    try:
        if is_valid_ipv4(ip):
            # For IPv4, use origin.asn.cymru.com
            octets = ip.split('.')
            reversed_ip = '.'.join(reversed(octets))
            query_name = f"{reversed_ip}.origin.asn.cymru.com"
        elif is_valid_ipv6(ip):
            # For IPv6, use origin6.asn.cymru.com
            # Convert IPv6 to expanded form and reverse nibbles
            import ipaddress
            ipv6_obj = ipaddress.IPv6Address(ip)
            expanded = ipv6_obj.exploded.replace(':', '')
            reversed_nibbles = '.'.join(reversed(expanded))
            query_name = f"{reversed_nibbles}.origin6.asn.cymru.com"
        else:
            return None
        
        txt_records = resolver.resolve(query_name, 'TXT')
        for record in txt_records:
            # Parse the TXT record: "ASN | IP | BGP Prefix | CC | Registry | Allocated | AS Name"
            parts = record.to_text().strip('"').split(' | ')
            if len(parts) >= 2:
                asn = parts[0].strip()
                return asn if asn and asn != '0' else None
        
        return None
    except Exception as e:
        app.logger.debug(f"ASN lookup failed for {ip}: {str(e)}")
        return None

def detect_ip_version(ip):
    """Detect if an IP is IPv4 or IPv6."""
    if is_valid_ipv4(ip):
        return 4
    elif is_valid_ipv6(ip):
        return 6
    else:
        return None

@app.after_request
def add_security_headers(response):
    """Add comprehensive security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "frame-src 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'; "
        "object-src 'none'"
    )
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Disable caching for API endpoints
    if request.endpoint and request.endpoint.startswith('api_'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.route('/')
def index():
    """Main IPWhale page - shows client IP information like ipquail.com."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    # Determine IP versions
    ipv4_address = None
    ipv6_address = None
    
    ip_version = detect_ip_version(client_ip)
    if ip_version == 4:
        ipv4_address = client_ip
    elif ip_version == 6:
        ipv6_address = client_ip
    
    # Get PTR records
    ipv4_ptr = lookup_ptr_record(ipv4_address) if ipv4_address else None
    ipv6_ptr = lookup_ptr_record(ipv6_address) if ipv6_address else None
    
    # Get ASN information
    ipv4_asn = lookup_asn(ipv4_address) if ipv4_address else None
    ipv6_asn = lookup_asn(ipv6_address) if ipv6_address else None
    
    # Format PTR records for display
    ipv4_ptr_display = ipv4_ptr[0] if ipv4_ptr else None
    ipv6_ptr_display = ipv6_ptr[0] if ipv6_ptr else None
    
    return render_template('index.html',
                         ipv4_address=ipv4_address,
                         ipv6_address=ipv6_address,
                         ipv4_ptr=ipv4_ptr_display,
                         ipv6_ptr=ipv6_ptr_display,
                         ipv4_asn=ipv4_asn,
                         ipv6_asn=ipv6_asn,
                         remote_port=client_info['remote_port'],
                         user_agent=client_info['user_agent'],
                         nat_detection=client_info['nat_detection'])

@app.route('/api/ip')
@handle_errors
def api_ip():
    """API endpoint to get client IP (both IPv4 and IPv6)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    ip_version = detect_ip_version(client_ip)
    
    result = {
        'ip': client_ip,
        'version': ip_version,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }
    
    return jsonify(result)

@app.route('/api/4/ip')
@handle_errors
def api_ipv4():
    """API endpoint to get client IPv4 address (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 4:
        return client_ip + '\n'
    else:
        return 'No IPv4 address detected\n'

@app.route('/api/6/ip')
@handle_errors
def api_ipv6():
    """API endpoint to get client IPv6 address (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 6:
        return client_ip + '\n'
    else:
        return 'No IPv6 address detected\n'

@app.route('/api/4/ptr')
@handle_errors
def api_ipv4_ptr():
    """API endpoint to get client IPv4 PTR record (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 4:
        ptr_records = lookup_ptr_record(client_ip)
        if ptr_records:
            return ptr_records[0] + '\n'
        else:
            return 'No PTR record found\n'
    else:
        return 'No IPv4 address detected\n'

@app.route('/api/6/ptr')
@handle_errors
def api_ipv6_ptr():
    """API endpoint to get client IPv6 PTR record (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 6:
        ptr_records = lookup_ptr_record(client_ip)
        if ptr_records:
            return ptr_records[0] + '\n'
        else:
            return 'No PTR record found\n'
    else:
        return 'No IPv6 address detected\n'

@app.route('/api/4/asn')
@handle_errors
def api_ipv4_asn():
    """API endpoint to get client IPv4 ASN (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 4:
        asn = lookup_asn(client_ip)
        if asn:
            return asn + '\n'
        else:
            return 'No ASN found\n'
    else:
        return 'No IPv4 address detected\n'

@app.route('/api/6/asn')
@handle_errors
def api_ipv6_asn():
    """API endpoint to get client IPv6 ASN (curl-friendly)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    if detect_ip_version(client_ip) == 6:
        asn = lookup_asn(client_ip)
        if asn:
            return asn + '\n'
        else:
            return 'No ASN found\n'
    else:
        return 'No IPv6 address detected\n'

@app.route('/api/full')
@handle_errors
def api_full():
    """API endpoint to get comprehensive client information (JSON)."""
    client_info = get_client_info()
    client_ip = client_info['ip']
    
    # Determine IP versions
    ipv4_address = None
    ipv6_address = None
    
    ip_version = detect_ip_version(client_ip)
    if ip_version == 4:
        ipv4_address = client_ip
    elif ip_version == 6:
        ipv6_address = client_ip
    
    # Get PTR records
    ipv4_ptr = lookup_ptr_record(ipv4_address) if ipv4_address else None
    ipv6_ptr = lookup_ptr_record(ipv6_address) if ipv6_address else None
    
    # Get ASN information
    ipv4_asn = lookup_asn(ipv4_address) if ipv4_address else None
    ipv6_asn = lookup_asn(ipv6_address) if ipv6_address else None
    
    result = {
        'ipv4_address': ipv4_address,
        'ipv6_address': ipv6_address,
        'ipv4_ptr': ipv4_ptr[0] if ipv4_ptr else None,
        'ipv6_ptr': ipv6_ptr[0] if ipv6_ptr else None,
        'ipv4_asn': ipv4_asn,
        'ipv6_asn': ipv6_asn,
        'remote_port': client_info['remote_port'],
        'user_agent': client_info['user_agent'],
        'nat_detection': client_info['nat_detection'],
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    }
    
    return jsonify(result)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'ipwhale',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 page."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
