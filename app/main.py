from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, make_response
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

# DNS timeout constant for direct queries
DNS_TIMEOUT = Config.DNS_TIMEOUT

DOMAIN_REGEX = re.compile(r'^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$')
def is_valid_domain(domain):
    return bool(DOMAIN_REGEX.match(domain.strip('.')))

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
    Handles error nameservers gracefully.
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

    # Filter out error entries and valid nameservers
    error_entries = [ns for ns in ns_list if ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]
    valid_ns_list = [ns for ns in ns_list if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]

    # For root servers, limit to 4 and show a "..." node
    is_root = zone == '.'
    display_ns_list = valid_ns_list
    has_more = False
    
    if is_root and len(valid_ns_list) > 4:
        display_ns_list = valid_ns_list[:4]
        has_more = True

    ns_nodes = {}
    
    # Handle valid nameservers
    for ns in display_ns_list:
        # Sanitize node names to avoid graphviz issues
        safe_ns = ns.replace('.', '_').replace('-', '_').replace(':', '_')
        ns_node = f"ns_{index}_{safe_ns}"
        ns_nodes[ns] = ns_node

    # Add "more servers" node if needed
    if has_more:
        more_node = f"more_{index}"
        ns_nodes[f"... and {len(valid_ns_list) - 4} more"] = more_node

    # Handle error entries
    if error_entries:
        error_node = f"error_{index}"
        error_text = "\\n".join(error_entries)
        ns_nodes["ERROR"] = error_node

    # Determine which NS are referenced by parent layer (only valid ones)
    referenced_ns = set()
    if parent_ns_list:
        valid_parent_ns = [ns for ns in parent_ns_list if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]
        referenced_ns = set(valid_parent_ns)

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
        dot.node(more_node, f"... and {len(valid_ns_list) - 4} more", shape='ellipse', style='filled,dashed', fillcolor='#f0f0f0', color='#888888')

    # Add error node if there are errors
    if error_entries:
        dot.node(error_node, error_text, shape='box', style='filled', fillcolor='#ffcccc', color='red')

    # Edges from zone to NS
    for ns in display_ns_list:
        ns_node = ns_nodes[ns]
        dot.edge(zone_node, ns_node)
    
    # Edge to "more servers" node
    if has_more:
        dot.edge(zone_node, more_node, style='dashed', color='#888888')

    # Edge to error node
    if error_entries:
        dot.edge(zone_node, error_node, color='red', style='dashed')

    # If this is the final layer (no children), add arrows between NS if they refer to themselves or each other
    # Only do this for valid nameservers
    if parent_ns_list is not None and len(display_ns_list) > 1:
        # Check NS refer to each other or themselves by resolving NS records of each NS
        for ns in display_ns_list:
            if ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:')):
                continue
            try:
                ns_ns_records = dns.resolver.resolve(ns, 'NS')
                ns_ns_list = [r.to_text() for r in ns_ns_records]
            except Exception:
                ns_ns_list = []
            for target_ns in display_ns_list:
                if target_ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:')):
                    continue
                if target_ns in ns_ns_list:
                    dot.edge(ns_nodes[ns], ns_nodes[target_ns], color='blue', style='dashed')

    # Draw box around referenced NS (only valid ones)
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
        
        # Skip glue record checking for root (.) and TLD zones (first two levels)
        if i <= 1:  # 0 = root, 1 = TLD
            zone_result['status'] = 'skipped'
            zone_result['glue_issues'].append(f"Glue record checking skipped for {zone} (root/TLD level)")
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
                    ns_glue['issues'].append(f"Error checking glue records from parent zone: {e}")
                
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
                    zone_result['glue_issues'].extend([f"{ns}: {issue}" for issue in ns_glue['issues']])
            
        except dns.resolver.NXDOMAIN:
            zone_result['status'] = 'nxdomain'
            zone_result['glue_issues'].append(f"Zone {zone} does not exist")
        except dns.resolver.NoAnswer:
            zone_result['status'] = 'no_ns'
            zone_result['glue_issues'].append(f"No NS records found for {zone}")
        except Exception as e:
            zone_result['status'] = 'error'
            zone_result['glue_issues'].append(f"Error querying {zone}: {e}")
        
        glue_results[zone] = zone_result
    
    return glue_results

