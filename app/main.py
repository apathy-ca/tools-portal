from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, make_response, session
import dns.resolver
import dns.message
import dns.query
import dns.rdatatype
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

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# Initialize compression
compress = Compress(app)

# Configure cache
cache = Cache(app)

# Enhanced rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[Config.RATELIMIT_DEFAULT],
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    strategy=Config.RATELIMIT_STRATEGY
)

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=Config.LOG_MAX_BYTES, backupCount=Config.LOG_BACKUP_COUNT)
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('DNS By Eye startup')

# Cache key generation function
def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (Config.CACHE_KEY_PREFIX + path + args).encode('utf-8')

# Request validation middleware
@app.before_request
def validate_request():
    if request.method == 'POST' and not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 415
    if request.content_length and request.content_length > Config.MAX_CONTENT_LENGTH:
        return jsonify({'error': 'Request too large'}), 413

# Error handling
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded', 'description': e.description}), 429

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com"
    return response

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

def calculate_health_score(trace, glue_results=None, cross_ref_results=None):
    """Calculate DNS health score and provide detailed breakdown."""
    score = 0
    breakdown = []
    
    # Weights for different layers
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
            breakdown.append(f"+{(0.7 * layer_weight):.1f} points: Layer {i + 1} ({node['zone']}) is healthy")
        else:
            breakdown.append(f"+0 points: Layer {i + 1} ({node['zone']}) has errors")
        
        # Check response time
        if not node.get('is_slow', False):
            layer_score += 0.3 * layer_weight
            breakdown.append(f"+{(0.3 * layer_weight):.1f} points: Layer {i + 1} ({node['zone']}) has good response time")
        else:
            breakdown.append(f"+0 points: Layer {i + 1} ({node['zone']}) has slow response")
        
        score += layer_score
    
    # Check glue records
    if glue_results:
        # Only count actual glue record issues (ignore unnecessary glue warnings)
        glue_issues = 0
        for zone in glue_results.values():
            for issue in zone.get('glue_issues', []):
                # Skip unnecessary glue record warnings
                if not "Unnecessary glue records" in issue:
                    glue_issues += 1
        
        if glue_issues == 0:
            score += weights['glue']
            breakdown.append(f"+{weights['glue']} points: All glue records are correct")
        else:
            deduction = min(glue_issues * 0.5, weights['glue'])
            remaining_points = weights['glue'] - deduction
            score += remaining_points
            breakdown.append(f"+{remaining_points:.1f} points: {glue_issues} glue record issue{'' if glue_issues == 1 else 's'} found")
    
    # Check cross-reference consistency
    if cross_ref_results:
        inconsistencies = sum(1 for ns, info in cross_ref_results.items()
                            if isinstance(info, dict) and info.get('references') and 
                            ns not in info['references'])
        if inconsistencies == 0:
            score += weights['crossRef']
            breakdown.append(f"+{weights['crossRef']} points: All nameserver references are consistent")
        else:
            deduction = min(inconsistencies * 0.5, weights['crossRef'])
            remaining_points = weights['crossRef'] - deduction
            score += remaining_points
            breakdown.append(f"+{remaining_points:.1f} points: {inconsistencies} inconsistent nameserver reference{'' if inconsistencies == 1 else 's'} found")
    
    # Normalize score to be out of 10
    max_score = 10
    score = min(10, round(score, 1))
    
    return {
        'score': score,
        'max_score': max_score,
        'breakdown': breakdown,
        'percentage': (score / max_score) * 100
    }

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

def create_custom_resolver(dns_server):
    """Create a custom DNS resolver with specified server."""
    if not dns_server or dns_server == 'system':
        return None  # Use system default
    
    custom_
