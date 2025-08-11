#!/usr/bin/env python3
"""
Standalone test script for glue record checking functionality.
This script tests the core DNS logic without Flask dependencies.
"""

import dns.resolver
import dns.message
import dns.query
import dns.rdatatype
import time
import re

# DNS configuration
DNS_TIMEOUT = 2.0
DNS_LIFETIME = 4.0

# Configure DNS resolver with timeouts
resolver = dns.resolver.Resolver()
resolver.timeout = DNS_TIMEOUT
resolver.lifetime = DNS_LIFETIME

DOMAIN_REGEX = re.compile(r'^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$')

def is_valid_domain(domain):
    return bool(DOMAIN_REGEX.match(domain.strip('.')))

def check_glue_records_standalone(domain, custom_resolver=None):
    """
    Standalone version of glue record checking functionality.
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
    
    for zone in chain:
        zone_result = {
            'zone': zone,
            'nameservers': [],
            'glue_records': {},
            'glue_issues': [],
            'status': 'unknown'
        }
        
        try:
            # Get NS records for this zone
            ns_response = query_resolver.resolve(zone, 'NS')
            ns_list = [r.to_text().rstrip('.') for r in ns_response]
            zone_result['nameservers'] = ns_list
            zone_result['status'] = 'success'
            
            # For each nameserver, check glue records
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
                
                # Try to get the full DNS response with additional section
                try:
                    # Query one of the nameservers for this zone to get glue records
                    if zone_result['nameservers']:
                        # Try to find an IP for one of the nameservers to query
                        query_target = None
                        for test_ns in zone_result['nameservers']:
                            try:
                                test_ns_ips = query_resolver.resolve(test_ns, 'A')
                                if test_ns_ips:
                                    query_target = test_ns_ips[0].to_text()
                                    break
                            except:
                                continue
                        
                        if query_target:
                            # Create DNS message for NS query
                            query_msg = dns.message.make_query(zone, 'NS')
                            try:
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
                            except:
                                pass
                
                except Exception as e:
                    ns_glue['issues'].append(f"Error checking glue records: {e}")
                
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

def test_glue_records(domain, description):
    """Test glue record checking for a domain and print the results."""
    print(f"\n{'='*80}")
    print(f"Testing Glue Records: {domain}")
    print(f"Description: {description}")
    print(f"{'='*80}")
    
    if not is_valid_domain(domain):
        print(f"ERROR: Invalid domain format: {domain}")
        return
    
    try:
        start_time = time.time()
        glue_results = check_glue_records_standalone(domain)
        end_time = time.time()
        
        print(f"Analysis completed in {round((end_time - start_time) * 1000, 2)}ms")
        
        # Summary statistics
        total_zones = len(glue_results)
        zones_with_issues = len([zone for zone, data in glue_results.items() if data['glue_issues']])
        total_nameservers = sum([len(data['nameservers']) for data in glue_results.values()])
        nameservers_with_issues = sum([
            len([ns for ns, ns_data in data['glue_records'].items() if ns_data['issues']])
            for data in glue_results.values()
        ])
        
        print(f"\nSUMMARY:")
        print(f"  Total Zones: {total_zones}")
        print(f"  Zones with Issues: {zones_with_issues}")
        print(f"  Total Nameservers: {total_nameservers}")
        print(f"  Nameservers with Issues: {nameservers_with_issues}")
        
        # Detailed results for each zone
        for zone, zone_data in glue_results.items():
            print(f"\n--- Zone: {zone} ---")
            print(f"Status: {zone_data['status']}")
            print(f"Nameservers: {', '.join(zone_data['nameservers'])}")
            
            if zone_data['glue_issues']:
                print(f"Zone Issues:")
                for issue in zone_data['glue_issues']:
                    print(f"  - {issue}")
            
            if zone_data['glue_records']:
                print(f"Glue Record Details:")
                for ns, ns_data in zone_data['glue_records'].items():
                    print(f"  {ns}:")
                    print(f"    Expected Glue: {ns_data['expected_glue']}")
                    print(f"    Has Glue A: {ns_data['has_glue_a']}")
                    print(f"    Has Glue AAAA: {ns_data['has_glue_aaaa']}")
                    
                    if ns_data['glue_a_records']:
                        print(f"    Glue A Records: {', '.join(ns_data['glue_a_records'])}")
                    if ns_data['glue_aaaa_records']:
                        print(f"    Glue AAAA Records: {', '.join(ns_data['glue_aaaa_records'])}")
                    if ns_data['resolved_a_records']:
                        print(f"    Resolved A Records: {', '.join(ns_data['resolved_a_records'])}")
                    if ns_data['resolved_aaaa_records']:
                        print(f"    Resolved AAAA Records: {', '.join(ns_data['resolved_aaaa_records'])}")
                    
                    print(f"    Glue Matches Resolution: {ns_data['glue_matches_resolution']}")
                    
                    if ns_data['issues']:
                        print(f"    Issues:")
                        for issue in ns_data['issues']:
                            print(f"      - {issue}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run tests for various domain scenarios to verify glue record functionality."""
    print("DNS By Eye - Glue Record Analysis Test (Standalone)")
    print("This script tests the new glue record checking functionality.")
    print("Note: This requires dnspython to be installed: pip install dnspython")
    
    # Test cases - using simpler domains that are more likely to work
    test_cases = [
        ("google.com", "Popular domain - should have proper glue records"),
        ("example.com", "IANA example domain - should work normally"),
    ]
    
    for domain, description in test_cases:
        test_glue_records(domain, description)
    
    print(f"\n{'='*80}")
    print("Glue Record Analysis Test completed!")
    print("The new functionality checks for:")
    print("1. Missing glue records for in-zone nameservers")
    print("2. Unnecessary glue records for out-of-zone nameservers")
    print("3. Mismatched glue records vs. actual resolution")
    print("4. Proper glue record validation across the delegation chain")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