def test_last_level_ns_references(ns_list, domain):
    """
    Test what each nameserver thinks the NS records should be for the domain.
    This shows if nameservers are consistent in their responses.
    Also fetch A and AAAA records for each nameserver.
    Returns a dict with ns as key and dict of references and IPs as value.
    
    This function is resilient to broken nameservers and will continue processing
    even if some nameservers are unreachable or misconfigured.
    """
    results = {}
    for ns in ns_list:
        ns_result = {
            'references': [],
            'A': [],
            'AAAA': [],
            'status': 'unknown'
        }
        
        # First, try to get A and AAAA records for the nameserver itself
        ns_ip = None
        try:
            a_records = dns.resolver.resolve(ns, 'A')
            ns_result['A'] = [a.to_text() for a in a_records]
            ns_ip = ns_result['A'][0]  # Use first A record for querying
            ns_result['status'] = 'reachable'
        except dns.resolver.NXDOMAIN:
            ns_result['status'] = 'nxdomain'
            ns_result['A'] = ['NXDOMAIN: Nameserver does not exist']
        except dns.resolver.NoAnswer:
            ns_result['status'] = 'no_a_record'
            ns_result['A'] = ['No A record found']
        except dns.resolver.Timeout:
            ns_result['status'] = 'timeout'
            ns_result['A'] = ['Timeout resolving A record']
        except Exception as e:
            ns_result['status'] = 'error'
            ns_result['A'] = [f'Error resolving A record: {e}']
        
        # Try to get AAAA records
        try:
            aaaa_records = dns.resolver.resolve(ns, 'AAAA')
            ns_result['AAAA'] = [a.to_text() for a in aaaa_records]
        except Exception:
            # AAAA records are optional, so we don't change status for this
            pass
        
        # Only try to query the nameserver if we have an IP address
        if ns_ip and ns_result['status'] == 'reachable':
            try:
                # Create a resolver that uses only this nameserver
                specific_resolver = dns.resolver.Resolver()
                specific_resolver.nameservers = [ns_ip]
                specific_resolver.timeout = Config.DNS_TIMEOUT
                specific_resolver.lifetime = Config.DNS_LIFETIME
                
                # Ask this nameserver what it thinks the NS records are for the domain
                ns_ns_records = specific_resolver.resolve(domain, 'NS')
                ns_ns_list = [r.to_text() for r in ns_ns_records]
                # Filter to only those in ns_list for comparison
                referenced = [ref for ref in ns_ns_list if ref in ns_list]
                ns_result['references'] = referenced
                ns_result['query_status'] = 'success'
                
            except dns.resolver.NXDOMAIN:
                ns_result['references'] = []
                ns_result['query_status'] = 'nxdomain'
            except dns.resolver.NoAnswer:
                ns_result['references'] = []
                ns_result['query_status'] = 'no_answer'
            except dns.resolver.Timeout:
                ns_result['references'] = ['Timeout querying nameserver']
                ns_result['query_status'] = 'timeout'
            except dns.resolver.NoNameservers:
                ns_result['references'] = ['No nameservers available']
                ns_result['query_status'] = 'no_nameservers'
            except Exception as e:
                ns_result['references'] = [f"Error querying nameserver: {e}"]
                ns_result['query_status'] = 'error'
        else:
            # Can't query this nameserver
            ns_result['references'] = [f"Cannot query: {ns_result['status']}"]
            ns_result['query_status'] = 'unreachable'
        
        results[ns] = ns_result
    return results

