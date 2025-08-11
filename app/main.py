[Previous content up to the security headers]

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
            zone_result['glue_issues'].append(f"Glue record checking skipped for {zone} (root level)")
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
                for rr in response.answer:
                    if rr.rdtype == dns.rdatatype.NS:
                        for rd in rr:
                            ref_ns = rd.to_text().rstrip('.')
                            if ref_ns in nameservers:
                                results[ns]['references'].add(ref_ns)
        except Exception as e:
            results[ns] = f"Error querying nameserver: {e}"
    
    # Convert sets to lists for JSON serialization
    for ns in results:
        if isinstance(results[ns], dict):
            results[ns]['references'] = list(results[ns]['references'])
    
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
        
        # Flag slow
