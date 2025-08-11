# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, make_response, session
import dns.resolver
import dns.message
import dns.query
import dns.rdatatype
import dns.dnssec
import os
from graphviz import Digraph
import re
import hashlib
import time
import csv
import json
import io
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import html

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# Initialize compression
compress = Compress(app)

# Configure cache
cache = Cache(app)

# Enhanced rate limiting with IP tracking
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    strategy=Config.RATELIMIT_STRATEGY
)
limiter.init_app(app)

# Configure logging with enhanced security
import sys

if not app.debug:
    file_handler = RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        delay=True  # Only create log file when needed
    )
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        app.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    app.logger.info('DNS By Eye startup')

# Configure DNS resolver with timeouts
resolver = dns.resolver.Resolver()
resolver.timeout = Config.DNS_TIMEOUT
resolver.lifetime = Config.DNS_LIFETIME

# DNS timeout constant for direct queries
DNS_TIMEOUT = Config.DNS_TIMEOUT

# Input validation constants
DOMAIN_REGEX = re.compile(r'^(?=.{4,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
IP_REGEX = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
MAX_DOMAIN_LENGTH = 253
MAX_DNS_SERVERS = ['system', '8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1', '9.9.9.9', '208.67.222.222', '208.67.220.220']

def is_valid_domain(domain):
    """Validate domain name format and length."""
    if not domain or len(domain) > MAX_DOMAIN_LENGTH:
        return False
    try:
        return bool(DOMAIN_REGEX.match(domain.strip('.')))
    except Exception:
        return False

def is_valid_dns_server(dns_server):
    """Validate DNS server is either 'system' or a valid IP from our allowed list."""
    if not dns_server:
        return False
    if dns_server == 'system':
        return True
    return dns_server in MAX_DNS_SERVERS and bool(IP_REGEX.match(dns_server))

def create_custom_resolver(dns_server):
    """Create a custom DNS resolver with specified server."""
    if not dns_server or dns_server == 'system':
        return None  # Use system default
    
    custom_resolver = dns.resolver.Resolver()
    custom_resolver.nameservers = [dns_server]
    custom_resolver.timeout = Config.DNS_TIMEOUT
    custom_resolver.lifetime = Config.DNS_LIFETIME
    return custom_resolver

def calculate_health_score(trace, glue_results=None, cross_ref_results=None):
    """Calculate DNS health score and provide detailed breakdown."""
    score = 0
    breakdown = []
    
    # Weights for different aspects
    weights = {
        'root': 1,    # Root servers
        'tld': 1,     # TLD servers
        'domain': 3,  # Domain nameservers
        'glue': 3,    # Glue records
        'crossRef': 2 # Cross-reference consistency
    }
    
    # Check each layer and add points
    for i, node in enumerate(trace):
        layer_weight = weights['root'] if i == 0 else (weights['tld'] if i == 1 else weights['domain'])
        layer_score = 0
        
        # Check for DNS errors
        if not any(ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:')) 
                  for ns in node['nameservers']):
            layer_score += 0.7 * layer_weight
            points = round(0.7 * layer_weight, 1)
            zone_name = node['zone']
            breakdown.append("+" + str(points) + " points: Layer " + str(i + 1) + " (" + zone_name + ") is healthy")
        else:
            zone_name = node['zone']
            breakdown.append("+0 points: Layer " + str(i + 1) + " (" + zone_name + ") has errors")
        
        # Check response time
        if not node.get('is_slow', False):
            layer_score += 0.3 * layer_weight
            points = round(0.3 * layer_weight, 1)
            zone_name = node['zone']
            breakdown.append("+" + str(points) + " points: Layer " + str(i + 1) + " (" + zone_name + ") has good response time")
        else:
            zone_name = node['zone']
            breakdown.append("+0 points: Layer " + str(i + 1) + " (" + zone_name + ") has slow response")
        
        score += layer_score
    
    # Check glue records
    if glue_results:
        # Count major and minor glue record issues
        major_glue_issues = 0
        minor_glue_issues = 0
        
        for zone in glue_results.values():
            for issue in zone.get('glue_issues', []):
                if "Missing glue" in issue or "don't match" in issue:
                    major_glue_issues += 1
                else:
                    minor_glue_issues += 1
        
        total_glue_issues = major_glue_issues + minor_glue_issues
        
        if total_glue_issues == 0:
            score += weights['glue']
            breakdown.append("+" + str(weights['glue']) + " points: All glue records are correct")
        else:
            # Major issues: -1 point each, Minor issues: -0.25 points each
            deduction = major_glue_issues * 1.0 + minor_glue_issues * 0.25
            remaining_points = max(0, weights['glue'] - deduction)
            score += remaining_points
            
            if major_glue_issues > 0:
                issue_text = "issue" if major_glue_issues == 1 else "issues"
                breakdown.append("-" + str(round(major_glue_issues * 1.0, 1)) + " points: " + str(major_glue_issues) + " major glue " + issue_text + " found")
            if minor_glue_issues > 0:
                issue_text = "issue" if minor_glue_issues == 1 else "issues"
                breakdown.append("-" + str(round(minor_glue_issues * 0.25, 1)) + " points: " + str(minor_glue_issues) + " minor glue " + issue_text + " found")
    
    # Check cross-reference consistency and nameserver health
    if cross_ref_results:
        inconsistencies = 0
        broken_nameservers = 0
        inconsistency_details = []
        
        for ns, info in cross_ref_results.items():
            if isinstance(info, dict):
                # Check for nameserver errors (broken/unreachable nameservers)
                if info.get('error'):
                    broken_nameservers += 1
                    inconsistency_details.append(ns + ": " + info.get('error'))
                
                # Check for self-reference inconsistencies
                refs = info.get('references', [])
                if refs and ns.rstrip('.') not in [ref.rstrip('.') for ref in refs]:
                    inconsistencies += 1
                    inconsistency_details.append(ns + " does not reference itself")
        
        total_issues = inconsistencies + broken_nameservers
        
        if total_issues == 0:
            score += weights['crossRef']
            breakdown.append("+" + str(weights['crossRef']) + " points: All nameserver references are consistent")
        else:
            # Major issues: -1 point each (broken nameservers), Minor issues: -0.25 points each (inconsistencies)
            deduction = broken_nameservers * 1.0 + inconsistencies * 0.25
            remaining_points = max(0, weights['crossRef'] - deduction)
            score += remaining_points
            
            if broken_nameservers > 0:
                ns_text = "nameserver" if broken_nameservers == 1 else "nameservers"
                breakdown.append("-" + str(round(broken_nameservers * 1.0, 1)) + " points: " + str(broken_nameservers) + " broken " + ns_text + " found")
                # Add specific broken nameserver details
                broken_details = [detail for detail in inconsistency_details if ": " in detail]
                for detail in broken_details[:3]:  # Show first 3 broken nameserver issues
                    breakdown.append("  • " + detail)
                if len(broken_details) > 3:
                    breakdown.append("  • ... and " + str(len(broken_details) - 3) + " more")
            
            if inconsistencies > 0:
                ref_text = "reference" if inconsistencies == 1 else "references"
                breakdown.append("-" + str(round(inconsistencies * 0.25, 1)) + " points: " + str(inconsistencies) + " inconsistent nameserver " + ref_text + " found")
    
    # Normalize score to be out of 10
    max_score = 10
    score = min(10, round(score, 1))
    
    return {
        'score': score,
        'max_score': max_score,
        'breakdown': breakdown,
        'percentage': (score / max_score) * 100
    }

# Request validation middleware
@app.before_request
def validate_request():
    """Validate and sanitize incoming requests."""
    # Validate content type for POST requests
    if request.method == 'POST':
        if not request.is_json:
            app.logger.warning("Invalid content type from " + str(get_remote_address()))
            return jsonify({'error': 'Request must be JSON'}), 415
        
        # Check request size
        if request.content_length and request.content_length > Config.MAX_CONTENT_LENGTH:
            app.logger.warning("Request too large from " + str(get_remote_address()))
            return jsonify({'error': 'Request too large'}), 413
        
        # Validate request body
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing request body'}), 400
        except Exception as e:
            app.logger.warning("Invalid JSON from " + str(get_remote_address()) + ": " + str(e))
            return jsonify({'error': 'Invalid JSON'}), 400

# Enhanced error handling
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle exceptions with enhanced security and logging."""
    error_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
    app.logger.error("Error " + error_id + ": " + str(e), exc_info=True)
    
    if isinstance(e, dns.resolver.NXDOMAIN):
        return jsonify({'error': 'Domain does not exist'}), 404
    elif isinstance(e, dns.resolver.NoAnswer):
        return jsonify({'error': 'No DNS records found'}), 404
    elif isinstance(e, dns.resolver.Timeout):
        return jsonify({'error': 'DNS query timed out'}), 504
    elif isinstance(e, dns.resolver.NoNameservers):
        return jsonify({'error': 'No nameservers available'}), 502
    elif isinstance(e, dns.dnssec.ValidationFailure):
        return jsonify({'error': 'DNSSEC validation failed'}), 400
    
    # Generic error response (don't expose internal details)
    return jsonify({
        'error': 'An unexpected error occurred',
        'error_id': error_id
    }), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors with enhanced logging."""
    app.logger.warning("Rate limit exceeded from " + str(get_remote_address()))
    return jsonify({
        'error': 'Rate limit exceeded',
        'description': e.description
    }), 429

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
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
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
    return response

@app.route('/', methods=['GET'])
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files with security headers."""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/health', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    })

@app.route('/api/dns-servers', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def get_dns_servers():
    """Get list of available DNS servers."""
    return jsonify({
        'dns_servers': MAX_DNS_SERVERS,
        'default': 'system'
    })

@app.route('/api/delegation', methods=['POST'])
@limiter.limit(Config.RATELIMIT_API_DEFAULT)
def api_delegation():
    """API endpoint for DNS delegation analysis with visualizations."""
    try:
        # Validate request body
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
            
        # Input validation
        domain = data.get('domain', '').strip().lower()
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        if not is_valid_domain(domain):
            return jsonify({'error': 'Invalid domain format'}), 400
            
        dns_server = data.get('dns_server', 'system')
        if not is_valid_dns_server(dns_server):
            return jsonify({'error': 'Invalid DNS server'}), 400
            
        verbose = bool(data.get('verbose', False))
        check_glue = bool(data.get('check_glue', True))
        
        app.logger.info("Received delegation request for domain: " + domain)
        
        # Create custom resolver if specified
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=True)
        chain_str = " → ".join(chain)

        # Get glue records and cross-reference data for health score
        glue_results = {}
        cross_ref_results = {}
        try:
            if check_glue:
                glue_results = check_glue_records(domain, custom_resolver)
            last_level_ns = [ns for ns in trace[-1]['nameservers'] 
                           if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]
            if last_level_ns:
                cross_ref_results = test_last_level_ns_references(last_level_ns, domain)
        except Exception as e:
            app.logger.warning("Additional analysis failed for " + domain + ": " + str(e))
        
        # Generate graphs for each level
        graph_urls = []
        try:
            for i, node in enumerate(trace):
                zone = node['zone']
                dot = Digraph(comment='DNS Delegation Graph for ' + zone)
                dot.attr(rankdir='TB')  # Top->down layout
                
                # Add zone node
                dot.node(zone, zone, shape='box', style='filled', fillcolor='lightblue')
                
                # Add nameserver nodes and edges
                for ns in node['nameservers']:
                    if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:')):
                        dot.node(ns, ns)
                        dot.edge(zone, ns)
                
                # Save graph
                filename = domain.replace('.', '_') + '_' + str(i)
                dot.render("app/static/generated/" + filename, format='png', cleanup=True)
                graph_urls.append(url_for('static', filename='generated/' + filename + '.png'))
        except Exception as e:
            app.logger.error("Error generating graphs: " + str(e))
        
        # Generate Domain Report graph
        domain_report_graph_url = None
        if cross_ref_results:
            try:
                dot = Digraph(comment='Domain Report for ' + domain)
                dot.attr(rankdir='TB')  # Top->down layout
                
                # Add domain node
                dot.node(domain, domain, shape='box', style='filled', fillcolor='lightblue')
                
                # Add nodes for each nameserver
                ns_count = len(cross_ref_results)
                for i, (ns, info) in enumerate(cross_ref_results.items()):
                    if isinstance(info, dict):
                        # Condense large sets of nameservers
                        if ns_count > 4 and i == 3 and domain != chain[-1]:
                            more_node = "more_" + str(ns_count-3)
                            more_label = "... (" + str(ns_count-3) + " more)"
                            dot.node(more_node, more_label, shape='ellipse', style='filled', fillcolor='lightgray')
                            dot.edge(domain, more_node)
                            break
                        
                        # Color nameservers based on their status
                        if info.get('error'):
                            color = 'lightcoral'  # Red for broken nameservers
                        elif info.get('self_reference'):
                            color = 'lightgreen'  # Green for healthy nameservers with self-reference
                        else:
                            color = 'lightyellow'  # Yellow for nameservers without self-reference
                        
                        dot.node(ns, ns, style='filled', fillcolor=color)
                        dot.edge(domain, ns)
                
                # Add edges for references - use separate arrows for each direction
                for ns, info in cross_ref_results.items():
                    if isinstance(info, dict):
                        ns_normalized = ns.rstrip('.')
                        refs = info.get('references', [])
                        for ref in refs:
                            ref_normalized = ref.rstrip('.')
                            if ref_normalized == ns_normalized:  # Self-reference
                                dot.edge(ns, ns, dir='both', color='green', label='self-ref')
                            else:
                                # Check if this nameserver exists in our results
                                ref_key = None
                                for key in cross_ref_results.keys():
                                    if key.rstrip('.') == ref_normalized:
                                        ref_key = key
                                        break
                                
                                if ref_key:
                                    # Always add a one-way arrow from this nameserver to the referenced one
                                    dot.edge(ns, ref_key, color='blue', penwidth='2')
                
                # Save graph
                filename = domain.replace('.', '_') + "_domain_report"
                dot.render("app/static/generated/" + filename, format='png', cleanup=True)
                domain_report_graph_url = url_for('static', filename='generated/' + filename + '.png')
            except Exception as e:
                app.logger.error("Error generating Domain Report graph: " + str(e))
        
        # Generate Glue Analysis graph
        glue_analysis_graph_url = None
        if glue_results:
            try:
                dot = Digraph(comment='Glue Analysis for ' + domain)
                dot.attr(rankdir='TB')  # Top->down layout
                
                for zone, data in glue_results.items():
                    dot.node(zone, zone, shape='box', style='filled', fillcolor='lightblue')
                    for ns, ns_data in data.get('glue_records', {}).items():
                        color = 'lightgreen' if ns_data.get('glue_matches_resolution') else 'lightcoral'
                        dot.node(ns, ns, style='filled', fillcolor=color)
                        dot.edge(zone, ns)
                        
                        if ns_data.get('glue_a_records'):
                            for ip in ns_data['glue_a_records']:
                                dot.node(ip, ip, shape='ellipse')
                                dot.edge(ns, ip, color='blue')
                        
                        if ns_data.get('glue_aaaa_records'):
                            for ip in ns_data['glue_aaaa_records']:
                                dot.node(ip, ip, shape='ellipse')
                                dot.edge(ns, ip, color='green')
                
                # Save graph
                filename = domain.replace('.', '_') + "_glue_analysis"
                dot.render("app/static/generated/" + filename, format='png', cleanup=True)
                glue_analysis_graph_url = url_for('static', filename='generated/' + filename + '.png')
            except Exception as e:
                app.logger.error("Error generating Glue Analysis graph: " + str(e))
        
        return jsonify({
            'domain': domain,
            'chain': chain_str,
            'dns_server_used': dns_server,
            'trace': trace,
            'timing_info': timing,
            'glue_results': glue_results,
            'cross_ref_results': cross_ref_results,
            'health_score': calculate_health_score(trace, glue_results, cross_ref_results),
            'graph_urls': graph_urls,
            'domain_report_graph_url': domain_report_graph_url,
            'glue_analysis_graph_url': glue_analysis_graph_url
        })
    except Exception as e:
        app.logger.error("Error processing delegation request for " + domain + ": " + str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/trace/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_trace_domain(domain):
    """API endpoint for DNS delegation trace without visualizations."""
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
        
    verbose = request.args.get('verbose', 'false').lower() == 'true'
    dns_server = request.args.get('dns_server', 'system')
    
    if not is_valid_dns_server(dns_server):
        return jsonify({'error': 'Invalid DNS server'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=True)
        chain_str = " → ".join(chain)
        
        return jsonify({
            'domain': domain,
            'trace': trace,
            'chain': chain_str,
            'dns_server_used': dns_server,
            'timing_info': timing,
            'verbose': verbose
        })
    except Exception as e:
        app.logger.error("Error tracing domain " + domain + ": " + str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def export_data(domain):
    """Export endpoint for DNS delegation data in JSON or CSV format."""
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
        
    format = request.args.get('format', 'json').lower()
    verbose = request.args.get('verbose', 'false').lower() == 'true'
    dns_server = request.args.get('dns_server', 'system')
    debug = request.args.get('debug', 'false').lower() == 'true'
    
    if not is_valid_dns_server(dns_server):
        return jsonify({'error': 'Invalid DNS server'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=debug)
        chain_str = " → ".join(chain)
        
        # Get additional data
        glue_results = check_glue_records(domain, custom_resolver)
        last_level_ns = [ns for ns in trace[-1]['nameservers'] 
                        if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]
        cross_ref_results = test_last_level_ns_references(last_level_ns, domain) if last_level_ns else {}
        
        if format == 'json':
            data = {
                'domain': domain,
                'chain': chain_str,
                'dns_server_used': dns_server,
                'trace': trace,
                'timing_info': timing,
                'glue_results': glue_results,
                'cross_ref_results': cross_ref_results,
                'health_score': calculate_health_score(trace, glue_results, cross_ref_results)
            }
            response = make_response(jsonify(data))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = 'attachment; filename=' + domain + '_dns_analysis.json'
            return response
            
        elif format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Domain Analysis Report for ' + domain])
            writer.writerow(['Chain:', chain_str])
            writer.writerow(['DNS Server:', dns_server])
            writer.writerow([])
            
            # Write delegation trace
            writer.writerow(['Delegation Trace'])
            writer.writerow(['Zone', 'Nameservers', 'Response Time (ms)', 'Is Slow', 'Error Type'])
            for node in trace:
                writer.writerow([
                    node['zone'],
                    '; '.join(node['nameservers']),
                    node['response_time'],
                    'Yes' if node.get('is_slow') else 'No',
                    node.get('error_type', '')
                ])
            writer.writerow([])
            
            # Write glue records analysis
            writer.writerow(['Glue Records Analysis'])
            for zone, data in glue_results.items():
                writer.writerow(['Zone:', zone])
                writer.writerow(['Status:', data['status']])
                if data['glue_issues']:
                    writer.writerow(['Issues:'])
                    for issue in data['glue_issues']:
                        writer.writerow(['', issue])
                writer.writerow([])
            
            # Write cross-reference results
            writer.writerow(['Domain Report'])
            for ns, info in cross_ref_results.items():
                if isinstance(info, dict):
                    writer.writerow(['Nameserver:', ns])
                    writer.writerow(['References:', '; '.join(info.get('references', []))])
                    writer.writerow(['Self Reference:', 'Yes' if info.get('self_reference') else 'No'])
                    if info.get('mutual_references'):
                        writer.writerow(['Mutual References:', '; '.join(info.get('mutual_references', []))])
                    if info.get('error'):
                        writer.writerow(['Error:', info.get('error')])
                    writer.writerow([])
            
            # Write health score
            health_score = calculate_health_score(trace, glue_results, cross_ref_results)
            writer.writerow(['Health Score'])
            writer.writerow(['Score:', str(health_score['score']) + '/' + str(health_score['max_score'])])
            writer.writerow(['Percentage:', str(health_score['percentage']) + '%'])
            writer.writerow([])
            writer.writerow(['Score Breakdown'])
            for detail in health_score['breakdown']:
                writer.writerow(['', detail])
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=' + domain + '_dns_analysis.csv'
            return response
        else:
            return jsonify({'error': 'Invalid export format. Use "json" or "csv"'}), 400
            
    except Exception as e:
        app.logger.error("Error exporting data for " + domain + ": " + str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/nameservers/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_nameservers(domain):
    """API endpoint to get nameservers for a domain."""
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
        
    dns_server = request.args.get('dns_server', 'system')
    if not is_valid_dns_server(dns_server):
        return jsonify({'error': 'Invalid DNS server'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        query_resolver = custom_resolver if custom_resolver else resolver
        
        ns_records = query_resolver.resolve(domain, 'NS')
        ns_list = [r.to_text() for r in ns_records]
        
        # Get A/AAAA records for each nameserver
        ns_info = {}
        for ns in ns_list:
            ns_info[ns] = {
                'a_records': [],
                'aaaa_records': []
            }
            try:
                a_records = query_resolver.resolve(ns, 'A')
                ns_info[ns]['a_records'] = [r.to_text() for r in a_records]
            except:
                pass
            try:
                aaaa_records = query_resolver.resolve(ns, 'AAAA')
                ns_info[ns]['aaaa_records'] = [r.to_text() for r in aaaa_records]
            except:
                pass
        
        return jsonify({
            'domain': domain,
            'nameservers': ns_list,
            'nameserver_info': ns_info,
            'dns_server_used': dns_server
        })
    except Exception as e:
        app.logger.error("Error getting nameservers for " + domain + ": " + str(e))
        return jsonify({'error': str(e)}), 500


def check_glue_records(domain, custom_resolver=None):
    """
    Check glue records for all domains in the delegation chain.
    This function performs comprehensive glue record validation by:
    1. Getting NS records for each zone in the delegation chain
    2. For each nameserver, checking if glue records (A/AAAA) are provided by the PARENT zone in the additional section
    3. Verifying that the glue record IPs actually resolve to the nameserver names
    4. Identifying missing, incorrect, or inconsistent glue records
    
    Glue records are provided by the parent zone, not the zone itself.
    
    Returns a dict with detailed glue record analysis for each zone.
    """
    query_resolver = custom_resolver if custom_resolver else resolver
    
    # Build the delegation chain
    labels = [label for label in domain.strip('.').split('.') if label]
    reversed_labels = labels[::-1]
    chain = ['.']
    for i in range(len(reversed_labels)):
        zone = '.'.join(reversed_labels[:i+1][::-1])
        chain.append(zone)
    
    glue_results = {}
    
    for i, zone in enumerate(chain):
        zone_result = {
            'zone': zone,
            'nameservers': [],
            'glue_records': {},
            'glue_issues': [],
            'status': 'unknown'
        }
        
        # Skip glue record checking for root (.) zone only
        if i == 0:  # 0 = root only
            zone_result['status'] = 'skipped'
            zone_result['glue_issues'].append("Glue record checking skipped for " + zone + " (root level)")
            glue_results[zone] = zone_result
            continue
        
        try:
            # Get NS records for this zone
            ns_response = query_resolver.resolve(zone, 'NS')
            ns_list = [r.to_text().rstrip('.') for r in ns_response]
            zone_result['nameservers'] = ns_list
            zone_result['status'] = 'success'
            
            # Get the parent zone to query for glue records
            parent_zone = chain[i-1] if i > 0 else '.'
            
            # For each nameserver, check glue records provided by the parent zone
            for ns in ns_list:
                ns_glue = {
                    'nameserver': ns,
                    'expected_glue': False,
                    'has_glue_a': False,
                    'has_glue_aaaa': False,
                    'glue_a_records': [],
                    'glue_aaaa_records': [],
                    'resolved_a_records': [],
                    'resolved_aaaa_records': [],
                    'glue_matches_resolution': True,
                    'issues': []
                }
                
                # Determine if glue records are expected
                # Glue records are needed when the nameserver is within the zone being delegated
                if zone != '.' and (ns.endswith('.' + zone) or ns == zone):
                    ns_glue['expected_glue'] = True
                
                # Query the parent zone for NS records of the current zone to get glue records
                try:
                    # Find a nameserver for the parent zone to query
                    parent_ns_list = []
                    if parent_zone == '.':
                        # Use root servers
                        parent_ns_list = ['a.root-servers.net', 'b.root-servers.net', 'c.root-servers.net']
                    else:
                        try:
                            parent_ns_response = query_resolver.resolve(parent_zone, 'NS')
                            parent_ns_list = [r.to_text().rstrip('.') for r in parent_ns_response]
                        except:
                            pass
                    
                    # Try to query one of the parent zone's nameservers
                    for parent_ns in parent_ns_list:
                        try:
                            # Get IP of parent nameserver
                            parent_ns_ips = query_resolver.resolve(parent_ns, 'A')
                            if parent_ns_ips:
                                query_target = parent_ns_ips[0].to_text()
                                
                                # Create DNS message for NS query of the child zone
                                query_msg = dns.message.make_query(zone, 'NS')
                                response = dns.query.udp(query_msg, query_target, timeout=DNS_TIMEOUT)
                                
                                # Check additional section for glue records
                                for rr in response.additional:
                                    if rr.name.to_text().rstrip('.') == ns:
                                        if rr.rdtype == dns.rdatatype.A:
                                            ns_glue['has_glue_a'] = True
                                            for rd in rr:
                                                ns_glue['glue_a_records'].append(rd.to_text())
                                        elif rr.rdtype == dns.rdatatype.AAAA:
                                            ns_glue['has_glue_aaaa'] = True
                                            for rd in rr:
                                                ns_glue['glue_aaaa_records'].append(rd.to_text())
                                break  # Found glue records from this parent NS, no need to try others
                        except Exception as e:
                            continue  # Try next parent nameserver
                
                except Exception as e:
                    ns_glue['issues'].append("Error checking glue records from parent zone: " + str(e))
                
                # Get resolved A and AAAA records for comparison
                try:
                    a_records = query_resolver.resolve(ns, 'A')
                    ns_glue['resolved_a_records'] = [r.to_text() for r in a_records]
                except:
                    pass
                
                try:
                    aaaa_records = query_resolver.resolve(ns, 'AAAA')
                    ns_glue['resolved_aaaa_records'] = [r.to_text() for r in aaaa_records]
                except:
                    pass
                
                # Check if glue records match resolved records
                if ns_glue['glue_a_records'] and ns_glue['resolved_a_records']:
                    if set(ns_glue['glue_a_records']) != set(ns_glue['resolved_a_records']):
                        ns_glue['glue_matches_resolution'] = False
                        ns_glue['issues'].append("Glue A records don't match resolved A records")
                
                if ns_glue['glue_aaaa_records'] and ns_glue['resolved_aaaa_records']:
                    if set(ns_glue['glue_aaaa_records']) != set(ns_glue['resolved_aaaa_records']):
                        ns_glue['glue_matches_resolution'] = False
                        ns_glue['issues'].append("Glue AAAA records don't match resolved AAAA records")
                
                # Check for missing glue records when expected
                if ns_glue['expected_glue']:
                    if not ns_glue['has_glue_a'] and ns_glue['resolved_a_records']:
                        ns_glue['issues'].append("Missing glue A records (expected for in-zone nameserver)")
                    if not ns_glue['has_glue_aaaa'] and ns_glue['resolved_aaaa_records']:
                        ns_glue['issues'].append("Missing glue AAAA records (expected for in-zone nameserver)")
                
                # Check for unnecessary glue records
                if not ns_glue['expected_glue']:
                    if ns_glue['has_glue_a'] or ns_glue['has_glue_aaaa']:
                        ns_glue['issues'].append("Unnecessary glue records (nameserver is out-of-zone)")
                
                zone_result['glue_records'][ns] = ns_glue
                
                # Add issues to zone-level issues
                if ns_glue['issues']:
                    zone_result['glue_issues'].extend([ns + ": " + issue for issue in ns_glue['issues']])
            
        except dns.resolver.NXDOMAIN:
            zone_result['status'] = 'nxdomain'
            zone_result['glue_issues'].append("Zone " + zone + " does not exist")
        except dns.resolver.NoAnswer:
            zone_result['status'] = 'no_ns'
            zone_result['glue_issues'].append("No NS records found for " + zone)
        except Exception as e:
            zone_result['status'] = 'error'
            zone_result['glue_issues'].append("Error querying " + zone + ": " + str(e))
        
        glue_results[zone] = zone_result
    
    return glue_results

def test_last_level_ns_references(nameservers, domain):
    """Test cross-references between nameservers at the last level."""
    results = {}
    for ns in nameservers:
        results[ns] = {'references': set()}
    
    for ns in nameservers:
        try:
            # Query this nameserver for NS records of the domain
            ns_ips = resolver.resolve(ns, 'A')
            if ns_ips:
                query_target = ns_ips[0].to_text()
                query_msg = dns.message.make_query(domain, 'NS')
                response = dns.query.udp(query_msg, query_target, timeout=DNS_TIMEOUT)
                
                # Extract nameservers from the response
                for section in [response.answer, response.authority]:
                    for rr in section:
                        if rr.rdtype == dns.rdatatype.NS:
                            for rd in rr:
                                ref_ns = rd.to_text().rstrip('.')
                                # Always add the reference, even if it's not in our nameserver list
                                # This helps catch cases where a nameserver references itself or others
                                results[ns]['references'].add(ref_ns)
                                # If this is a self-reference, mark it explicitly
                                if ref_ns.rstrip('.') == ns.rstrip('.'):
                                    results[ns]['self_reference'] = True
        except Exception as e:
            app.logger.warning("Error querying nameserver " + ns + " for " + domain + ": " + str(e))
            results[ns] = {'references': set(), 'error': str(e)}
    
    # Convert sets to lists for JSON serialization and ensure all nameservers are included
    for ns in nameservers:
        if isinstance(results.get(ns), dict):
            refs = sorted(list(results[ns]['references']))
            results[ns]['references'] = refs
            # Add self-reference indicator
            results[ns]['self_reference'] = any(ref.rstrip('.') == ns.rstrip('.') for ref in refs)
            # Add mutual reference indicators
            results[ns]['mutual_references'] = [
                ref for ref in refs
                if ref in nameservers and 
                   isinstance(results.get(ref), dict) and
                   any(r.rstrip('.') == ns.rstrip('.') for r in results[ref]['references'])
            ]
        else:
            results[ns] = {'references': [], 'error': str(results.get(ns, 'Unknown error'))}
    
    return results

def trace_delegation(domain, verbose=False, custom_resolver=None, debug=False):
    """
    Trace DNS delegation from root (.) down to authoritative nameserver.
    Returns a list of dicts with zone, nameservers, and optional verbose info.
    Constructs chain starting from root (.) at layer 1, then TLD, then domain, etc.
    
    This function is resilient to failures - it will trace as far as possible
    and stop gracefully when it encounters unresolvable zones.
    """
    # Use custom resolver if provided, otherwise use default
    query_resolver = custom_resolver if custom_resolver else resolver
    
    result = []
    timing_info = {}
    labels = [label for label in domain.strip('.').split('.') if label]
    # Reverse labels for right-to-left processing
    reversed_labels = labels[::-1]
    chain = ['.']
    # Build chain from root to domain
    for i in range(len(reversed_labels)):
        zone = '.'.join(reversed_labels[:i+1][::-1])
        chain.append(zone)

    # Track if we've encountered a fatal error that should stop further tracing
    should_continue = True
    
    for i in range(len(chain)):
        if not should_continue:
            break
            
        zone = chain[i]
        start_time = time.time()
        error_type = None
        
        try:
            ns_records = query_resolver.resolve(zone, 'NS')
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            ns_list = [r.to_text() for r in ns_records]
            verbose_info = ""
            
            if verbose:
                glue = []
                for ns in ns_list:
                    try:
                        a_start = time.time()
                        a_records = query_resolver.resolve(ns, 'A')
                        a_end = time.time()
                        a_time = round((a_end - a_start) * 1000, 2)
                        glue.append(f"{ns} A: {', '.join([a.to_text() for a in a_records])} ({a_time}ms)")
                    except Exception:
                        pass
                    try:
                        aaaa_start = time.time()
                        aaaa_records = query_resolver.resolve(ns, 'AAAA')
                        aaaa_end = time.time()
                        aaaa_time = round((aaaa_end - aaaa_start) * 1000, 2)
                        glue.append(f"{ns} AAAA: {', '.join([a.to_text() for a in aaaa_records])} ({aaaa_time}ms)")
                    except Exception:
                        pass
                if glue:
                    verbose_info = " | ".join(glue)
                    
        except dns.resolver.NXDOMAIN as e:
            # Domain doesn't exist - this is a definitive answer, stop here
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"NXDOMAIN: {zone} does not exist"]
            verbose_info = f"Domain {zone} does not exist" if verbose else ""
            error_type = "NXDOMAIN"
            should_continue = False
            
        except dns.resolver.NoAnswer as e:
            # No NS records found for this zone
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"No NS records: {zone} has no nameservers"]
            verbose_info = f"No NS records found for {zone}" if verbose else ""
            error_type = "NO_NS"
            should_continue = False
            
        except dns.resolver.Timeout as e:
            # Timeout - could be temporary, but stop tracing deeper
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"Timeout: Query for {zone} timed out"]
            verbose_info = f"DNS query timeout for {zone}" if verbose else ""
            error_type = "TIMEOUT"
            should_continue = False
            
        except dns.resolver.NoNameservers as e:
            # No nameservers available to answer the query
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"No nameservers: No servers available for {zone}"]
            verbose_info = f"No nameservers available for {zone}" if verbose else ""
            error_type = "NO_NAMESERVERS"
            should_continue = False
            
        except Exception as e:
            # Other errors - log them but continue if it's not too deep in the chain
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            error_msg = str(e)
            ns_list = [f"Error: {error_msg}"]
            verbose_info = f"Query error for {zone}: {error_msg}" if verbose else ""
            error_type = "OTHER"
            
            # If we're past the TLD level and getting errors, stop tracing
            if i > 1:  # 0=root, 1=TLD, 2+=domain levels
                should_continue = False
        
        # Flag slow responses (>2000ms is considered slow for DNS)
        is_slow = response_time > 2000
        timing_info[zone] = {
            'response_time': response_time, 
            'is_slow': is_slow,
            'error_type': error_type
        }
        
        result.append({
            'zone': zone, 
            'nameservers': ns_list, 
            'verbose': verbose_info if verbose else None,
            'response_time': response_time,
            'is_slow': is_slow,
            'error_type': error_type,
            'trace_stopped': not should_continue and i < len(chain) - 1
        })
    
    # If we stopped early, update the chain to reflect what was actually traced
    if not should_continue and len(result) < len(chain):
        chain = chain[:len(result)]
    
    return result, chain, timing_info if debug else {}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