def build_cross_ref_graph(cross_ref_results, domain=None, prefix=None, glue_data=None):
    """
    Build a detailed graphviz graph visualizing the cross references among last-level nameservers.
    Shows arrows between nameservers that reference each other.
    Marks servers that do not reference themselves with red border.
    Includes a node for the domain pointing to its nameservers.
    Handles broken/unreachable nameservers gracefully.
    Enhanced with glue record information when available.
    Layout similar to domain delegation graphs with domain at top, nameservers below.
    """
    dot = Digraph(format='png')
    dot.attr(rankdir='TB')  # Top to bottom like domain graphs
    # Show the domain being looked up prominently in the title
    title = f'Cross-Reference Analysis for: {domain}' if domain else 'Last Level Nameserver Cross-Reference'
    dot.attr(label=title, labelloc='t', fontsize='20')

    # Collect all servers from keys and valid references (filter out error messages)
    all_servers = set(cross_ref_results.keys())
    for info in cross_ref_results.values():
        if isinstance(info, dict):
            refs = info.get('references', [])
            # Only add references that don't start with error messages
            valid_refs = [ref for ref in refs if not ref.startswith(('Error:', 'Timeout', 'Cannot query:', 'NXDOMAIN:', 'No nameservers'))]
            all_servers.update(valid_refs)

    # Add domain node if provided
    if domain:
        dot.node(domain, domain, shape='box', style='filled', fillcolor='#ccccff')

    # Add nodes with colors based on their status and glue record information
    for server in all_servers:
        if server in cross_ref_results:
            # This is a nameserver we tested
            info = cross_ref_results[server]
            status = info.get('status', 'unknown')
            
            # Base colors based on reachability status
            if status == 'reachable':
                fillcolor = '#eaffea'  # green - working
                color = 'black'
            elif status == 'nxdomain':
                fillcolor = '#ffcccc'  # red - doesn't exist
                color = 'red'
            elif status in ['timeout', 'error']:
                fillcolor = '#ffffcc'  # yellow - problematic
                color = 'orange'
            else:
                fillcolor = '#f0f0f0'  # gray - unknown
                color = 'gray'
            
            # Enhance with glue record information if available
            node_label = server
            glue_info = []
            if glue_data and server in glue_data:
                glue_record = glue_data[server]
                
                # Add glue record indicators to the label
                if glue_record.get('expected_glue', False):
                    if glue_record.get('has_glue_a', False):
                        glue_info.append('A✓')
                    else:
                        glue_info.append('A✗')
                        # Change color to indicate missing glue
                        if status == 'reachable':
                            fillcolor = '#ffeeaa'  # yellow-ish for missing glue
                            color = 'darkorange'
                    
                    if glue_record.get('has_glue_aaaa', False):
                        glue_info.append('AAAA✓')
                    elif glue_record.get('resolved_aaaa_records'):
                        glue_info.append('AAAA✗')
                        # Change color to indicate missing glue
                        if status == 'reachable':
                            fillcolor = '#ffeeaa'  # yellow-ish for missing glue
                            color = 'darkorange'
                
                # Check for glue record issues
                if glue_record.get('issues'):
                    # Add warning indicator for any glue issues
                    glue_info.append('⚠️')
                    if status == 'reachable':
                        fillcolor = '#ffd4aa'  # orange-ish for glue issues
                        color = 'red'
                
                # Add glue info to label if any
                if glue_info:
                    node_label = f"{server}\\n[{' '.join(glue_info)}]"
                
            dot.node(server, node_label, shape='ellipse', style='filled', fillcolor=fillcolor, color=color)
        else:
            # This is a referenced server we didn't test directly
            dot.node(server, server, shape='ellipse', style='filled', fillcolor='#eaffea')

    # Add edges from domain to its nameservers (the keys of cross_ref_results)
    if domain:
        for ns in cross_ref_results.keys():
            dot.edge(domain, ns, color='black', style='bold')

    # Add edges for cross-references between nameservers
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            # Only draw edges for valid references
            valid_refs = [ref for ref in refs if not ref.startswith(('Error:', 'Timeout', 'Cannot query:', 'NXDOMAIN:', 'No nameservers'))]
            
            for ref in valid_refs:
                if ref in all_servers and ref != ns:  # Don't draw self-loops for clarity
                    # Color the edge based on query status
                    query_status = info.get('query_status', 'unknown')
                    if query_status == 'success':
                        edge_color = 'blue'
                    elif query_status in ['timeout', 'error']:
                        edge_color = 'orange'
                    else:
                        edge_color = 'gray'
                    
                    dot.edge(ns, ref, color=edge_color, style='dashed', label='references')

    # Mark servers that do not reference themselves with red border
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            valid_refs = [ref for ref in refs if not ref.startswith(('Error:', 'Timeout', 'Cannot query:', 'NXDOMAIN:', 'No nameservers'))]
            
            if ns not in valid_refs and info.get('status') == 'reachable':
                # Only mark as problematic if the server is reachable but doesn't self-reference
                dot.node(ns, ns, shape='ellipse', style='filled,bold', fillcolor='#eaffea', color='red', penwidth='3')

    # Self-reference arrows (draw these separately for clarity)
    for ns, info in cross_ref_results.items():
        if isinstance(info, dict):
            refs = info.get('references', [])
            valid_refs = [ref for ref in refs if not ref.startswith(('Error:', 'Timeout', 'Cannot query:', 'NXDOMAIN:', 'No nameservers'))]
            
            if ns in valid_refs:
                # Create a self-loop
                query_status = info.get('query_status', 'unknown')
                if query_status == 'success':
                    edge_color = 'green'
                elif query_status in ['timeout', 'error']:
                    edge_color = 'orange'
                else:
                    edge_color = 'gray'
                    
                dot.edge(ns, ns, color=edge_color, style='solid', label='self-ref')

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
    check_glue = data.get('check_glue', True)  # Enable glue record checking by default
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
        glue_results = {}
        
        if trace:
            # Filter out error nameservers more comprehensively
            last_level_ns = [ns for ns in trace[-1]['nameservers'] 
                           if not ns.startswith(('Error:', 'NXDOMAIN:', 'No NS records:', 'Timeout:', 'No nameservers:'))]
            if last_level_ns:
                try:
                    cross_ref_results = test_last_level_ns_references(last_level_ns, domain)
                    # Always get glue records for cross-reference graph enhancement
                    domain_glue_results = {}
                    try:
                        full_glue_results = check_glue_records(domain, custom_resolver)
                        # Extract glue info for the final domain level
                        if domain in full_glue_results:
                            domain_glue_results = full_glue_results[domain].get('glue_records', {})
                    except Exception as e:
                        app.logger.warning(f"Glue record analysis for cross-ref failed for {domain}: {e}")
                    
                    cross_ref_graph_url = build_cross_ref_graph(cross_ref_results, domain, prefix, domain_glue_results)
                except Exception as e:
                    # If cross-reference analysis fails, continue without it
                    app.logger.warning(f"Cross-reference analysis failed for {domain}: {e}")
                    cross_ref_results = {}
                    cross_ref_graph_url = None
        
        # Check glue records if requested
        if check_glue:
            try:
                glue_results = check_glue_records(domain, custom_resolver)
            except Exception as e:
                app.logger.warning(f"Glue record analysis failed for {domain}: {e}")
                glue_results = {}
        
        return jsonify({
            'trace': trace,
            'graph_urls': graph_urls,
            'chain': chain_str,
            'cross_ref_results': cross_ref_results,
            'cross_ref_graph_url': cross_ref_graph_url,
            'glue_results': glue_results,
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
        'version': '1.0.1'
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

@app.route('/api/glue-records/<domain>', methods=['GET'])
@limiter.limit(Config.RATELIMIT_DEFAULT)
def api_glue_records(domain):
    """API endpoint to check glue records for a domain."""
    dns_server = request.args.get('dns_server', 'system')
    
    if not is_valid_domain(domain):
        return jsonify({'error': 'Invalid domain format'}), 400
    
    try:
        custom_resolver = create_custom_resolver(dns_server)
        glue_results = check_glue_records(domain, custom_resolver)
        
        # Calculate summary statistics
        total_zones = len(glue_results)
        zones_with_issues = len([zone for zone, data in glue_results.items() if data['glue_issues']])
        total_nameservers = sum([len(data['nameservers']) for data in glue_results.values()])
        nameservers_with_issues = sum([
            len([ns for ns, ns_data in data['glue_records'].items() if ns_data['issues']])
            for data in glue_results.values()
        ])
        
        return jsonify({
            'domain': domain,
            'dns_server_used': dns_server,
            'glue_analysis': glue_results,
            'summary': {
                'total_zones': total_zones,
                'zones_with_issues': zones_with_issues,
                'total_nameservers': total_nameservers,
                'nameservers_with_issues': nameservers_with_issues,
                'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
