from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, make_response
import dns.resolver
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

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config.from_object(Config)

# Initialize compression
compress = Compress(app)

# Configure simple in-memory cache
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)
limiter = Limiter(app, key_func=get_remote_address, default_limits=[Config.RATELIMIT_DEFAULT])

@app.after_request
def add_csp_header(response):
    return response

# Configure DNS resolver with timeouts
resolver = dns.resolver.Resolver()
resolver.timeout = Config.DNS_TIMEOUT
resolver.lifetime = Config.DNS_LIFETIME

DOMAIN_REGEX = re.compile(r'^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$')
def is_valid_domain(domain):
    return bool(DOMAIN_REGEX.match(domain.strip('.')))

def trace_delegation(domain, verbose=False, custom_resolver=None, debug=False):
    """
    Trace DNS delegation from root (.) down to authoritative nameserver.
    Returns a list of dicts with zone, nameservers, and optional verbose info.
    Constructs chain starting from root (.) at layer 1, then TLD, then domain, etc.
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

    for i in range(len(chain)):
        zone = chain[i]
        start_time = time.time()
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
        except Exception as e:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            ns_list = [f"Error: {e}"]
            verbose_info = str(e) if verbose else ""
        
        # Flag slow responses (>2000ms is considered slow for DNS)
        is_slow = response_time > 2000
        timing_info[zone] = {'response_time': response_time, 'is_slow': is_slow}
        
        result.append({
            'zone': zone, 
            'nameservers': ns_list, 
            'verbose': verbose_info if verbose else None,
            'response_time': response_time,
            'is_slow': is_slow
        })
    
    return result, chain, timing_info if debug else {}

def create_custom_resolver(dns_server):
    """Create a custom DNS resolver with specified server."""
    if not dns_server or dns_server == 'system':
        return None  # Use system default
    
    custom_resolver = dns.resolver.Resolver()
    custom_resolver.nameservers = [dns_server]
    custom_resolver.timeout = Config.DNS_TIMEOUT
    custom_resolver.lifetime = Config.DNS_LIFETIME
    return custom_resolver


def build_layer_graph(zone, ns_list, parent_ns_list=None, verbose_info=None, verbose=False, index=0, prefix=None):
    """
    Build a graph for a single layer (zone and its NS).
    Show arrows between NS if they refer to themselves or each other (only for final layer).
    Draw box around NS that match delegation from parent layer.
    For root servers, limit to 4 and show indication of more.
    """
    dot = Digraph(format='png')
    dot.attr(rankdir='TB')
    # Sanitize zone name for label to avoid dot causing syntax error
    safe_zone_label = zone.replace('.', '\\.')
    dot.attr(label=safe_zone_label, labelloc='t', fontsize='20')

    zone_node = f"zone_{index}"
    # Remove verbose info from the zone box - keep it clean
    label = zone
    dot.node(zone_node, label, shape='box', style='filled', fillcolor='#e0e0ff')

    # For root servers, limit to 4 and show a "..." node
    is_root = zone == '.'
    display_ns_list = ns_list
    has_more = False
    
    if is_root and len(ns_list) > 4:
        display_ns_list = ns_list[:4]
        has_more = True

    ns_nodes = {}
    for ns in display_ns_list:
        ns_node = f"ns_{index}_{ns.replace('.', '_')}"
        ns_nodes[ns] = ns_node

    # Add "more servers" node if needed
    if has_more:
        more_node = f"more_{index}"
        ns_nodes[f"... and {len(ns_list) - 4} more"] = more_node

    # Determine which NS are referenced by parent layer
    referenced_ns = set(parent_ns_list) if parent_ns_list else set()

    # Draw NS nodes, color based on whether referenced by parent
    for ns in display_ns_list:
        ns_node = ns_nodes[ns]
        if ns in referenced_ns:
            fillcolor = '#eaffea'  # greenish
            style = 'filled'
        else:
            fillcolor = '#ffcccc'  # redish
            style = 'filled'
        dot.node(ns_node, ns, shape='ellipse', style=style, fillcolor=fillcolor)

    # Add "more servers" node
    if has_more:
        dot.node(more_node, f"... and {len(ns_list) - 4} more", shape='ellipse', style='filled,dashed', fillcolor='#f0f0f0', color='#888888')

    # Edges from zone to NS
    for ns in display_ns_list:
        ns_node = ns_nodes[ns]
        dot.edge(zone_node, ns_node)
    
    # Edge to "more servers" node
    if has_more:
        dot.edge(zone_node, more_node, style='dashed', color='#888888')

    # If this is the final layer (no children), add arrows between NS if they refer to themselves or each other
    if parent_ns_list is not None and len(display_ns_list) > 1:
        # Check NS refer to each other or themselves by resolving NS records of each NS
        for ns in display_ns_list:
            try:
                ns_ns_records = dns.resolver.resolve(ns, 'NS')
                ns_ns_list = [r.to_text() for r in ns_ns_records]
            except Exception:
                ns_ns_list = []
            for target_ns in display_ns_list:
                if target_ns in ns_ns_list:
                    dot.edge(ns_nodes[ns], ns_nodes[target_ns], color='blue', style='dashed')

    # Draw box around referenced NS
    if referenced_ns:
        with dot.subgraph(name=f"cluster_{index}") as c:
            c.attr(style='dashed', color='blue')
            for ns in display_ns_list:
                if ns in referenced_ns:
                    c.node(ns_nodes[ns])

    # Save to static/generated/graph_layer_{index}.png
    static_dir = os.path.join(app.root_path, "static", "generated")
    os.makedirs(static_dir, exist_ok=True)
    graph_path = os.path.join(static_dir, f"{prefix}_graph_layer_{index}")
    dot.render(graph_path, cleanup=True)
    return url_for('static', filename=f"generated/{prefix}_graph_layer_{index}.png")

def build_all_layer_graphs(trace, domain, verbose=False, prefix=None):
    """
    Build graphs for all layers and return list of URLs.
    """
    urls = []
    for i, node in enumerate(trace):
        zone = node['zone']
        ns_list = node['nameservers']
        verbose_info = node.get('verbose', None)
        parent_ns_list = trace[i-1]['nameservers'] if i > 0 else None
        url = build_layer_graph(zone, ns_list, parent_ns_list, verbose_info, verbose, i, prefix)
        urls.append(url)
    return urls

def test_last_level_ns_references(ns_list, domain):
    """
    Test what each nameserver thinks the NS records should be for the domain.
    This shows if nameservers are consistent in their responses.
    Also fetch A and AAAA records for each nameserver.
    Returns a dict with ns as key and dict of references and IPs as value.
    """
    results = {}
    for ns in ns_list:
        ns_result = {}
        # Query this specific nameserver for NS records of the domain
        try:
            # Create a resolver that uses only this nameserver
            specific_resolver = dns.resolver.Resolver()
            specific_resolver.nameservers = [dns.resolver.resolve(ns, 'A')[0].to_text()]
            specific_resolver.timeout = Config.DNS_TIMEOUT
            specific_resolver.lifetime = Config.DNS_LIFETIME
            
            # Ask this nameserver what it thinks the NS records are for the domain
            ns_ns_records = specific_resolver.resolve(domain, 'NS')
            ns_ns_list = [r.to_text() for r in ns_ns_records]
            # Filter to only those in ns_list for comparison
            referenced = [ref for ref in ns_ns_list if ref in ns_list]
            ns_result['references'] = referenced
        except dns.resolver.NoAnswer:
            ns_result['references'] = []
        except Exception as e:
            ns_result['references'] = [f"Error: {e}"]
        
        # Get A and AAAA records for the nameserver itself
        try:
            a_records = dns.resolver.resolve(ns, 'A')
            ns_result['A'] = [a.to_text() for a in a_records]
        except Exception:
            ns_result['A'] = []
        try:
            aaaa_records = dns.resolver.resolve(ns, 'AAAA')
            ns_result['AAAA'] = [a.to_text() for a in aaaa_records]
        except Exception:
            ns_result['AAAA'] = []
        results[ns] = ns_result
    return results

def build_cross_ref_graph(cross_ref_results, domain=None, prefix=None):
    """
    Build a detailed graphviz graph visualizing the cross references among last-level nameservers.
    Shows arrows between nameservers that reference each other.
    Marks servers that do not reference themselves with red border.
    Includes a node for the domain pointing to its nameservers.
    """
    dot = Digraph(format='png')
    dot.attr(rankdir='LR')
    # Show the domain being looked up prominently in the title
    title = f'Cross-Reference Analysis for: {domain}' if domain else 'Last Level Nameserver Cross-Reference'
    dot.attr(label=title, labelloc='t', fontsize='20')

    # Collect all servers from keys and all references
    all_servers = set(cross_ref_results.keys())
    for info in cross_ref_results.values():
        if isinstance(info, dict):
            all_servers.update(info.get('references', []))

    # Add domain node if provided
    if domain:
        dot.node(domain, domain, shape='box', style='filled', fillcolor='#ccccff')

    # Add nodes with default green fill
    for server in all_servers:
        dot.node(server, server, shape='ellipse', style='filled', fillcolor='#eaffea')

    # Add edges from domain to its nameservers (the keys of cross_ref_results)
    if domain:
        for ns in cross_ref_results.keys():
            dot.edge(domain, ns, color='black', style='bold')

    # Add edges for cross-references between nameservers
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            for ref in refs:
                if ref in all_servers and ref != ns:  # Don't draw self-loops for clarity
                    dot.edge(ns, ref, color='blue', style='dashed', label='references')

    # Mark servers that do not reference themselves with red border
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            if ns not in refs:
                dot.node(ns, ns, shape='ellipse', style='filled,bold', fillcolor='#eaffea', color='red', penwidth='3')

    # Self-reference arrows (draw these separately for clarity)
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            if ns in refs:
                # Create a self-loop
                dot.edge(ns, ns, color='green', style='solid', label='self-ref')

    # Save to static/generated with unique prefix to avoid collisions
    static_dir = os.path.join(app.root_path, "static", "generated")
    os.makedirs(static_dir, exist_ok=True)
    graph_path = os.path.join(static_dir, f"{prefix}_cross_ref_graph")
    dot.render(graph_path, cleanup=True)
    return url_for('static', filename=f'generated/{prefix}_cross_ref_graph.png')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files explicitly to ensure they work in all environments."""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/delegation', methods=['POST'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_delegation():
    app.logger.info(f"Received delegation request for domain: {request.json.get('domain')}")
    data = request.get_json()
    domain = data.get('domain', '')
    verbose = data.get('verbose', False)
    dns_server = data.get('dns_server', 'system')
    prefix = hashlib.sha256(f"{domain}_{verbose}_{dns_server}".encode()).hexdigest()
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    try:
        # Create custom resolver if specified
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, _ = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver)
        graph_urls = build_all_layer_graphs(trace, domain, verbose, prefix)
        chain_str = " → ".join(chain)

        cross_ref_results = {}
        cross_ref_graph_url = None
        if trace:
            last_level_ns = [ns for ns in trace[-1]['nameservers'] if not ns.startswith("Error:")]
            if last_level_ns:
                cross_ref_results = test_last_level_ns_references(last_level_ns, domain)
                cross_ref_graph_url = build_cross_ref_graph(cross_ref_results, domain, prefix)
        return jsonify({
            'trace': trace,
            'graph_urls': graph_urls,
            'chain': chain_str,
            'cross_ref_results': cross_ref_results,
            'cross_ref_graph_url': cross_ref_graph_url,
            'dns_server_used': dns_server
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trace/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_trace_domain(domain):
    """API endpoint for DNS delegation trace without visualizations."""
    verbose = request.args.get('verbose', 'false').lower() == 'true'
    dns_server = request.args.get('dns_server', 'system')
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, _ = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver)
        chain_str = " → ".join(chain)
        
        return jsonify({
            'domain': domain,
            'trace': trace,
            'chain': chain_str,
            'dns_server_used': dns_server,
            'verbose': verbose
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nameservers/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_nameservers(domain):
    """API endpoint to get nameservers for a domain."""
    dns_server = request.args.get('dns_server', 'system')
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        query_resolver = custom_resolver if custom_resolver else resolver
        
        ns_records = query_resolver.resolve(domain, 'NS')
        ns_list = [r.to_text() for r in ns_records]
        
        return jsonify({
            'domain': domain,
            'nameservers': ns_list,
            'dns_server_used': dns_server
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'DNS By Eye',
        'version': '1.0.0'
    })

@app.route('/api/dns-servers', methods=['GET'])
def api_dns_servers():
    """Get list of available public DNS servers."""
    dns_servers = {
        'system': 'System Default',
        '8.8.8.8': 'Google DNS',
        '8.8.4.4': 'Google DNS (Secondary)',
        '1.1.1.1': 'Cloudflare DNS',
        '1.0.0.1': 'Cloudflare DNS (Secondary)',
        '9.9.9.9': 'Quad9 DNS',
        '208.67.222.222': 'OpenDNS',
        '208.67.220.220': 'OpenDNS (Secondary)'
    }
    return jsonify(dns_servers)

@app.route('/api/export/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_export(domain):
    """Export DNS delegation analysis data in JSON or CSV format."""
    format_type = request.args.get('format', 'json').lower()
    verbose = request.args.get('verbose', 'false').lower() == 'true'
    dns_server = request.args.get('dns_server', 'system')
    debug = request.args.get('debug', 'false').lower() == 'true'
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    if format_type not in ['json', 'csv']:
        return jsonify({'error': 'Format must be json or csv'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=debug)
        chain_str = " → ".join(chain)
        
        # Prepare export data
        export_data = {
            'domain': domain,
            'chain': chain_str,
            'dns_server_used': dns_server,
            'export_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'trace': trace
        }
        
        if debug:
            export_data['timing_info'] = timing
            
        if format_type == 'json':
            response = make_response(json.dumps(export_data, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=dns_trace_{domain}_{int(time.time())}.json'
            return response
            
        elif format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            headers = ['Zone', 'Nameservers', 'Response_Time_ms', 'Is_Slow']
            if verbose:
                headers.append('Verbose_Info')
            writer.writerow(headers)
            
            # Write data
            for step in trace:
                row = [
                    step['zone'],
                    '; '.join(step['nameservers']),
                    step.get('response_time', ''),
                    step.get('is_slow', False)
                ]
                if verbose and step.get('verbose'):
                    row.append(step['verbose'])
                elif verbose:
                    row.append('')
                writer.writerow(row)
            
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=dns_trace_{domain}_{int(time.time())}.csv'
            return response
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare', methods=['POST'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_compare():
    """Compare DNS delegation for multiple domains."""
    data = request.get_json()
    domains = data.get('domains', [])
    verbose = data.get('verbose', False)
    dns_server = data.get('dns_server', 'system')
    debug = data.get('debug', False)
    
    if not domains or not isinstance(domains, list):
        return jsonify({'error': 'domains must be a non-empty list'}), 400
    
    if len(domains) > 5:  # Limit to prevent abuse
        return jsonify({'error': 'Maximum 5 domains allowed for comparison'}), 400
    
    # Validate all domains
    for domain in domains:
        if not is_valid_domain(domain):
            return jsonify({'error': f'Invalid domain format: {domain}'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        comparison_results = {}
        
        for domain in domains:
            trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=debug)
            chain_str = " → ".join(chain)
            
            comparison_results[domain] = {
                'trace': trace,
                'chain': chain_str,
                'total_response_time': sum([step.get('response_time', 0) for step in trace]),
                'slow_responses': len([step for step in trace if step.get('is_slow', False)]),
                'nameserver_count': len([ns for step in trace for ns in step['nameservers'] if not ns.startswith('Error:')])
            }
            
            if debug:
                comparison_results[domain]['timing_info'] = timing
        
        return jsonify({
            'comparison_results': comparison_results,
            'dns_server_used': dns_server,
            'comparison_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_debug(domain):
    """Get detailed debug information for DNS delegation trace."""
    verbose = request.args.get('verbose', 'false').lower() == 'true'
    dns_server = request.args.get('dns_server', 'system')
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    try:
        start_total = time.time()
        custom_resolver = create_custom_resolver(dns_server)
        trace, chain, timing = trace_delegation(domain, verbose=verbose, custom_resolver=custom_resolver, debug=True)
        end_total = time.time()
        
        chain_str = " → ".join(chain)
        total_time = round((end_total - start_total) * 1000, 2)
        
        # Calculate statistics
        response_times = [step.get('response_time', 0) for step in trace]
        slow_count = len([step for step in trace if step.get('is_slow', False)])
        
        debug_info = {
            'domain': domain,
            'trace': trace,
            'chain': chain_str,
            'dns_server_used': dns_server,
            'timing_analysis': {
                'total_query_time': total_time,
                'average_response_time': round(sum(response_times) / len(response_times), 2) if response_times else 0,
                'slowest_response': max(response_times) if response_times else 0,
                'fastest_response': min(response_times) if response_times else 0,
                'slow_responses_count': slow_count,
                'total_queries': len(trace)
            },
            'detailed_timing': timing,
            'resolver_config': {
                'timeout': Config.DNS_TIMEOUT,
                'lifetime': Config.DNS_LIFETIME,
                'custom_server': dns_server if dns_server != 'system' else None
            },
            'debug_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
