#!/usr/bin/env python3
"""
Test script for the new glue record checking functionality.
This script tests the glue record analysis without Flask dependencies.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import check_glue_records, create_custom_resolver, is_valid_domain
import time

def test_glue_records(domain, description, dns_server='system'):
    """Test glue record checking for a domain and print the results."""
    print(f"\n{'='*80}")
    print(f"Testing Glue Records: {domain}")
    print(f"Description: {description}")
    print(f"DNS Server: {dns_server}")
    print(f"{'='*80}")
    
    if not is_valid_domain(domain):
        print(f"ERROR: Invalid domain format: {domain}")
        return
    
    try:
        start_time = time.time()
        custom_resolver = create_custom_resolver(dns_server)
        glue_results = check_glue_records(domain, custom_resolver)
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
    print("DNS By Eye - Glue Record Analysis Test")
    print("This script tests the new glue record checking functionality.")
    
    # Test cases
    test_cases = [
        ("google.com", "Popular domain - should have proper glue records"),
        ("example.com", "IANA example domain - should work normally"),
        ("github.com", "GitHub domain - test for proper glue record handling"),
        ("cloudflare.com", "Cloudflare domain - known for good DNS practices"),
        ("nonexistent-domain-12345.com", "Non-existent domain - should handle gracefully"),
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
